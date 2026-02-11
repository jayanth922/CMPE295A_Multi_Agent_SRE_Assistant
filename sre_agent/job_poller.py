"""
Job Poller Module for Edge Agent.

This module enables the Edge Agent to act as a "client" of the SaaS Platform,
polling for pending jobs and executing them using LangGraph.

Usage:
    1. Set CLUSTER_TOKEN environment variable
    2. Set SAAS_URL environment variable (defaults to http://localhost:8080)
    3. Call start_job_poller() to begin polling in the background
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any

import httpx

logger = logging.getLogger(__name__)

# Configuration from environment
SAAS_URL = os.getenv("SAAS_URL", "http://localhost:8080")
CLUSTER_TOKEN = os.getenv("CLUSTER_TOKEN", "")
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "5"))

# Global state
_poller_task: Optional[asyncio.Task] = None
_is_running = False


class JobPollerClient:
    """HTTP client for communicating with SaaS Job Queue."""
    
    def __init__(self, saas_url: str, cluster_token: str):
        self.saas_url = saas_url.rstrip("/")
        self.cluster_token = cluster_token
        self.headers = {"Authorization": f"Bearer {cluster_token}"}
    
    async def get_pending_job(self) -> Optional[Dict[str, Any]]:
        """Poll for pending jobs from SaaS."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.saas_url}/api/v1/clusters/jobs/pending",
                    headers=self.headers
                )
                if response.status_code == 200:
                    data = response.json()
                    return data if data else None
                elif response.status_code == 401:
                    logger.error("❌ Invalid cluster token - check CLUSTER_TOKEN")
                    return None
                else:
                    logger.warning(f"Unexpected response: {response.status_code}")
                    return None
        except httpx.RequestError as e:
            logger.debug(f"Connection error polling jobs: {e}")
            return None
    
    async def update_job_status(
        self, 
        job_id: str, 
        status: str, 
        result: Optional[str] = None,
        logs: Optional[str] = None
    ) -> bool:
        """Update job status on SaaS."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                payload = {"status": status}
                if result:
                    payload["result"] = result
                if logs:
                    payload["logs"] = logs
                
                response = await client.post(
                    f"{self.saas_url}/api/v1/clusters/jobs/{job_id}/status",
                    headers={**self.headers, "Content-Type": "application/json"},
                    json=payload
                )
                return response.status_code == 200
        except httpx.RequestError as e:
            logger.error(f"Failed to update job status: {e}")
            return False
    
    async def append_job_logs(self, job_id: str, logs: str) -> bool:
        """Append logs to a running job (telemetry streaming)."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.saas_url}/api/v1/clusters/jobs/{job_id}/logs",
                    headers={**self.headers, "Content-Type": "application/json"},
                    json=logs
                )
                return response.status_code == 200
        except httpx.RequestError as e:
            logger.debug(f"Failed to append logs: {e}")
            return False


async def execute_job(job: Dict[str, Any], client: JobPollerClient) -> None:
    """
    Execute a job using LangGraph and stream telemetry back to SaaS.
    
    This function:
    1. Updates job status to RUNNING
    2. Runs the LangGraph agent
    3. Streams logs during execution
    4. Updates job status to COMPLETED/FAILED with result
    """
    job_id = job["id"]
    job_type = job.get("job_type", "investigation")
    payload = job.get("payload", "{}")
    
    logger.info(f"▶️ Executing job {job_id} (type: {job_type})")
    
    # 1. Update status to RUNNING
    await client.update_job_status(job_id, "running")
    
    accumulated_logs = []
    
    def log_callback(message: str):
        """Callback to capture and stream logs."""
        timestamp = datetime.utcnow().isoformat()
        log_line = f"[{timestamp}] {message}"
        accumulated_logs.append(log_line)
        logger.info(f"  📋 {message}")
    
    try:
        # 2. Parse payload and prepare initial state
        try:
            payload_data = json.loads(payload) if payload else {}
        except json.JSONDecodeError:
            payload_data = {"raw": payload}
        
        alert_name = payload_data.get("alert", payload_data.get("title", "Unknown Alert"))
        alert_name = payload_data.get("alert", payload_data.get("title", "Unknown Alert"))
        
        # --- Zero-Touch Configuration Handler ---
        if job_type == "configure_cluster":
            log_callback("⚙️ Receiving cluster configuration update...")
            kubeconfig = payload_data.get("kubeconfig")
            
            if not kubeconfig:
                raise ValueError("No kubeconfig provided in payload")
            
            log_callback("Connecting to Kubernetes MCP Server...")
            
            # Create MCP client dynamically
            from .multi_agent_langgraph import create_mcp_client
            # We need to use asyncio.wait_for to prevent hanging
            mcp_client = create_mcp_client()
            
            try:
                log_callback("Invoking configure_cluster tool...")
                # Connect to K8s server (assuming it's the first or named 'k8s')
                # Since multi-server client abstracts this, we list tools to find it
                all_tools = await mcp_client.get_tools()
                config_tool = next((t for t in all_tools if t.name == "configure_cluster"), None)
                
                if not config_tool:
                    raise RuntimeError("configure_cluster tool not found on MCP server")
                
                # Invoke tool
                result_msg = await config_tool.ainvoke({"kubeconfig_content": kubeconfig})
                log_callback(f"Result: {result_msg}")
                
                 # Update to COMPLETED
                await client.update_job_status(
                    job_id, 
                    "completed", 
                    result=json.dumps({"status": "success", "message": result_msg}),
                    logs="\n".join(accumulated_logs)
                )
                return

            except Exception as e:
                log_callback(f"Configuration failed: {e}")
                raise e
            finally:
                # Cleanup if needed (MultiServerMCPClient manages its own sessions mostly)
                pass

        # --- End Zero-Touch Handler ---

        log_callback(f"Starting {job_type} for alert: {alert_name}")
        
        # 3. Import and run agent (delayed import to avoid circular deps)
        from .agent_runtime import agent_graph, initialize_agent, state_store, tools
        from .agent_state import AgentState
        from langchain_core.messages import HumanMessage
        
        # Ensure agent is initialized
        if agent_graph is None:
            log_callback("Initializing agent system...")
            await initialize_agent()
            from .agent_runtime import agent_graph as initialized_graph
            graph = initialized_graph
        else:
            graph = agent_graph
        
        if graph is None:
            raise RuntimeError("Agent graph not initialized")
        
        # 4. Create initial state
        session_id = job_id
        initial_state: AgentState = {
            "messages": [HumanMessage(content=f"Investigate alert: {alert_name}")],
            "next_agent": "analysis",
            "analysis_result": None,
            "remediation_plan": None,
            "execution_result": None,
            "requires_approval": False,
            "approval_status": "pending",
            "final_report": None,
            "metadata": {
                "session_id": session_id,
                "job_id": job_id,
                "alert_name": alert_name,
                "started_at": datetime.utcnow().isoformat(),
                "tools": tools,
            }
        }
        
        log_callback("Running LangGraph agent...")
        
        # 5. Execute the graph (streaming)
        final_state = None
        async for event in graph.astream(initial_state, config={"configurable": {"thread_id": session_id}}):
            # Log each step
            for node_name, node_output in event.items():
                if node_name != "__end__":
                    log_callback(f"Agent step: {node_name}")
                    
                    # Stream logs periodically
                    if len(accumulated_logs) >= 5:
                        await client.update_job_status(
                            job_id, "running", 
                            logs="\n".join(accumulated_logs[-5:])
                        )
            
            final_state = event
        
        # 6. Extract result
        result = {
            "status": "success",
            "completed_at": datetime.utcnow().isoformat(),
        }
        
        # Check for analysis result or final report
        if final_state:
            for node_output in final_state.values():
                if isinstance(node_output, dict):
                    if "final_report" in node_output and node_output["final_report"]:
                        result["report"] = node_output["final_report"][:1000]  # Truncate
                    if "analysis_result" in node_output and node_output["analysis_result"]:
                        result["analysis"] = str(node_output["analysis_result"])[:500]
                    if "remediation_plan" in node_output and node_output["remediation_plan"]:
                        result["remediation"] = str(node_output["remediation_plan"])[:500]
        
        log_callback("Job completed successfully!")
        
        # 7. Update to COMPLETED
        await client.update_job_status(
            job_id, 
            "completed", 
            result=json.dumps(result),
            logs="\n".join(accumulated_logs)
        )
        
    except Exception as e:
        error_msg = str(e)
        log_callback(f"ERROR: {error_msg}")
        logger.exception(f"Job execution failed: {e}")
        
        # Update to FAILED
        await client.update_job_status(
            job_id,
            "failed",
            result=json.dumps({"error": error_msg}),
            logs="\n".join(accumulated_logs)
        )


async def polling_loop(client: JobPollerClient) -> None:
    """Main polling loop that checks for pending jobs."""
    global _is_running
    
    logger.info(f"🔄 Starting job poller (interval: {POLL_INTERVAL_SECONDS}s)")
    logger.info(f"   SaaS URL: {client.saas_url}")
    logger.info(f"   Token: {client.cluster_token[:10]}...")
    
    _is_running = True
    consecutive_errors = 0
    
    while _is_running:
        try:
            # Poll for pending job
            job = await client.get_pending_job()
            
            if job:
                logger.info(f"📥 Received job: {job['id']}")
                consecutive_errors = 0
                
                # Execute the job
                await execute_job(job, client)
                
            else:
                # No pending job - that's normal
                consecutive_errors = 0
            
            # Wait before next poll
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
            
        except asyncio.CancelledError:
            logger.info("Job poller cancelled")
            break
        except Exception as e:
            consecutive_errors += 1
            logger.error(f"Polling error ({consecutive_errors}): {e}")
            
            # Exponential backoff on repeated errors
            wait_time = min(POLL_INTERVAL_SECONDS * (2 ** consecutive_errors), 60)
            await asyncio.sleep(wait_time)
    
    _is_running = False
    logger.info("🛑 Job poller stopped")


def start_job_poller() -> Optional[asyncio.Task]:
    """
    Start the job poller as a background task.
    
    Returns the Task object for management, or None if already running or no token.
    """
    global _poller_task, CLUSTER_TOKEN
    
    # Re-read token in case it was set after module load
    CLUSTER_TOKEN = os.getenv("CLUSTER_TOKEN", "")
    
    if not CLUSTER_TOKEN:
        logger.warning("⚠️ CLUSTER_TOKEN not set - job poller disabled")
        return None
    
    if _poller_task and not _poller_task.done():
        logger.warning("Job poller already running")
        return _poller_task
    
    client = JobPollerClient(SAAS_URL, CLUSTER_TOKEN)
    _poller_task = asyncio.create_task(polling_loop(client))
    
    return _poller_task


def stop_job_poller() -> None:
    """Stop the job poller."""
    global _is_running, _poller_task
    
    _is_running = False
    if _poller_task and not _poller_task.done():
        _poller_task.cancel()


# Convenience function for CLI usage
async def run_poller_forever():
    """Run the poller until interrupted (for standalone usage)."""
    task = start_job_poller()
    if task:
        try:
            await task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    # Allow running as standalone script
    import sys
    
    if not CLUSTER_TOKEN:
        print("Error: CLUSTER_TOKEN environment variable required")
        print("Usage: CLUSTER_TOKEN=cl_xxx python -m sre_agent.job_poller")
        sys.exit(1)
    
    print(f"Starting job poller...")
    print(f"  SAAS_URL: {SAAS_URL}")
    print(f"  CLUSTER_TOKEN: {CLUSTER_TOKEN[:15]}...")
    print(f"  Poll interval: {POLL_INTERVAL_SECONDS}s")
    print()
    
    try:
        asyncio.run(run_poller_forever())
    except KeyboardInterrupt:
        print("\nStopped.")
