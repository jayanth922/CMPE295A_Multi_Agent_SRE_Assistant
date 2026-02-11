# Multi-Agent SRE Assistant

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

## 🏗️ Architecture

The system is composed of decoupled microservices running in Docker:

| Service | Description |
| :--- | :--- |
| **SRE Agent** | The core brain. FastAPI runtime hosting the LangGraph state machine. |
| **Dashboard** | Next.js UI for real-time observation and human-in-the-loop approvals. |
| **MCP Servers** | Standalone tool providers (K8s, Prometheus, Loki, GitHub, Notion, Memory). |
| **Vector Store** | Qdrant for semantic memory and RAG. |
| **Observability** | Prometheus and Loki for self-monitoring and target app monitoring. |

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
*This script will generate a default `.env` file (using local Ollama LLM) and launch the stack.*

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
MIT License. Copyright (c) 2024 CMPE295A Team.
