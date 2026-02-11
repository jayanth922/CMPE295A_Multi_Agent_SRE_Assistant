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

## 📖 Deep Dive: How It Works

### 1. The Concept: "The Autonomous SRE"

Imagine a Senior Site Reliability Engineer who never sleeps. This agent doesn't just "alert" you; it investigates, thinks, plans, and acts.

*   **The Brain (SRE Agent):** Uses **LangGraph** to maintain a persistent state of the incident. It thinks in loops (Observe -> Orient -> Decide -> Act).
*   **The Hands (MCP Servers):** The agent cannot touch your infrastructure directly. It asks "Tools" to do it. Tools are safely isolated in **MCP Servers** (Model Context Protocol).
    *   *Need logs?* Ask the Loki MCP.
    *   *Need to revert code?* Ask the GitHub MCP.
*   **The Eyes (Dashboard):** A real-time mission control where you can watch the agent "think" (trace its reasoning) and approve its dangerous plans.

---

### 2. Anatomy of an Incident (The Workflow)

Here is exactly what happens when an alert fires, step-by-step:

#### Phase 1: The Trigger 🚨
*   **Prometheus** detects a spike in 500 errors.
*   It sends a JSON webhook to the **Agent's API** (`/webhook/alert`).
*   **Agent Runtime** (`agent_runtime.py`) receives it, validates it, and spins up a new **Investigation Session**.

#### Phase 2: Observation (The Swarm) 🔍
*   The **Supervisor** (`supervisor.py`) looks at the alert labels. "Oh, this is a Kubernetes High Error Rate."
*   It wakes up the **Kubernetes Agent** and **Logs Agent**.
*   **K8s Agent:** uses `k8s_real` MCP to run `kubectl get pods` and `kubectl describe pod`. "Aha! The frontend-v2 pod is CrashLoopBackOff."
*   **Logs Agent:** uses `loki_real` MCP to query logs. "I see a `NullPointerException` in `checkout.js`."
*   They save these findings into the shared **Agent State** (`agent_state.py`).

#### Phase 3: Orientation (The Hypothesis) 💡
*   The **Reflector Node** reads the findings.
*   It checks **GitHub MCP**: "Was there a recent deployment?" -> "Yes, commit `a1b2c` was merged 10 minutes ago."
*   **Hypothesis:** "Commit `a1b2c` introduced a bug in `checkout.js` causing a crash loop."

#### Phase 4: Decision (The Plan) 🛡️
*   The **Planner Node** (`agent_nodes.py`) formulates a solution.
*   **Plan:** "Revert Commit `a1b2c`."
*   **Safety Check:** The **Policy Engine** (`policy_engine.py`) scans the plan.
    *   *Risk:* HIGH (Reverting code affects production).
    *   *Policy:* "High risk actions require Human Approval."
*   The agent pauses and pings the **Dashboard**.

#### Phase 5: Action (The Execution) ⚡
*   **You** see the "Approve Revert?" button on the Dashboard (`MissionControl.tsx`). You click **Approve**.
*   The **Executor Node** wakes up.
*   It calls `github_real` MCP -> `create_revert_pr` -> `merge_pr`.
*   The code is reverted. The pod stabilizes.

#### Phase 6: Verification ✅
*   The **Verifier Node** queries Prometheus again. "Error rate has dropped to 0%."
*   Case Closed.

---

### 3. Detailed File Guide (Where does code live?)

#### 🧠 The Core Brain (`sre_agent/`)
This directory contains the logic for the "Senior SRE" bot.
*   `agent_runtime.py`: **The Front Door.** A FastAPI server that listens for webhooks. It initializes the graph for each new incident.
*   `graph_builder.py`: **The Map.** Defines the flow of the agent. "After A, go to B". It wires together all the nodes (Investigator -> Planner -> Executor).
*   `agent_nodes.py`: **The Workers.** Python functions for each step.
    *   `investigator_node`: Decides which tools to call.
    *   `planner_node`: Writes the remediation YAML.
*   `agent_state.py`: **The Memory.** Defines the data structure (Pydantic models) passed between nodes. Think of this as the "Incident Notebook" passed around the room.
*   `policy_engine.py`: **The Lawyer.** Checks every plan against a set of rules (Policy as Code). "You cannot restart a database without approval."
*   `config/agent_config.yaml`: **The Tool Belt.** Lists which Agent is allowed to use which MCP Tool.

#### 🛠️ The Infrastructure (`infrastructure/`)
*   `docker-compose.yaml`: **The Blueprint.** Defines how to spin up the entire "Company in a Box".
    *   Starts `sre-agent` (The Brain).
    *   Starts `dashboard` (The UI).
    *   Starts `mcp-*` servers (The Tools).
    *   Starts `redis` (Hot memory) and `postgres` (Long-term memory).

#### � The Tools (`mcp_servers/`)
Each folder here is a tiny, isolated microservice.
*   `k8s_real/server.py`: A Python server that knows how to talk to your local Kubernetes cluster (`~/.kube/config`). Exposes tools like `get_pod_logs`.
*   `github_real/server.py`: Knows how to talk to GitHub API. Exposes `create_pull_request`.
*   *Why split them?* Security and isolation. The Agent code never imports `kubernetes`. It just asks the MCP server.

#### �️ The Dashboard (`dashboard/`)
A Next.js (React) application.
*   `app/clusters/[id]/page.tsx`: The main "War Room" page.
*   `components/dashboard/MissionControl.tsx`: The black terminal-like window that streams the agent's "Thoughts". It connects via WebSocket to the Agent.
*   `components/dashboard/IncidentCommandCenter.tsx`: The layout that holds logs, metrics sparklines, and action buttons.

#### � The Backend (`backend/`)
Handles persistent storage for the UI.
*   `models.py`: Database tables (SQLAlchemy) for `Incidents`, `Users`, and `AuditLogs`.
*   `crud.py`: Functions to Save/Load these objects from Postgres. |

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
