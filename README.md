# Autonomous SRE Platform

![Status](https://img.shields.io/badge/Status-Production%20Ready-green)
![Architecture](https://img.shields.io/badge/Architecture-Event%20Driven-blue)
![License](https://img.shields.io/badge/License-MIT-purple)

An event-driven Site Reliability Engineering (SRE) platform that automates incident response using **LangGraph** orchestration and the **Model Context Protocol (MCP)**. This system observes infrastructure signals, investigates root causes, plans remediation via policy gates, and executes corrective actions on live environments.

---

## 🏗 System Architecture

The platform operates as a closed-loop control system (OODA Loop):

| Component | Responsibility | Technology |
|-----------|----------------|------------|
| **SRE Agent** | Core orchestration engine. Manages state, decision-making, and tool delegation. | Python, FastAPI, LangGraph |
| **MCP Servers** | Isolated sidecars providing secure access to infrastructure tools (K8s, GitHub, Prometheus). | Python, FastMCP, Docker |
| **Dashboard** | Real-time "Mission Control" UI for observing agent logs and approving sensitive actions. | Next.js, React, WebSocket |
| **State Store** | Persistence for incident history (`Postgres`) and active session state (`Redis`). | PostgreSQL, Redis |
| **Memory** | Semantic search for runbooks and past incident context. | Qdrant (Vector DB) |

---

## ✨ Features

*   **Autonomous Investigation:** Correlates alerts (Prometheus) with logs (Loki) and deployment events (GitHub) to identify root causes.
*   **Zero-Mock Data:** Connects directly to real infrastructure via MCP. No synthetic data paths.
*   **Policy-as-Code:** All remediation plans are evaluated by a Policy Engine. High-risk actions (e.g., `revert_commit`) trigger human-in-the-loop approval.
*   **Immutable Audit Logs:** All actions and decisions are cryptographically logged for post-incident review.
*   **One-Click Deployment:** fully containerized stack managed via Docker Compose.

---

## 🚀 Getting Started

### Prerequisites
*   **Docker** & **Docker Compose**
*   **Git**
*   **Make** (optional, for development)

### Quick Start

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/jayanth922/CMPE295A_Multi_Agent_SRE_Assistant.git
    cd CMPE295A_Multi_Agent_SRE_Assistant
    ```

2.  **Initialize and Start:**
    Run the startup script to generate configuration and launch the stack.
    ```bash
    ./start.sh
    ```
    *Note: This creates a default `.env` configured for local LLM inference (Llama 3.2 via Ollama).*

3.  **Access Interfaces:**
    *   **Dashboard:** [http://localhost:3000](http://localhost:3000)
    *   **Agent API:** [http://localhost:8080/docs](http://localhost:8080/docs)

4.  **Teardown:**
    ```bash
    ./stop.sh
    ```

---

## ⚙️ Configuration

The system is configured via the `.env` file. Key variables:

*   **LLM Configuration:**
    *   `LLM_PROVIDER`: `ollama` (local) or `groq` (cloud).
    *   `OLLAMA_MODEL`: Default is `llama3.2`.
*   **Integrations:**
    *   `GITHUB_TOKEN`: Required for the GitHub Agent to list commits/create PRs.
    *   `PROMETHEUS_URL`: Target endpoint for metric queries.
    *   `LOKI_URL`: Target endpoint for log queries.

---

## 📂 Repository Structure

### Service Components
*   **`sre_agent/`**: Core application logic.
    *   `graph_builder.py`: Defines the LangGraph state machine.
    *   `agent_nodes.py`: Implementation of workflow steps (Investigate, Plan, Execute).
    *   `policy_engine.py`: Logic for risk assessment and approval gates.
*   **`mcp_servers/`**: Microservices for tool exposure.
    *   `k8s_real/`: Adapts Kubernetes API to MCP.
    *   `github_real/`: Adapts GitHub API to MCP.
*   **`dashboard/`**: Frontend application source code (Next.js).
*   **`infrastructure/`**: IaC and deployment configurations.
    *   `docker-compose.yaml`: Service orchestration definition.
    *   `k8s/`: Kubernetes manifests for production deployment.

### Development Tools
*   **`Makefile`**: Automation for standard development tasks.
    *   `make quality`: Runs formatters (black), linters (ruff), and security checks (bandit).
    *   `make test`: Executes unit tests via pytest.
    *   *Usage ensures consistent code quality across the team.*
*   **`pyproject.toml`**: Centralized dependency management and tool configuration.
*   **`scripts/`**: Maintenance and utility scripts.
    *   `seed_runbooks.py`: Bootstraps knowledge base data.

---

## 🤝 Contributing

1.  Fork the repository.
2.  Install dependencies: `uv sync`
3.  Create a feature branch.
4.  Ensure quality checks pass: `make quality`
5.  Submit a Pull Request.

---

## 📄 License

MIT License. Copyright (c) 2026 Multi-Agent SRE Team.
