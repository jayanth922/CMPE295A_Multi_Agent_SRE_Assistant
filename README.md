# Multi-Agent SRE Assistant

An autonomous Site Reliability Engineering platform that investigates production incidents, plans remediations, and executes fixes — with human approval at every high-risk step.

Built as a capstone project for CMPE295A at San José State University.

---

## What it does

When an alert fires in a customer's Kubernetes cluster, the platform:

1. **Observes** — dispatches a swarm of AI agents to query Kubernetes, Prometheus, Loki, GitHub, and runbook databases in parallel
2. **Orients** — a reflector agent correlates findings and identifies root cause
3. **Decides** — a planner proposes a remediation and scores its risk
4. **Acts** — a policy gate checks safety rules; a human approves if the action is risky; the executor runs the fix
5. **Verifies** — confirms the issue is resolved and closes the incident

All tool execution (querying the customer's infra) happens inside the customer's network via a lightweight edge agent. All AI reasoning happens on the SaaS platform. No customer data leaves their environment unintentionally.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    SaaS Platform (us)                        │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  sre-agent-api  (FastAPI + LangGraph)               │    │
│  │                                                     │    │
│  │   Webhook ──► Supervisor ──► Investigation Swarm    │    │
│  │                              (K8s / Metrics / Logs  │    │
│  │                               GitHub / Runbooks)    │    │
│  │               Reflector ──► Policy Gate ──► Exec    │    │
│  │               Verify ──► Incident Closed            │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────┐  ┌─────────┐  ┌────────┐  ┌──────────┐    │
│  │  PostgreSQL │  │  Redis  │  │ Qdrant │  │  Ollama  │    │
│  └─────────────┘  └─────────┘  └────────┘  └──────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Dashboard (Next.js)                                │    │
│  │  Cluster overview · Incidents · Approvals · Audit   │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
              ▲  Job Queue (CLUSTER_TOKEN auth)  ▼
              ▲  Tool results                    ▼
┌──────────────────────────────────────────────────────────────┐
│                  Customer Edge (edge_agent/)                  │
│                                                              │
│   edge-relay  ──► mcp-k8s        (Kubernetes API)           │
│                   mcp-prometheus  (Metrics queries)          │
│                   mcp-loki        (Log queries)              │
│                   mcp-github      (Code + PRs)               │
│                   mcp-notion      (Runbooks)                 │
│                                                              │
│   No LLM. No AI. Just reads customer infra and returns data. │
└──────────────────────────────────────────────────────────────┘
              ▲  Alertmanager webhook  ▼
┌──────────────────────────────────────────────────────────────┐
│              Customer Infrastructure (existing)              │
│   K8s Cluster · Prometheus · Loki · Alertmanager · GitHub    │
└──────────────────────────────────────────────────────────────┘
```

### Key design decisions

| Decision | Rationale |
|---|---|
| Tool execution on customer edge | Customer data never leaves their network |
| AI reasoning on SaaS platform | Customers don't need GPUs |
| Outbound-only communication from edge | No inbound firewall rules required |
| Job queue pattern | Works through NAT/firewalls; edge polls SaaS |
| Human approval gate | High-risk PROD actions require explicit sign-off |
| Immutable audit trail | SOC2 compliance; every action logged |

---

## Repository structure

```
CMPE295A_Multi_Agent_SRE_Assistant/
│
├── backend/                  # Data layer (shared by sre_agent)
│   ├── models.py             # SQLAlchemy ORM: User, Org, Cluster, Incident, Job, SLO
│   ├── crud.py               # All database operations
│   ├── auth.py               # JWT + password hashing
│   ├── schemas.py            # Pydantic request/response types
│   ├── rbac.py               # Role enforcement (admin / member)
│   ├── rate_limit.py         # Sliding-window rate limiter
│   └── routers/auth.py       # Login and registration endpoints
│
├── sre_agent/                # Agent system + API server
│   ├── agent_runtime.py      # FastAPI app; webhook receiver; job orchestration
│   ├── multi_agent_langgraph.py  # MCP client setup; agent system factory
│   ├── graph_builder.py      # LangGraph state machine (OODA loop)
│   ├── job_poller.py         # Polls for pending jobs; streams telemetry
│   ├── mcp_tool_wrapper.py   # Retry + circuit breaker for MCP tool calls
│   ├── policy_engine.py      # Deterministic safety rules
│   ├── agent_nodes.py        # Individual agent node implementations
│   ├── supervisor.py         # Routing logic between OODA phases
│   └── api/v1/
│       ├── clusters.py       # Cluster CRUD + lock/unlock
│       ├── incidents.py      # Incident list + manual trigger
│       ├── mission_control.py # Audit logs + human approval
│       ├── agent_connect.py  # Edge agent heartbeat + telemetry
│       ├── jobs.py           # Job queue polling endpoint
│       └── slos.py           # SLO tracking + error budget
│
├── edge_agent/               # Shipped to customers
│   ├── edge_relay.py         # Polls SaaS; executes tool calls; no LLM
│   ├── docker-compose.yaml   # Edge stack (relay + 5 MCP servers)
│   └── mcp_servers/
│       ├── k8s_real/         # kubectl-equivalent queries
│       ├── prometheus_real/  # PromQL execution
│       ├── loki_real/        # LogQL execution
│       ├── github_real/      # GitHub API (commits, PRs, issues)
│       └── notion_real/      # Runbook lookup
│
├── platform/                 # SaaS infrastructure orchestration
│   ├── docker-compose.yaml   # Postgres, Redis, Qdrant, Ollama, API, Dashboard
│   ├── start.sh
│   └── stop.sh
│
└── dashboard/                # Next.js frontend
    ├── app/(auth)/           # Login / register
    └── app/(dashboard)/      # Cluster overview, incidents, audit logs
```

---

## How the OODA loop works

```
Alert received  (Alertmanager webhook  ──►  /api/v1/alerts/webhook)
         │
         ▼
   [SUPERVISOR]   decides which phase to enter
         │
         ▼  OBSERVE
   [INVESTIGATION SWARM]  — runs in parallel
    ├─ K8s agent      pod status, events, restart counts
    ├─ Metrics agent  CPU, memory, error rate, latency (PromQL)
    ├─ Logs agent     error patterns, stack traces (LogQL)
    ├─ GitHub agent   recent commits, open PRs, deployments
    └─ Runbooks agent existing SOPs for this alert type
         │
         ▼  ORIENT
   [REFLECTOR]   correlates all findings → root cause hypothesis
         │
         ▼  DECIDE
   [POLICY GATE]
    ├─ risk score < threshold  →  auto-approved
    └─ risk score ≥ threshold  →  paused, dashboard notified
                                  human approves or rejects
         │
         ▼  ACT
   [EXECUTOR]   dispatches tool calls through edge relay
         │
         ▼  VERIFY
   Metrics return to normal?  →  incident RESOLVED
                                 audit trail written
```

---

## Safety rules (policy engine)

The policy engine is evaluated before any action reaches the executor:

| Action | Environment | Behaviour |
|---|---|---|
| `RESTART` | PROD, risk score > 3.0 | Blocked |
| `DELETE` | PROD | Always blocked |
| `SCALE_DOWN` to 0 replicas | PROD | Blocked (causes outage) |
| `ROLLBACK` | PROD, no approval flag | Requires human approval |
| Any action | Non-PROD | Allowed |

---

## Data models

| Model | Purpose |
|---|---|
| `Organization` | Tenant; owns users and clusters |
| `User` | Email + hashed password + role (ADMIN / MEMBER) |
| `Cluster` | Customer K8s cluster; holds token and heartbeat |
| `Incident` | One per alert; tracks status (OPEN → INVESTIGATING → RESOLVED) |
| `Job` | Unit of work dispatched to edge (type: `INVESTIGATE`) |
| `AuditEvent` | Immutable record of every remediation action |
| `SLO` | Service level objective with error budget tracking |

Duplicate incident detection: if an incident with the same title is already OPEN or INVESTIGATING within the last 30 minutes, a new one is not created.

---

## Quickstart

### 1. Run the SaaS platform

```bash
cd platform
cp ../.env.example ../.env      # fill in SECRET_KEY, GROQ_API_KEY, etc.
docker compose up -d --build
```

API is up at `http://localhost:8080`. Dashboard at `http://localhost:3000`.

Seed the database (creates admin user + sample org):

```bash
python -m backend.seed
```

### 2. Deploy the edge agent (customer side)

```bash
cd edge_agent
cp .env.example .env            # fill in CLUSTER_TOKEN + your infra URLs
docker compose up -d --build
```

Get a `CLUSTER_TOKEN` from the dashboard after creating a cluster, or via the API:

```bash
curl -X POST http://localhost:8080/api/v1/clusters \
  -H "Authorization: Bearer <admin_jwt>" \
  -H "Content-Type: application/json" \
  -d '{"name": "prod-cluster", "org_id": 1}'
```

### 3. Trigger a test incident

```bash
curl -X POST http://localhost:8080/api/v1/clusters/1/trigger \
  -H "Authorization: Bearer <jwt>" \
  -H "Content-Type: application/json" \
  -d '{"title": "High error rate on checkout-service", "severity": "critical"}'
```

Watch the investigation in the dashboard under Incidents.

---

## Configuration

### SaaS platform (`.env`)

| Variable | Description |
|---|---|
| `SECRET_KEY` | JWT signing key (`openssl rand -hex 32`) |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `QDRANT_URL` | Qdrant vector DB endpoint |
| `LLM_PROVIDER` | `groq` or `ollama` |
| `GROQ_API_KEY` | Groq API key (if using Groq) |
| `OLLAMA_BASE_URL` | Ollama endpoint (if using Ollama) |
| `SEED_ADMIN_EMAIL` | Admin user created on first run |
| `SEED_ADMIN_PASSWORD` | Admin password |

### Edge agent (`edge_agent/.env`)

| Variable | Description |
|---|---|
| `CLUSTER_TOKEN` | Token from the SaaS dashboard |
| `SAAS_URL` | SaaS platform URL |
| `PROMETHEUS_URL` | Customer's Prometheus endpoint |
| `LOKI_URL` | Customer's Loki endpoint |
| `GITHUB_TOKEN` | GitHub personal access token |
| `GITHUB_REPO` | `org/repo` of the monitored codebase |
| `NOTION_API_KEY` | Notion integration token (optional) |
| `NOTION_RUNBOOK_DATABASE_ID` | Notion DB ID for runbooks (optional) |

---

## API reference

All endpoints require `Authorization: Bearer <jwt>` unless noted.

### Auth
| Method | Path | Notes |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Rate limited: 3 req/min |
| `POST` | `/api/v1/auth/login` | Rate limited: 5 req/min |

### Clusters
| Method | Path | Notes |
|---|---|---|
| `POST` | `/api/v1/clusters` | Create cluster, returns token |
| `GET` | `/api/v1/clusters` | List clusters for org |
| `DELETE` | `/api/v1/clusters/{id}` | Admin only |
| `POST` | `/api/v1/clusters/{id}/lock` | Emergency lock toggle (admin only) |
| `GET` | `/api/v1/clusters/{id}/audit` | Audit trail |

### Incidents
| Method | Path | Notes |
|---|---|---|
| `GET` | `/api/v1/clusters/{id}/incidents` | List incidents |
| `POST` | `/api/v1/clusters/{id}/trigger` | Manually trigger investigation |
| `POST` | `/api/v1/alerts/webhook` | Alertmanager webhook (no auth) |

### Mission control
| Method | Path | Notes |
|---|---|---|
| `GET` | `/api/v1/incidents/{id}/logs` | Audit + execution logs |
| `GET` | `/api/v1/incidents/{id}/status` | LangGraph execution state |
| `POST` | `/api/v1/incidents/{id}/approve` | Approve pending remediation |

### SLOs
| Method | Path | Notes |
|---|---|---|
| `POST` | `/api/v1/clusters/{id}/slos` | Create SLO |
| `GET` | `/api/v1/clusters/{id}/slos` | List SLOs |
| `GET` | `/api/v1/clusters/{id}/slos/{slo_id}/status` | Error budget remaining |

### Edge agent (authenticated by CLUSTER_TOKEN)
| Method | Path | Notes |
|---|---|---|
| `POST` | `/api/v1/agent/heartbeat` | Liveness signal (30 req/min) |
| `POST` | `/api/v1/agent/telemetry` | Forward metrics/logs (60 req/min) |
| `GET` | `/api/v1/clusters/jobs/pending` | Poll for tool-call jobs |

---

## Tech stack

| Layer | Technology |
|---|---|
| Agent orchestration | LangGraph, LangChain |
| LLM | Groq (cloud) or Ollama (self-hosted) |
| Tool protocol | Model Context Protocol (MCP) via FastMCP |
| API server | FastAPI (async, Python 3.12) |
| Database | PostgreSQL + SQLAlchemy async + Alembic |
| Cache / state | Redis |
| Vector memory | Qdrant |
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Auth | JWT (python-jose) + OAuth2PasswordBearer |
| Containers | Docker, Docker Compose |
| Observability | Prometheus + Loki + Alertmanager + Grafana |

---

## Demo app

`SRE_Demo_App/` (separate folder) simulates a customer's infrastructure with three intentionally flaky microservices. Alertmanager fires webhooks to the SaaS platform automatically. See `SRE_Demo_App/` for setup.
