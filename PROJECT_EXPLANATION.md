# Project Architecture & File Guide

## 1. System Architecture

This project is an **Autonomous SRE Agent** built on an event-driven, microservices architecture. It uses **LangGraph** for stateful orchestration and the **Model Context Protocol (MCP)** to interface with real infrastructure.

### Core Components

1.  **SRE Agent (The Brain):**
    *   **Runtime:** Python FastAPI service.
    *   **Logic:** A LangGraph state machine implementing an **OODA Loop** (Observe, Orient, Decide, Act).
    *   **State:** Persisted in Redis (hot state) and Postgres (long-term incident history).
    *   **Memory:** Qdrant (Vector DB) for semantic recall of past incidents and runbooks.

2.  **MCP Servers (The Hands):**
    *   Standalone sidecar containers that expose specific tools to the agent.
    *   **k8s_real:** Interacts with the Kubernetes API (get pods, logs, describe).
    *   **prometheus_real / loki_real:** Queries metrics and logs.
    *   **github_real:** Manages code operations (list commits, create revert PRs).
    *   **notion_real:** Fetches runbooks and docs.

3.  **Dashboard (The Eyes):**
    *   A Next.js application providing a "Mission Control" interface.
    *   Real-time websocket connection to the Agent to stream "Thoughts" and "Actions".
    *   Human-in-the-loop approval gates for sensitive actions.

### The Workflow (OODA Loop)

The agent follows a cyclical workflow triggered by an alert:

1.  **Trigger (Webhook):** An alert arrives from Prometheus at `POST /webhook/alert`.
2.  **CONTEXT_BUILDER:** The payload is enriched. A unique `session_id` is generated.
3.  **OBSERVE (Investigation Swarm):**
    *   The **Supervisor** delegates to sub-agents (K8s, Logs, Metrics) based on the alert type.
    *   Agents call MCP tools (e.g., `search_logs`, `get_pod_status`) to gather data.
4.  **ORIENT (Reflector):**
    *   The agent analyzes findings against the "State of the World".
    *   It formulates a **Hypothesis** (e.g., "Commit X caused latency spike").
5.  **DECIDE (Planner):**
    *   A remediation plan is generated (e.g., "Revert Commit X" or "Restart Pod").
    *   **Policy Check:** The `policy_engine` assigns a risk score. High-risk actions require approval.
6.  **ACT (Executor):**
    *   If approved, the agent calls the executor tools (e.g., `github_create_pr`).
7.  **VERIFY (Verifier):**
    *   The agent re-checks metrics to confirm resolution.

---

## 2. File-by-File Explanation

### Root Directory
*   `README.md`: The entry point documentation.
*   `start.sh / stop.sh`: Automation scripts for one-click Docker Compose and environment setup.
*   `Makefile`: Development commands (linting, formatting, testing).
*   `pyproject.toml`: Python dependency definitions (using `uv` package manager).

### 📂 infrastructure/
Contains deployment configurations.
*   `docker-compose.yaml`: The main stack definition. Runs Agent, Dashboard, Databases, and MCP servers.
*   `k8s/`: Kubernetes manifests for production deployment (Base/Kustomize).

### 📂 sre_agent/
The core application logic (Python).
*   `agent_runtime.py`: The FastAPI server entry point. Handles webhooks and API routes.
*   `graph_builder.py`: Defines the LangGraph nodes and edges (the "State Machine" definition).
*   `agent_nodes.py`: Implementation of the graph nodes (Investigator, Planner, Executor).
*   `agent_state.py`: Pydantic models defining the data structure passed between nodes.
*   `supervisor.py`: Logic for the orchestrator agent that manages sub-agents.
*   `policy_engine.py`: "Safety Guardrails" logic. Evaluates plans for risk.
*   `job_poller.py`: Background worker that listens for Dashboard jobs (e.g., "Configure Cluster").
*   `config/agent_config.yaml`: Configuration mapping Agents to their allowed Tools.
*   `config/prompts/*.txt`: System prompts for the LLMs (defining their persona and instructions).

### 📂 mcp_servers/
Independent tool providers (Microservices).
*   `k8s_real/`:
    *   `server.py`: FastMCP server exposing `kubectl` wrappers.
*   `github_real/`:
    *   `server.py`: Exposes GitHub API tools (PyGithub).
*   `prometheus_real/`:
    *   `server.py`: Exposes PromQL querying tools.
    *   (Similar structure for `loki_real`, `notion_real`, `memory_real`).

### 📂 dashboard/
The Frontend application (Next.js / React).
*   `app/`: Next.js App Router pages.
    *   `page.tsx`: Main landing page (Cluster list).
    *   `clusters/[id]/page.tsx`: Detailed cluster view (The "Mission Control").
*   `components/dashboard/`: React components.
    *   `MissionControl.tsx`: The terminal-like interface showing live logs.
    *   `MetricSparklines.tsx`: Visualizations for latency/error rates.
    *   `IncidentCommandCenter.tsx`: The layout container.

### 📂 scripts/
Utility scripts for maintenance.
*   `seed_runbooks.py`: Populates the Notion database with initial SRE runbooks.
*   `k8s-apply.sh`: Helper to deploy the stack to a Kubernetes cluster.
*   `audit_runbooks.py`: Helper to verify Notion content.

### 📂 backend/
The Persistence Layer (SQLAlchemy / Postgres).
*   `models.py`: Database schema definitions (Users, Clusters, Incidents).
*   `crud.py`: Create/Read/Update/Delete operations.
*   `database.py`: DB connection management.
