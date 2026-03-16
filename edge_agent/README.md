# SRE Edge Agent

The lightweight agent you deploy inside your Kubernetes cluster. It has no AI or LLM — it only reads your existing infrastructure and relays data to the SaaS platform for analysis.

---

## What it contains

```
edge_agent/
├── edge_relay.py         # Core relay: polls SaaS for jobs, executes tool calls
├── docker-compose.yaml   # Runs the relay + all MCP servers
├── Dockerfile            # Builds the relay container
├── .env.example          # Configuration template
├── k8s/
│   └── mcp-k8s-rbac.yaml # RBAC rules for the K8s MCP server
└── mcp_servers/
    ├── k8s_real/         # Reads pods, events, logs, deployments
    ├── prometheus_real/  # Executes PromQL queries
    ├── loki_real/        # Executes LogQL queries
    ├── github_real/      # Reads commits, PRs, issues
    └── notion_real/      # Looks up runbooks
```

---

## How it works

```
SaaS Platform                          Edge Agent
     │                                     │
     │  GET /api/v1/clusters/jobs/pending  │
     │ ◄────────────────────────────────── │  (polls every 3s)
     │                                     │
     │  { job_type: "tool_call",           │
     │    tool: "query_prometheus",        │
     │    args: { query: "..." } }         │
     │ ──────────────────────────────────► │
     │                                     │
     │                           executes tool against
     │                           local Prometheus/K8s/Loki
     │                                     │
     │  POST /api/v1/jobs/{id}/result      │
     │ ◄────────────────────────────────── │
     │  { result: "..." }                  │
```

The edge agent never opens inbound ports. All communication is outbound from your network.

---

## Prerequisites

- Docker + Docker Compose
- Access to your Kubernetes cluster (`~/.kube/config`)
- Your Prometheus and Loki endpoints reachable from where you deploy the edge agent
- A `CLUSTER_TOKEN` from the SaaS platform (created in the dashboard)

---

## Setup

```bash
cp .env.example .env
```

Edit `.env`:

```env
CLUSTER_TOKEN=cl_...          # from the SaaS dashboard
SAAS_URL=https://your-sre-platform.example.com

PROMETHEUS_URL=http://prometheus:9090
LOKI_URL=http://loki:3100

GITHUB_TOKEN=ghp_...
GITHUB_REPO=your-org/your-repo

# optional
NOTION_API_KEY=secret_...
NOTION_RUNBOOK_DATABASE_ID=...
```

Start the stack:

```bash
docker compose up -d --build
```

Verify the relay is connected:

```bash
docker logs edge-relay -f
# Should show: "Heartbeat OK" every few seconds
```

---

## MCP servers

Each MCP server is a standalone FastAPI process that exposes tools over HTTP/SSE using the Model Context Protocol. The edge relay discovers tools from all servers at startup.

| Server | Port | Tools provided |
|---|---|---|
| `mcp-k8s` | 3000 | list_pods, get_pod_logs, restart_deployment, scale_deployment, get_events |
| `mcp-prometheus` | 3000 | query_metrics, get_alerts, query_range, get_targets |
| `mcp-loki` | 3000 | query_logs, get_log_streams, query_log_range |
| `mcp-github` | 3000 | get_recent_commits, get_open_prs, get_deployments, create_issue |
| `mcp-notion` | 3000 | search_runbooks, get_runbook, list_runbooks |

---

## Kubernetes deployment

Apply RBAC rules so the K8s MCP server can read cluster resources:

```bash
kubectl apply -f k8s/mcp-k8s-rbac.yaml
```

Then deploy the edge agent as a pod (update image references in `k8s/` manifests from the demo app if needed).

---

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `CLUSTER_TOKEN` | Yes | Authentication token from SaaS platform |
| `SAAS_URL` | Yes | SaaS platform base URL |
| `PROMETHEUS_URL` | Yes | Your Prometheus instance |
| `LOKI_URL` | Yes | Your Loki instance |
| `GITHUB_TOKEN` | Yes | GitHub PAT with repo read access |
| `GITHUB_REPO` | Yes | `org/repo` |
| `NOTION_API_KEY` | No | Enables runbook lookup |
| `NOTION_RUNBOOK_DATABASE_ID` | No | Notion database for runbooks |
| `POLL_INTERVAL_SECONDS` | No | Job poll frequency (default: 3) |
