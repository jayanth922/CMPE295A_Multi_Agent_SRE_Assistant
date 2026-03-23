# SRE Demo App — Step-by-Step Run Guide

> A simulated e-commerce backend with fault injection + full observability stack (Prometheus, Grafana, Loki, Alertmanager).

---

## Prerequisites

Before you begin, make sure you have the following installed on your machine:

| Tool | Why You Need It | Installation Link |
|------|-----------------|-------------------|
| **Docker Desktop** | Runs all containers | [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop) |
| **Docker Compose** | Orchestrates multi-container setup (bundled with Docker Desktop) | Included with Docker Desktop |
| **Git** | Clone the repository | [git-scm.com](https://git-scm.com/) |

> [!IMPORTANT]
> Make sure Docker Desktop is **running** before proceeding. You can verify by opening a terminal and running `docker --version`.

---

## Step 1 — Clone the Repository

If you haven't already cloned the project:

```bash
git clone <your-repo-url>
cd SRE_Demo_App
```

---

## Step 2 — Create Your Environment File

Copy the example environment file to create your own `.env`:

**On Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**On macOS / Linux:**
```bash
cp .env.example .env
```

---

## Step 3 — Configure Environment Variables

Open the `.env` file in your editor and review/update the values:

```env
# SaaS Platform connection (optional — leave defaults if not using SaaS platform)
SAAS_WEBHOOK_URL=https://your-sre-platform.example.com/api/v1/alerts/webhook
CLUSTER_TOKEN=cl_your_token_here

# Fault injection knobs (safe to leave as defaults)
CHECKOUT_ERROR_RATE=0.15         # 15% payment failures
CHECKOUT_SLOW_RATE=0.20          # 20% slow checkouts
INVENTORY_SLOW_QUERY_RATE=0.25   # 25% slow DB queries
CHAOS_MODE=false                 # set true to spike checkout errors to ~50%

# Load generator
LOAD_RPS=5                       # steady-state requests/sec
LOAD_BURST_RPS=20                # burst requests/sec
LOAD_BURST_DURATION=15           # burst lasts N seconds
LOAD_BURST_INTERVAL=60           # burst every N seconds

# Grafana credentials
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin
```

> [!TIP]
> For a first-time run, the defaults work perfectly. You don't need to change anything unless you have a SaaS webhook URL.

---

## Step 4 — Build and Start All Services

Run the following command from the project root directory (`SRE_Demo_App/`):

```bash
docker compose up -d --build
```

**What this does:**
- Builds Docker images for the 4 custom services (api-gateway, checkout-service, inventory-service, load-generator)
- Pulls official images for the observability stack (Prometheus, Alertmanager, Loki, Promtail, Grafana)
- Starts all 9 containers in detached mode (`-d`)

> [!NOTE]
> The first build may take **2–5 minutes** as Docker downloads base images and installs Python dependencies. Subsequent builds will be much faster due to caching.

---

## Step 5 — Verify All Containers Are Running

Check that all containers are up and healthy:

```bash
docker compose ps
```

You should see **9 containers** all in the `Up` state:

| Container | Port | Status |
|-----------|------|--------|
| `api-gateway` | `8000` | Up |
| `checkout-service` | `8001` | Up |
| `inventory-service` | `8002` | Up |
| `load-generator` | — | Up |
| `prometheus` | `9090` | Up |
| `alertmanager` | `9093` | Up |
| `loki` | `3100` | Up |
| `promtail` | — | Up |
| `grafana` | `3000` | Up |

If any container is not running, check its logs:

```bash
docker compose logs <container-name>
```

For example:
```bash
docker compose logs checkout-service
```

---

## Step 6 — Access the Application UIs

Open the following URLs in your browser:

### 🛒 API Gateway (Swagger UI)
```
http://localhost:8000/docs
```
Interactive API documentation — test checkout and inventory endpoints directly.

### 📊 Grafana (Dashboards)
```
http://localhost:3000
```
- **Username:** `admin`
- **Password:** `admin`
- Pre-provisioned with Prometheus and Loki data sources.

### 🔍 Prometheus (Metrics)
```
http://localhost:9090
```
Query raw metrics and see active alert rules.

### 🚨 Alertmanager
```
http://localhost:9093
```
View currently firing alerts and alert routing configuration.

---

## Step 7 — Test the API Endpoints

You can test the services manually using `curl` or the Swagger UI at `http://localhost:8000/docs`.

### Health Check
```bash
curl http://localhost:8000/health
```

### Checkout an Order
```bash
curl http://localhost:8000/checkout/order123
```
> Expect ~15% of requests to fail and ~20% to be slow (by default).

### Get Inventory
```bash
curl http://localhost:8000/inventory
```
> Expect ~25% of requests to have slow responses (by default).

### View Raw Metrics
```bash
curl http://localhost:8000/metrics
```

---

## Step 8 — Watch the Load Generator in Action

The load generator automatically sends traffic to the API Gateway. View its live logs:

```bash
docker compose logs -f load-generator
```

It sends:
- **5 requests/sec** steady-state traffic
- **20 requests/sec** bursts every 60 seconds (lasting 15 seconds each)

Press `Ctrl+C` to stop following the logs.

---

## Step 9 — (Optional) Enable Chaos Mode

To spike checkout errors to ~50%, edit your `.env` file:

```env
CHAOS_MODE=true
```

Then restart the checkout service to pick up the change:

```bash
docker compose up -d checkout-service
```

Watch the error rate increase in Grafana or Prometheus.

To disable, set `CHAOS_MODE=false` and restart again.

---

## Step 10 — View Logs in Grafana (via Loki)

1. Open Grafana at `http://localhost:3000`
2. Go to **Explore** (compass icon on the left sidebar)
3. Select **Loki** as the data source
4. Use a query like:
   ```
   {container_name="checkout-service"}
   ```
5. Click **Run Query** to see live logs from the checkout service

---

## Step 11 — View Alerts in Prometheus

1. Open Prometheus at `http://localhost:9090`
2. Click **Alerts** in the top navigation bar
3. View the configured alert rules and their current state (inactive / pending / firing)

---

## Step 12 — Stop All Services

When you're done, shut everything down:

```bash
docker compose down
```

To also **remove persistent data** (metrics history, logs, Grafana dashboards):

```bash
docker compose down -v
```

> [!CAUTION]
> Using `-v` will delete all stored Prometheus metrics, Loki logs, and Grafana data. Only use this if you want a completely fresh start.

---

## Quick Reference

| Action | Command |
|--------|---------|
| Start all services | `docker compose up -d --build` |
| Stop all services | `docker compose down` |
| Stop and wipe data | `docker compose down -v` |
| View logs for a service | `docker compose logs -f <service-name>` |
| Restart a single service | `docker compose up -d <service-name>` |
| Check container status | `docker compose ps` |
| Rebuild a single service | `docker compose build <service-name>` |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **Port already in use** | Another process is using the port. Stop it or change the port mapping in `docker-compose.yaml`. |
| **Container keeps restarting** | Check logs with `docker compose logs <service>`. Common cause: misconfigured `.env` file. |
| **Grafana shows "No Data"** | Wait 1–2 minutes for Prometheus to scrape metrics. Verify Prometheus is running at `http://localhost:9090`. |
| **Docker build fails** | Ensure Docker Desktop is running and you have internet access for base image pulls. |
| **Promtail not reading logs** | On Windows, Docker Desktop must have access to the Docker socket. Check Docker Desktop settings. |
