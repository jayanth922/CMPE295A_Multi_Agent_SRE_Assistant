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

## 🧠 How It Works: The "Digital SRE"

To understand this project, imagine hiring a new Site Reliability Engineer (the **SRE Agent**). You give them access to your tools (Kubernetes, GitHub, Prometheus) and a runbook. This project automates that "Digital SRE" using AI.

### 1. The Core Concept (OODA Loop)
The agent doesn't just "chat." It thinks and acts in a loop, exactly like a human engineer:

1.  **👀 Observe (Investigation):** "I see an alert. Let me check the logs and metrics to see what's broken."
2.  **🧠 Orient (Reflection):** "The logs show a database error starting 5 minutes ago. This matches the deployment of `v2.0`."
3.  **💡 Decide (Planning):** "I should revert the last commit to fix this immediately. I need approval first."
4.  **✋ Act (Execution):** "Approval granted. Running `git revert` and deploying."
5.  **✅ Verify:** "Latency is back to normal. Incident closed."

This loop is built using **LangGraph**, which defines these steps as a "State Machine" in `sre_agent/graph_builder.py`.

---

### 2. The Components (The "Body")

*   **The Brain (`sre_agent/`):** This is the Python application. It receives alerts (webhooks) and decides what to do. It holds the "State" of the incident in memory.
*   **The Hands (`mcp_servers/`):** The Brain cannot touch your infrastructure directly. It uses **MCP Servers** as "hands" or "drivers."
    *   Need to check Kubernetes? The Brain asks the `k8s_real` server.
    *   Need to query metrics? The Brain asks the `prometheus_real` server.
    *   *Why?* This keeps the Brain generic. It doesn't know *how* to talk to K8s, it just asks the "K8s Hand" to do it.
*   **The Eyes (`dashboard/`):** A real-time Control Room. Since the agent acts autonomously, you need to trust it. The dashboard shows you exactly what the agent is "thinking" (Thought Traces) and lets you approve/reject critical actions (like `revert_commit`).

---

### 3. Deep Dive: Code Structure

Here is exactly what you are looking at in the codebase:

#### 📂 `sre_agent/` (The Brain)
*   **`agent_runtime.py`**: The " Ears." A web server (FastAPI) that listens for Alerts from Prometheus (`POST /webhook/alert`). When an alert hits this file, the agent wakes up.
*   **`graph_builder.py`**: The "Map." This file defines the flowchart of the agent's brain. It connects the nodes: `Investigator` -> `Planner` -> `Executor`.
*   **`agent_nodes.py`**: The "Skills." Each function here (`investigation_node`, `execution_node`) performs the actual thinking for that step of the flow.
*   **`policy_engine.py`**: The "Conscience." Before doing anything dangerous (like restarting a DB), the agent checks this file. If the Risk Score is high, it pauses and waits for Human Approval.
*   **`config/agent_config.yaml`**: The "Resume." Lists what tools each sub-agent is allowed to use. (e.g., "The GitHub Agent is allowed to `create_pr`").

#### 📂 `infrastructure/` (The World)
*   **`docker-compose.yaml`**: The "Blueprint." Describes how to spin up the entire world: the Agent, the Dashboard, the Databases (Redis/Postgres), and the MCP Tool Servers.
*   **`k8s/`**: The "Production Instructions." If you want to deploy this to a real Cloud cluster, you use these files.

#### 📂 `mcp_servers/` (The Tools)
*   **`k8s_real/server.py`**: A tiny server that just knows how to run `kubectl` commands.
*   **`github_real/server.py`**: A tiny server that knows how to use the GitHub API.
*   *Note: These are separate from the agent so they can be swapped out easily.*

#### 📂 `dashboard/` (The Interface)
*   **`app/clusters/[id]/page.tsx`**: The main code for the "Mission Control" page you see in the browser.
*   **`components/dashboard/MissionControl.tsx`**: The specific component that renders the scrolling "Terminal" logs of the agent's actions.

#### 📂 `scripts/` (Helpers)
*   **`start.sh`**: A simple script that runs `docker compose up` so you don't have to remember the commands.
*   **`seed_runbooks.py`**: A helper that fills your Notion database with template Runbooks (like "How to fix high latency") so the agent has something to read.

---

### 4. Example Scenario: "The Bad Deployment"

1.  **You** push bad code. CI/CD deploys it.
2.  **Prometheus** (Infrastructure) notices high latency and fires an alert to `sre-agent`.
3.  **`agent_runtime.py`** receives the alert and starts a new generic Session.
4.  **`graph_builder.py`** (The Graph) starts the `Investigator` node.
5.  **`agent_nodes.py`** (Investigator) asks: "I need to check recent deployments." -> Calls `mcp-k8s`.
6.  **`mcp-k8s`** server replies: "Deployment `frontend-v2` happened 1 min ago."
7.  **`agent_nodes.py`** (Reflector) thinks: "Timing matches. High confidence this caused it."
8.  **`agent_nodes.py`** (Planner) proposes: "Revert commit `a1b2c3d`."
9.  **`policy_engine.py`** flags this as "High Risk."
10. **Dashboard** shows a "Waiting for Approval" button.
11. **You** click "Approve."
12. **`agent_nodes.py`** (Executor) calls `mcp-github` -> `create_revert_pr`.
13. **Result:** PR created, incident resolved. |

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
