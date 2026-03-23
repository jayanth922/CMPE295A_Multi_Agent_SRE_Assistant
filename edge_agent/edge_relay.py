"""
Edge Relay — Lightweight bridge between SaaS Platform and customer MCP servers.

This is the ONLY service a customer needs to run alongside their MCP tool servers.
It does NOT run any AI/LLM inference — all reasoning happens on the SaaS platform.

Flow:
    1. Polls SaaS for pending tool_call jobs
    2. Executes the tool call against the appropriate local MCP server
    3. Returns the result to the SaaS platform

Usage:
    CLUSTER_TOKEN=cl_xxx SAAS_URL=https://... python -m customer.edge_relay
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("edge_relay")

# ── Configuration ────────────────────────────────────────────────────────────

SAAS_URL = os.getenv("SAAS_URL", "http://localhost:8080").rstrip("/")
CLUSTER_TOKEN = os.getenv("CLUSTER_TOKEN", "")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_SECONDS", "3"))

# MCP server URIs (local to the customer's Docker network)
MCP_SERVERS: Dict[str, str] = {}
for key, env_var in {
    "k8s": "MCP_K8S_URI",
    "logs": "MCP_LOGS_URI",
    "metrics": "MCP_METRICS_URI",
    "github": "MCP_GITHUB_URI",
    "runbooks": "MCP_RUNBOOKS_URI",
    "memory": "MCP_MEMORY_URI",
}.items():
    uri = os.getenv(env_var)
    if uri:
        MCP_SERVERS[key] = uri


# ── MCP Tool Registry ───────────────────────────────────────────────────────

_tools: Dict[str, Any] = {}  # tool_name -> LangChain tool object
_tools_loaded = False


async def load_mcp_tools() -> None:
    """Connect to local MCP servers and discover available tools."""
    global _tools, _tools_loaded

    if not MCP_SERVERS:
        logger.error("No MCP server URIs configured. Set MCP_K8S_URI, MCP_METRICS_URI, etc.")
        return

    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient

        server_config = {}
        for name, uri in MCP_SERVERS.items():
            server_config[name] = {"url": uri, "transport": "sse"}

        client = MultiServerMCPClient(server_config)
        async with client:
            tools = client.get_tools()
            for tool in tools:
                _tools[tool.name] = tool
                logger.info(f"  Registered tool: {tool.name}")

        _tools_loaded = True
        logger.info(f"Loaded {len(_tools)} tools from {len(MCP_SERVERS)} MCP servers")
    except Exception as e:
        logger.error(f"Failed to load MCP tools: {e}")


async def call_tool(tool_name: str, tool_args: Dict[str, Any]) -> str:
    """Execute a single MCP tool call and return the result as a string."""
    from langchain_mcp_adapters.client import MultiServerMCPClient

    # Reconnect each time to avoid stale SSE connections
    server_config = {
        name: {"url": uri, "transport": "sse"}
        for name, uri in MCP_SERVERS.items()
    }

    try:
        client = MultiServerMCPClient(server_config)
        async with client:
            tools = client.get_tools()
            tool_map = {t.name: t for t in tools}

            if tool_name not in tool_map:
                return json.dumps({
                    "error": f"Tool '{tool_name}' not found. Available: {list(tool_map.keys())}"
                })

            tool = tool_map[tool_name]
            result = await tool.ainvoke(tool_args)
            return str(result)
    except Exception as e:
        logger.error(f"Tool call failed ({tool_name}): {e}")
        return json.dumps({"error": str(e)})


# ── SaaS Communication ──────────────────────────────────────────────────────

class SaaSClient:
    """HTTP client for communicating with the SaaS platform."""

    def __init__(self, saas_url: str, token: str):
        self.saas_url = saas_url
        self.headers = {"Authorization": f"Bearer {token}"}

    async def get_pending_job(self) -> Optional[Dict[str, Any]]:
        """Poll for a pending tool_call job."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as http:
                resp = await http.get(
                    f"{self.saas_url}/api/v1/clusters/jobs/pending",
                    headers=self.headers,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data if data else None
                if resp.status_code == 401:
                    logger.error("Invalid CLUSTER_TOKEN — check your .env")
                return None
        except httpx.RequestError as e:
            logger.debug(f"Poll error: {e}")
            return None

    async def submit_result(
        self,
        job_id: str,
        status: str,
        result: Optional[str] = None,
        logs: Optional[str] = None,
    ) -> bool:
        """Send tool result back to SaaS."""
        try:
            payload: Dict[str, Any] = {"status": status}
            if result:
                payload["result"] = result
            if logs:
                payload["logs"] = logs

            async with httpx.AsyncClient(timeout=10.0) as http:
                resp = await http.post(
                    f"{self.saas_url}/api/v1/clusters/jobs/{job_id}/status",
                    headers={**self.headers, "Content-Type": "application/json"},
                    json=payload,
                )
                return resp.status_code == 200
        except httpx.RequestError as e:
            logger.error(f"Failed to submit result for job {job_id}: {e}")
            return False

    async def send_heartbeat(self) -> bool:
        """Send a heartbeat so the SaaS knows this edge agent is alive."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as http:
                resp = await http.post(
                    f"{self.saas_url}/api/v1/agent/heartbeat",
                    headers=self.headers,
                )
                return resp.status_code == 200
        except httpx.RequestError:
            return False


# ── Main Loop ────────────────────────────────────────────────────────────────

async def execute_job(job: Dict[str, Any], saas: SaaSClient) -> None:
    """Execute a single tool_call job from the SaaS platform."""
    job_id = job["id"]
    job_type = job.get("job_type", "tool_call")
    payload_raw = job.get("payload", "{}")

    try:
        payload = json.loads(payload_raw) if isinstance(payload_raw, str) else payload_raw
    except json.JSONDecodeError:
        payload = {"raw": payload_raw}

    tool_name = payload.get("tool_name", "")
    tool_args = payload.get("tool_args", {})

    logger.info(f"▶ Job {job_id}: {job_type} → {tool_name}({json.dumps(tool_args)[:200]})")

    # Mark as running
    await saas.submit_result(job_id, "running")

    try:
        result = await call_tool(tool_name, tool_args)

        await saas.submit_result(
            job_id,
            "completed",
            result=result,
            logs=f"[{datetime.now(timezone.utc).isoformat()}] tool={tool_name} status=ok",
        )
        logger.info(f"✓ Job {job_id} completed ({len(result)} chars)")

    except Exception as e:
        logger.exception(f"✗ Job {job_id} failed: {e}")
        await saas.submit_result(
            job_id,
            "failed",
            result=json.dumps({"error": str(e)}),
            logs=f"[{datetime.now(timezone.utc).isoformat()}] tool={tool_name} error={e}",
        )


async def main_loop() -> None:
    """Poll for jobs and execute them."""
    saas = SaaSClient(SAAS_URL, CLUSTER_TOKEN)
    consecutive_errors = 0
    heartbeat_counter = 0

    logger.info("=" * 60)
    logger.info("  SRE Edge Relay")
    logger.info(f"  SaaS URL:     {SAAS_URL}")
    logger.info(f"  Token:        {CLUSTER_TOKEN[:15]}...")
    logger.info(f"  MCP Servers:  {list(MCP_SERVERS.keys())}")
    logger.info(f"  Poll interval: {POLL_INTERVAL}s")
    logger.info("=" * 60)

    while True:
        try:
            # Heartbeat every ~30s
            heartbeat_counter += 1
            if heartbeat_counter >= 30 // POLL_INTERVAL:
                await saas.send_heartbeat()
                heartbeat_counter = 0

            job = await saas.get_pending_job()

            if job:
                consecutive_errors = 0
                await execute_job(job, saas)
            else:
                consecutive_errors = 0

            await asyncio.sleep(POLL_INTERVAL)

        except asyncio.CancelledError:
            break
        except Exception as e:
            consecutive_errors += 1
            logger.error(f"Loop error ({consecutive_errors}): {e}")
            wait = min(POLL_INTERVAL * (2 ** consecutive_errors), 60)
            await asyncio.sleep(wait)

    logger.info("Edge relay stopped.")


# ── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not CLUSTER_TOKEN:
        print("Error: CLUSTER_TOKEN environment variable is required.")
        print("  cp .env.example .env   # then fill in your token")
        sys.exit(1)

    if not MCP_SERVERS:
        print("Error: No MCP server URIs configured.")
        print("  Set at least MCP_K8S_URI and MCP_METRICS_URI in .env")
        sys.exit(1)

    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\nStopped.")
