# 🚀 How to Run the SRE Platform (Complete Guide)

This project has **3 separate stacks**. Each lives in its own folder and has its own `.env` file.

```
Main_Project/
├── CMPE295A_Multi_Agent_SRE_Assistant/   ← Stack 1: SaaS Platform (AI brain)
│   ├── platform/docker-compose.yaml
│   └── .env                              ← ENV FILE #1
│
├── SRE_Demo_App/                         ← Stack 2: Demo App (fake customer infra)
│   ├── docker-compose.yaml
│   └── .env                              ← ENV FILE #2
│
└── CMPE295A_Multi_Agent_SRE_Assistant/
    └── edge_agent/                       ← Stack 3: Edge Agent (bridges the two)
        ├── docker-compose.yaml
        └── .env                          ← ENV FILE #3
```

---

## Step 0: Stop everything (clean slate)

```powershell
cd "C:\Users\Ramro\OneDrive\Documents\a_code_folder\Git Projects\Main_Project\CMPE295A_Multi_Agent_SRE_Assistant\platform"
docker compose down -v

cd "C:\Users\Ramro\OneDrive\Documents\a_code_folder\Git Projects\Main_Project\SRE_Demo_App"
docker compose down -v

cd "C:\Users\Ramro\OneDrive\Documents\a_code_folder\Git Projects\Main_Project\CMPE295A_Multi_Agent_SRE_Assistant\edge_agent"
docker compose down -v
```

---

## Step 1: Start the SaaS Platform

### 1a. Set up the env file

The file already exists at:  
`CMPE295A_Multi_Agent_SRE_Assistant/.env`

Make sure it has:

```env
SECRET_KEY=your_secret_key_here
POSTGRES_USER=sre_user
POSTGRES_PASSWORD=sre_password
POSTGRES_DB=sre_platform
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_YOUR_KEY_HERE
SEED_ADMIN_EMAIL=admin@example.com
SEED_ADMIN_PASSWORD=admin123
```

### 1b. Start the containers

```powershell
cd "C:\Users\Ramro\OneDrive\Documents\a_code_folder\Git Projects\Main_Project\CMPE295A_Multi_Agent_SRE_Assistant\platform"
docker compose up -d --build
```

### 1c. Create the database tables

```powershell
docker exec sre-agent-api uv run alembic upgrade head
```

### 1d. Create the admin user

```powershell
docker exec sre-agent-api uv run python -m backend.seed
```

### 1e. Log in and create a cluster

1. Open **http://localhost:3000**
2. Log in: `admin@example.com` / `admin`
3. Click **"Add Cluster"** → name it anything → click **Create**
4. **Copy the token** (starts with `cl_...`) — you need it for the next 2 steps

> ⚠️ The token is shown **only once**. If you lose it, run:  
> `docker exec -it postgres psql -U sre_user -d sre_platform -c "SELECT name, token FROM clusters;"`

---

## Step 2: Start the SRE Demo App

### 2a. Create the env file

Create a new file at: `SRE_Demo_App/.env`

```env
# Paste the cluster token from Step 1e
CLUSTER_TOKEN=cl_PASTE_YOUR_TOKEN_HERE

# Fault injection (leave defaults)
CHECKOUT_ERROR_RATE=0.15
CHECKOUT_SLOW_RATE=0.20
INVENTORY_SLOW_QUERY_RATE=0.25
CHAOS_MODE=false

# Load generator
LOAD_RPS=5

# Grafana
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin
```

### 2b. Start the containers

```powershell
cd "C:\Users\Ramro\OneDrive\Documents\a_code_folder\Git Projects\Main_Project\SRE_Demo_App"
docker compose up -d --build
```

---

## Step 3: Start the Edge Agent

### 3a. Create the env file

Create a new file at: `CMPE295A_Multi_Agent_SRE_Assistant/edge_agent/.env`

```env
# Same cluster token from Step 1e
CLUSTER_TOKEN=cl_PASTE_YOUR_TOKEN_HERE
```

### 3b. Start the containers

```powershell
cd "C:\Users\Ramro\OneDrive\Documents\a_code_folder\Git Projects\Main_Project\CMPE295A_Multi_Agent_SRE_Assistant\edge_agent"
docker compose up -d --build
```

---

## 🌐 All Access Links

| What | URL | Login |
|---|---|---|
| **SaaS Dashboard** | http://localhost:3000 | `admin@example.com` / `admin` |
| **API Docs (Swagger)** | http://localhost:8080/docs | — |
| **Grafana** | http://localhost:3001 | `admin` / `admin` |
| **Prometheus** | http://localhost:9090 | — |
| **Alertmanager** | http://localhost:9093 | — |
| **Demo API Gateway** | http://localhost:8000 | — |

---

## ✅ How to verify it's working

| Check | How |
|---|---|
| SaaS is up | Open http://localhost:3000 — you see the dashboard |
| Demo App is running | Open http://localhost:8000/health — returns `ok` |
| Prometheus is scraping | Open http://localhost:9090/targets — all targets are UP |
| Alerts are firing | Open http://localhost:9090/alerts — wait 3-5 minutes |
| Edge agent is connected | Dashboard shows cluster as **Online** (green) |
| Incidents auto-created | Dashboard → cluster → incidents appear after alerts fire |

---

## 🔄 What happens automatically

```
Load Generator → Demo Microservices → errors/slowness
                         ↓
                   Prometheus scrapes metrics
                         ↓
                   Alert rules trigger (after 1-3 min)
                         ↓
                   Alertmanager fires webhook → SaaS API
                         ↓
                   SaaS creates incident + triggers AI investigation
                         ↓
                   Edge Agent polls for jobs, executes MCP tool calls
                         ↓
                   Results appear in Dashboard
```
