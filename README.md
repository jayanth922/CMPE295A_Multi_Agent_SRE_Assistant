# Autonomous SRE Platform (Agentic)

![Status](https://img.shields.io/badge/Status-Production%20Ready-green)
![Architecture](https://img.shields.io/badge/Architecture-Event%20Driven-blue)
![Agents](https://img.shields.io/badge/Agents-LangGraph-orange)

An autonomous, event-driven Site Reliability Engineering (SRE) platform that automates incident response. Built on **LangGraph** and the **Model Context Protocol (MCP)**, it observes observability signals (Prometheus/Loki), orients using specialist agents, decides on remediation plans, and executes actions with safety guardrails.

## 🚀 Key Features

*   **Closed-Loop Autonomy:** Implements the OODA loop (Observe, Orient, Decide, Act) for full incident lifecycle management.
*   **Zero-Mock Architecture:** Integrates with *real* infrastructure (Prometheus, Loki, Kubernetes, GitHub, Notion) via MCP. No synthetic data paths.
*   **Safety First:** Policy-as-Code guardrails ensure no destructive action is taken without approval (unless configured otherwise).
*   **Specialist Agents:**
    *   **Kubernetes Agent:** Pod/Deployment diagnostics and remediation.
    *   **Logs Agent:** Semantic log analysis using Loki.
    *   **Metrics Agent:** Golden signal analysis (Latency, Traffic, Errors, Saturation).
    *   **Runbooks Agent:** RAG-based runbook retrieval from Notion.
    *   **GitHub Agent:** Correlates deployments with incidents and safeguards code (Reverts).
*   **Live Control Center:** Real-time dashboard for monitoring agent reasoning and system health.

## 🏗️ Architecture & Workflow

### 1. System Architecture

This project is an **Autonomous SRE Agent** built on an event-driven, microservices architecture. It uses **LangGraph** for stateful orchestration and the **Model Context Protocol (MCP)** to interface with real infrastructure.

#### Core Components

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

### 2. The Workflow (OODA Loop)

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

### 3. File-by-File Explanation

#### Root Directory
*   `README.md`: The entry point documentation.
*   `start.sh / stop.sh`: Automation scripts for one-click Docker Compose and environment setup.
*   `Makefile`: Development commands (linting, formatting, testing).
*   `pyproject.toml`: Python dependency definitions (using `uv` package manager).

#### 📂 infrastructure/
Contains deployment configurations.
*   `docker-compose.yaml`: The main stack definition. Runs Agent, Dashboard, Databases, and MCP servers.
*   `k8s/`: Kubernetes manifests for production deployment (Base/Kustomize).

#### 📂 sre_agent/
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

#### 📂 mcp_servers/
Independent tool providers (Microservices).
*   `k8s_real/`:
    *   `server.py`: FastMCP server exposing `kubectl` wrappers.
*   `github_real/`:
    *   `server.py`: Exposes GitHub API tools (PyGithub).
*   `prometheus_real/`:
    *   `server.py`: Exposes PromQL querying tools.
    *   (Similar structure for `loki_real`, `notion_real`, `memory_real`).

#### 📂 dashboard/
The Frontend application (Next.js / React).
*   `app/`: Next.js App Router pages.
    *   `page.tsx`: Main landing page (Cluster list).
    *   `clusters/[id]/page.tsx`: Detailed cluster view (The "Mission Control").
*   `components/dashboard/`: React components.
    *   `MissionControl.tsx`: The terminal-like interface showing live logs.
    *   `MetricSparklines.tsx`: Visualizations for latency/error rates.
    *   `IncidentCommandCenter.tsx`: The layout container.

#### 📂 scripts/
Utility scripts for maintenance.
*   `seed_runbooks.py`: Populates the Notion database with initial SRE runbooks.
*   `k8s-apply.sh`: Helper to deploy the stack to a Kubernetes cluster.
*   `audit_runbooks.py`: Helper to verify Notion content.

#### 📂 backend/
The Persistence Layer (SQLAlchemy / Postgres).
*   `models.py`: Database schema definitions (Users, Clusters, Incidents).
*   `crud.py`: Create/Read/Update/Delete operations.
*   `database.py`: DB connection management. |

---

## 🛠️ Quick Start

**Prerequisites:** Docker, Docker Compose, and `git`.

### 1. Clone the repository
```bash
git clone https://github.com/jayanth922/CMPE295A_Multi_Agent_SRE_Assistant.git
cd CMPE295A_Multi_Agent_SRE_Assistant
```

### 2. One-Click Startup
We provide a unified startup script that handles configuration and container orchestration.

```bash
./start.sh
```
*This script will generate a default `.env` file (using local Ollama with **Llama 3.2**) and launch the stack.*

### 3. Access the Platform
*   **Dashboard:** [http://localhost:3000](http://localhost:3000)
*   **Agent API:** [http://localhost:8080/docs](http://localhost:8080/docs)
*   **Observability:** *External (Configure in `.env`)*

### 4. Stop the System
```bash
./stop.sh
```

---

## ⚙️ Configuration

The system is configured via environment variables in `.env`.

### LLM Provider
By default, the system uses **Ollama** (local). To use **Groq** for higher performance:
```bash
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...
```

### Integrations (Optional)
To enable full capabilities for real-world usage, populate these keys in `.env`:
*   `GITHUB_TOKEN`: For commit analysis and revert PRs.
*   `NOTION_API_KEY` & `NOTION_RUNBOOK_DATABASE_ID`: For runbook RAG.
*   `PROMETHEUS_URL` & `LOKI_URL`: To point the agent at your production observability stack.

---

## 🧪 Development

This project adheres to strict coding standards. Use the `Makefile` for quality assurance.

```bash
make format    # Auto-format code (Black)
make lint      # Run linters (Ruff)
make quality   # Run full quality suite (Lint, Typecheck, Security)
make test      # Run unit tests
```

---

## 📚 Documentation
*   **[Master Architecture Doc](docs/MASTER_PROMPT.md):** Deep dive into system design and behavioral contracts.
*   **[Agent Configuration](sre_agent/config/agent_config.yaml):** Tool definitions and agent capabilities.

---

## 🤝 Contributing
1.  Fork the repository.
2.  Create a feature branch (`git checkout -b feature/amazing-agent`).
3.  Commit your changes.
4.  Open a Pull Request.

## 📄 License
MIT License. Copyright (c) 2026 Multi-Agent SRE Team.
