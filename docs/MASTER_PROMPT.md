# Master Prompt: CMPE295A Multi-Agent SRE Platform

Use this document to ground another AI when working on this codebase. It describes architecture, conventions, and where key behavior lives.

---

## 1. Project identity

- **Name:** CMPE295A Multi-Agent SRE Assistant (Digital SRE).
- **Goal:** Event-driven, closed-loop autonomic SRE: ingest Prometheus alerts, investigate via specialist agents, plan remediation, gate by policy, execute (including GitHub revert PRs), verify, and surface everything in a Live SRE Control Center.
- **Philosophy:** Production-grade, **zero-mock** for data paths: real Prometheus, Loki, Redis, Qdrant, MCP servers. No synthetic metrics or fake backends in the main flow. The only “simulation” is the UI’s “Trigger Bad Commit Alert,” which sends a **real** webhook to the backend (demo trigger, not mock data).

---

## 2. Architecture at a glance

- **Orchestration:** LangGraph `StateGraph` (cyclic OODA loop).
- **Flow:** OBSERVE → ORIENT → DECIDE → ACT → VERIFY.
- **Tooling:** Model Context Protocol (MCP). All tools are provided by MCP servers; no ad-hoc API wrappers in the agent core.
- **Data:** Pydantic V2 for all cross-node payloads; agents output structured JSON, not free text, between nodes.
- **Safety:** Every write (e.g. revert PR, restart) goes through policy gate; human approval is required unless `auto_approve_plan` is set (default: false).
- **Observability:** Prometheus-aligned (Golden Signals, SLOs); dashboard shows real metrics from Prometheus. If Prometheus is down, `/metrics/snapshot` returns **503** (no mock data).

---

## 3. Repo layout (what lives where)

| Path | Purpose |
|------|--------|
| `sre_agent/` | Core agent: graph, state, nodes, runtime API, MCP wiring. |
| `sre_agent/agent_state.py` | `AgentState` TypedDict + Pydantic models: `AlertContext`, `InvestigationFindings`, `ReflectorAnalysis`, `RemediationPlan`, `RemediationAction`, `VerificationResult`. |
| `sre_agent/graph_builder.py` | Builds LangGraph: nodes (investigation_swarm, reflector, planner, policy_gate, executor, verifier, aggregate), edges, routing. **Single source of truth** for graph shape. |
| `sre_agent/agent_nodes.py` | Factory functions for specialist agents (Kubernetes, Logs, Metrics, Runbooks, GitHub); each agent is bound to MCP tools per `agent_config.yaml`. |
| `sre_agent/agent_runtime.py` | FastAPI app: `/webhook/alert`, `/approve/{session_id}`, `/metrics/snapshot`, `/agent/state`, `/ping`. No mock fallbacks; 503 when Prometheus unavailable. |
| `sre_agent/multi_agent_langgraph.py` | MCP client setup (`MultiServerMCPClient`), tool loading from env URIs, `create_multi_agent_system()` which calls `build_multi_agent_graph()` and injects agents into state metadata. |
| `sre_agent/config/agent_config.yaml` | Maps agent names to tool names (e.g. `github_agent`: `create_revert_pr`, `comment_on_pr`, `revert_pr`). |
| `sre_agent/config/prompts/` | System/user prompts for supervisor, reflector, planner, runbooks, logs, metrics, kubernetes, github agents. |
| `sre_agent/context_builder.py` | Enriches incoming webhook alert with extra context before starting the graph. |
| `sre_agent/policy_engine.py` | Risk scoring and action evaluation for policy_gate. |
| `sre_agent/supervisor.py` | Supervisor agent used in aggregation/planning (if referenced). |
| `mcp_servers/` | One dir per MCP server: `k8s_real`, `prometheus_real`, `github_real`, `loki_real`, `notion_real`, `memory_real`. Each has `server.py`, `Dockerfile`, `requirements.txt`. |
| `mcp_servers/github_real/server.py` | GitHub MCP: `create_revert_pr(commit_sha, pr_title)`, `comment_on_pr(pr_number, comment)`, plus read tools (`list_commits`, `get_commit`, etc.). |
| `ui/streamlit_app.py` | Live SRE Control Center: left = real-time metrics (from `/metrics/snapshot`), right = agent reasoning/approvals. “Simulation mode” = button to send real alert webhook. |
| `target_app/` | **REMOVED** (Decoupled). The agent is now generic and connects to any app via Prometheus/Loki. |
| `docker-compose.yaml` | Stack: sre-agent, dashboard, prometheus, locus, redis, qdrant, MCP servers. |
| `config/prometheus.yml` | Prometheus scrape config. |

---

## 4. OODA loop (graph nodes)

1. **investigation_swarm** (OBSERVE): Runs Kubernetes, Logs, Metrics, Runbooks, GitHub agents in parallel; fills `investigation_findings`.
2. **reflector** (ORIENT): Consumes findings, produces `ReflectorAnalysis` (discrepancies, hypothesis, confidence). Can route back to `investigation_swarm` or to `planner`.
3. **planner** (DECIDE): Produces `RemediationPlan` (actions, risk, approval flag, verification_metrics).
4. **policy_gate**: Evaluates plan (policy_engine); routes to `executor` or `aggregate` (e.g. reject).
5. **executor** (ACT): Executes actions. For `revert_commit`: calls MCP `create_revert_pr`, then `comment_on_pr` with reasoning. No silent mocking; failures surface.
6. **verifier** (VERIFY): Re-checks metrics/SLOs, produces `VerificationResult`.
7. **aggregate**: Final summary and transition to END.

State is carried in `AgentState`; keys include `alert_context`, `investigation_findings`, `reflector_analysis`, `remediation_plan`, `execution_results`, `verification_result`, `thought_traces`, `session_id`, `metadata`.

---

## 5. Remediation actions and executor

- **Action types** (in `agent_state.py`): `restart`, `scale`, `rollback`, `config_change`, `patch`, `escalate`, `revert_commit`.
- **Executor** (`graph_builder.py`): `_map_action_to_tool` maps `revert_commit` → `create_revert_pr`; `_prepare_tool_args` fills `commit_sha`, `pr_title` from plan/action. After `create_revert_pr`, executor parses PR number/URL and calls `comment_on_pr(pr_number, reasoning)`.
- Tool results may be objects with `.content`/`.text` or JSON strings; parsing handles both.

---

## 6. API contract (agent runtime)

- **POST /webhook/alert**  
  Body: Prometheus Alertmanager payload (`alerts[]` with `labels`, `annotations`, etc.). Enriches via `ContextBuilder`, creates `AlertContext`, invokes graph. Returns session/investigation info.
- **POST /approve/{session_id}**  
  Marks plan approved for that session; graph continues to executor.
- **GET /metrics/snapshot**  
  Returns CPU usage and HTTP error rate from Prometheus. **503** with `prometheus_unavailable` when Prometheus is down (no mock).
- **GET /agent/state**, **GET /agent/state/{session_id}**  
  Return active investigations, thought traces, pending approvals (from Redis when available).
- **GET/HEAD /ping**  
  Health check for Docker/load balancers.

---

## 7. UI (Streamlit)

- **Left:** Real-time metrics (polling `/metrics/snapshot`); history for CPU and error rate. If backend returns 503, metrics are not updated (no fake data).
- **Right:** Agent activity, thought traces (deduplicated by `agent_name:thought_text`), pending approvals. For plans containing `revert_commit`, a clear warning is shown before approval.
- **Simulation mode:** Toggle + “Trigger Bad Commit Alert” sends a real POST to `/webhook/alert` with a synthetic alert payload (for demos). This is event simulation, not data mocking.

---

## 8. Zero-mock checklist (for changes)

- **Metrics:** No synthetic time series; `/metrics/snapshot` returns 503 when Prometheus is unreachable.
- **MCP servers:** All production servers (`*_real`); no mock MCPs in the main pipeline.
- **Executor:** No silent mock execution; failures are logged and surfaced.
- **UI:** Only “simulate” is the alert trigger; all displayed metrics/state come from backend/Prometheus or show “unavailable.”

---

## 9. Conventions for edits

- **State shape:** Extend `AgentState` and Pydantic models in `agent_state.py`; keep all cross-node structs in Pydantic V2.
- **New action type:** Add to `RemediationAction.action_type`, then implement mapping and args in `graph_builder.py` (`_map_action_to_tool`, `_prepare_tool_args`) and execution in executor node.
- **New MCP tool:** Add tool in the appropriate `mcp_servers/*/server.py`, then add the tool name to `sre_agent/config/agent_config.yaml` for the right agent.
- **New graph node:** Add node and edges in `graph_builder.py`; update routing and any conditional edges.
- **Env:** Secrets and URIs in `.env` (see `.env.example`); e.g. `GROQ_API_KEY`, `MCP_*_URI`, `PROMETHEUS_URL`, `REDIS_URL`.

---

## 10. Testing / run

- **Local stack:** `docker-compose up -d`; Dashboard at 3000, SRE Agent at 8080.
- **Smoke test:** Use the "Simulate Alert" button in the Dashboard (or POST to `/webhook/alert` manually) to trigger the agent. check logs: `docker-compose logs -f sre-agent`.
- **Kubernetes (optional):** `k8s/` and `scripts/kind-*.sh`, `k8s-apply.sh` for kind-based testing.

Use this master prompt as the single reference for architecture, data flow, and “what is mock vs real” when making or reviewing changes.
