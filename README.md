# Autonomous SRE Platform (Agentic)

![Status](https://img.shields.io/badge/Status-Production%20Ready-green)
![Architecture](https://img.shields.io/badge/Architecture-Event%20Driven-blue)
![Agents](https://img.shields.io/badge/Agents-LangGraph-orange)

An **Autonomous Site Reliability Engineering (SRE) Agent** that doesn't just alert you—it investigates, plans, and fixes incidents using production-grade tools.

Built on **LangGraph** (Orchestration) and the **Model Context Protocol (MCP)** (Infrastructure Access).

---

## 🚀 Key Features

*   **The "Senior SRE" Brain:** Implements the OODA loop (Observe, Orient, Decide, Act) to solve problems like a human expert.
*   **Real Infrastructure, No Mocks:** Connects to *actual* Kubernetes clusters, GitHub repos, and Prometheus metrics via secure MCP tunnels.
*   **Safety Guardrails:** A "Policy Engine" reviews every plan. Risky actions (like `revert_commit`) require human approval via the dashboard.
*   **Mission Control:** A real-time UI to watch the agent "think" and execute.

---

## 📖 How It Works (Deep Dive)

### The Workflow: Anatomy of an Incident

1.  **Trigger 🚨:** A high-latency alert fires in Prometheus. It hits the agent's webhook.
2.  **Observe 🔍:** The **Supervisor** wakes up the **K8s Agent** and **Logs Agent**.
    *   *Agent:* "Get me logs for the `frontend` pod."
    *   *MCP:* Returns the crash log: `NullPointerException in header.tsx`.
3.  **Orient 💡:** The **Reflector** correlates findings.
    *   *Hypothesis:* "Commit `x89s0` (merged 5 mins ago) broke the header component."
4.  **Decide 🛡️:** The **Planner** proposes a fix: "Revert commit `x89s0`."
    *   *Policy Check:* "Reverting code is High Risk. Requesting Human Approval."
5.  **Act ⚡:** You see the request on the Dashboard and click **Approve**.
    *   The **Executor** calls the **GitHub MCP** to open and merge the revert PR.
6.  **Verify ✅:** The **Verifier** confirms metric stability.

---

## 📂 The File Guide (What is all this?)

You asked for a complete breakdown. Here is every file and folder explained:

### 🛠️ Developer Tools (Why do I need these?)
*   **`Makefile`:** Think of this as your "Command Shortcuts". Instead of typing long commands, you just type:
    *   `make format`: Beautifies your code (using Black).
    *   `make lint`: Checks for bugs/style issues (using Ruff).
    *   `make test`: Runs functionality tests (using Pytest).
    *   *Why?* It ensures every developer on the team maintains the same high code quality standard.
*   **`pyproject.toml`:** The configuration center for Python. It lists all libraries (dependencies) the project needs and configures the tools used in the Makefile.
*   **`.gitignore`:** Tells Git which files to *ignore* (like passwords or temporary build folders).

### 🧠 `sre_agent/` (The Brain)
The core Python application.
*   `agent_runtime.py`: The web server (FastAPI) that receives alerts.
*   `graph_builder.py`: **The most important file.** It defines the "Brain wiring" (the LangGraph state machine).
*   `agent_nodes.py`: The logic for each "step" of thinking (Investigator, Planner, Executor).
*   `agent_state.py`: The "Short-term Memory" where the agent writes its findings during an incident.
*   `policy_engine.py`: The "Safety Officer". It rejects dangerous plans.
*   `config/`: Configuration files and Prompts (the personality instructions for the AI).

### 🔌 `mcp_servers/` (The Hands)
The agent cannot touch your laptop/cloud directly. It asks these isolated servers to do it.
*   `k8s_real`: Knows how to talk to Kubernetes (`kubectl`).
*   `github_real`: Knows how to talk to GitHub.
*   `prometheus_real` / `loki_real`: Know how to query metrics and logs.

### 🖥️ `dashboard/` (The Eyes)
The User Interface (Next.js/React).
*   `app/clusters/[id]/page.tsx`: The main "War Room" screen.
*   `components/dashboard/MissionControl.tsx`: The terminal window that streams the agent's thoughts.

### 💾 `backend/` (The Memory)
Saves history to a database.
*   `models.py`: Defines tables (Incidents, Users).
*   `crud.py`: Functions to save/load data.

### 🏗️ `infrastructure/` (The Data Center)
*   `docker-compose.yaml`: The "Master Switch". It spins up the Agent, Dashboard, Database, and all MCP servers in one go.

---

## 🛠️ Quick Start

**Prerequisites:** Docker, Docker Compose, and Git.

### 1. One-Click Start
We created a script to handle everything for you.

```bash
./start.sh
```
*This script will:*
1.  Check for `.env` (and create a default one using **Llama 3.2**).
2.  Build all Docker containers.
3.  Start the entire stack.

### 2. Access the Platform
*   **Dashboard:** [http://localhost:3000](http://localhost:3000)
*   **Agent API:** [http://localhost:8080/docs](http://localhost:8080/docs)

### 3. Stop
```bash
./stop.sh
```

---

## ⚙️ Configuration (`.env`)

The system uses environment variables to connect to your real tools.

*   `LLM_PROVIDER`: `ollama` (default) or `groq`.
*   `GITHUB_TOKEN`: Your GitHub Personal Access Token (for the GitHub Agent).
*   `PROMETHEUS_URL`: URL of your Prometheus server (e.g. `http://host.docker.internal:9090`).

---

## 📄 License
MIT License. Copyright (c) 2026 Multi-Agent SRE Team.
