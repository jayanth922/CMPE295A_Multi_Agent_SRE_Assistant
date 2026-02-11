#!/usr/bin/env python3
"""
Seed Notion with Standard SRE Runbooks

This script populates the configured Notion database with a set of "Golden"
SRE runbooks. It is idempotent - it checks if a runbook with the same title
already exists before creating it.

Usage:
    export NOTION_API_KEY="your_key"
    export NOTION_DATABASE_ID="your_db_id"
    python3 scripts/seed_runbooks.py
"""

import os
import sys
import time
from typing import List, Dict, Any

try:
    from notion_client import Client
    from dotenv import load_dotenv
except ImportError:
    print("❌ Dependencies not found. Install them: pip install notion-client python-dotenv")
    sys.exit(1)

# Load env file
load_dotenv()


# --- Configuration ---
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID") or os.getenv("NOTION_RUNBOOK_DATABASE_ID")

if not NOTION_API_KEY:
    print("❌ Error: NOTION_API_KEY must be set.")
    sys.exit(1)

if not NOTION_DATABASE_ID:
    print("❌ Error: NOTION_DATABASE_ID or NOTION_RUNBOOK_DATABASE_ID must be set.")
    sys.exit(1)

client = Client(auth=NOTION_API_KEY)

# --- Runbook Content ---

RUNBOOKS = [
    {
        "title": "SRE-001: Kubernetes Pod CrashLoopBackOff",
        "tags": ["kubernetes", "critical", "incident"],
        "content_blocks": [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"type": "text", "text": {"content": "SRE-001: Pod CrashLoopBackOff Runbook"}}]}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": "🚨 Symptoms & Triggers"}}]}
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": "Alert: `KubePodCrashLooping` firing."}}]}
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": "Pod status is `CrashLoopBackOff` or `Error`."}}]}
            },
             {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": "Service availability degradation (5xx errors)."}}]}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": "🛑 Immediate Mitigation (Stop the Bleeding)"}}]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "If this is causing strict unavailability, check for a recent deployment and ROLLBACK immediately."}}]}
            },
            {
                "object": "block",
                "type": "code",
                "code": {"language": "bash", "rich_text": [{"type": "text", "text": {"content": "kubectl rollout undo deployment <deployment_name> -n <namespace>"}}]}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": "🕵️‍♂️ Investigation Steps"}}]}
            },
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": "1. Inspect Exit Code"}}]}
            },
            {
                "object": "block",
                "type": "code",
                "code": {"language": "bash", "rich_text": [{"type": "text", "text": {"content": "kubectl get pod <pod_name> -n <namespace> -o jsonpath='{.status.containerStatuses[0].state.terminated}'"}}]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "• Exit Code 137: OOMKilled (Out of Memory). Increase limits.\n• Exit Code 1/255: App Error. Check logs."}}]}
            },
             {
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": "2. Analyze Previous Logs"}}]}
            },
            {
                "object": "block",
                "type": "code",
                "code": {"language": "bash", "rich_text": [{"type": "text", "text": {"content": "kubectl logs <pod_name> -n <namespace> --previous --tail=100"}}]}
            },
             {
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": "3. Check Events"}}]}
            },
             {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Look for LivenessProbe failures or volume mounting issues."}}]}
            },
            {
                "object": "block",
                "type": "code",
                "code": {"language": "bash", "rich_text": [{"type": "text", "text": {"content": "kubectl describe pod <pod_name> -n <namespace>"}}]}
            }
        ]
    },
    {
        "title": "SRE-002: High API Latency (SLO Breach)",
        "tags": ["performance", "latency", "critical"],
        "content_blocks": [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"type": "text", "text": {"content": "SRE-002: High API Latency Runbook"}}]}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": "🚨 Symptoms"}}]}
            },
             {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": "p99 latency > 500ms for > 5 minutes."}}]}
            },
             {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": "Load Balancer 504 Gateway Timeouts."}}]}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": "🕵️‍♂️ Root Cause Analysis"}}]}
            },
             {
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": "Step 1: Isolate the bottleneck"}}]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Check Golden Signals to identify if it's CPU Saturation or Dependency Latency."}}]}
            },
             {
                "object": "block",
                "type": "code",
                "code": {"language": "plain text", "rich_text": [{"type": "text", "text": {"content": "# CPU Throttling Query\nsum(rate(container_cpu_cfs_throttled_seconds_total{namespace=\"default\"}[2m])) by (pod)"}}]}
            },
             {
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": "Step 2: Check Database Performance"}}]}
            },
             {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "High application latency often points to slow database queries."}}]}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": "✅ Mitigation Steps"}}]}
            },
             {
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": [{"type": "text", "text": {"content": "Scale Up: If CPU saturated, increase replicas."}}]}
            },
            {
                "object": "block",
                "type": "code",
                "code": {"language": "bash", "rich_text": [{"type": "text", "text": {"content": "kubectl scale deployment <name> --replicas=<current+2>"}}]}
            },
             {
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": [{"type": "text", "text": {"content": "Enable Caching: Verify Redis cache hit rates."}}]}
            }
        ]
    },
    {
        "title": "SRE-003: Node Not Ready (Infrastructure Failure)",
        "tags": ["infrastructure", "node", "hardware"],
        "content_blocks": [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"type": "text", "text": {"content": "SRE-003: Node Not Ready Runbook"}}]}
            },
             {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": "🚨 Impact"}}]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Capacity reduction. Pods on this node may be terminated or stuck in `Terminating`."}}]}
            },
             {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": "🕵️‍♂️ Diagnostics"}}]}
            },
             {
                "object": "block",
                "type": "code",
                "code": {"language": "bash", "rich_text": [{"type": "text", "text": {"content": "kubectl describe node <node_name>"}}]}
            },
             {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Key conditions to look for:\n• MemoryPressure\n• DiskPressure (Logs filling up?)\n• PIDPressure (Fork bomb?)\n• NetworkUnavailable"}}]}
            },
             {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": "✅ Recovery"}}]}
            },
             {
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": [{"type": "text", "text": {"content": "Cordon the node to prevent new pods."}}]}
            },
             {
                "object": "block",
                "type": "code",
                "code": {"language": "bash", "rich_text": [{"type": "text", "text": {"content": "kubectl cordon <node_name>"}}]}
            },
             {
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": [{"type": "text", "text": {"content": "Drain the node safely."}}]}
            },
             {
                "object": "block",
                "type": "code",
                "code": {"language": "bash", "rich_text": [{"type": "text", "text": {"content": "kubectl drain <node_name> --ignore-daemonsets --delete-emptydir-data"}}]}
            },
             {
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": [{"type": "text", "text": {"content": "Restart Kubelet or Recycle Node."}}]}
            }
        ]
    },
    {
        "title": "SRE-004: Postgres Connection Failure",
         "tags": ["database", "critical", "outage"],
         "content_blocks": [
             {
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"type": "text", "text": {"content": "SRE-004: Postgres Connection Refused"}}]}
            },
              {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": "🚨 Symptoms"}}]}
            },
             {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Logs show `FATAL: remaining connection slots are reserved for non-replication superuser connections` or `Connection refused`."}}]}
            },
             {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": "🕵️‍♂️ Investigation"}}]}
            },
             {
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": "1. Check Connection Count"}}]}
            },
             {
                "object": "block",
                "type": "code",
                "code": {"language": "sql", "rich_text": [{"type": "text", "text": {"content": "SELECT count(*) FROM pg_stat_activity;"}}]}
            },
             {
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": "2. Identify Leaking Clients"}}]}
            },
             {
                "object": "block",
                "type": "code",
                "code": {"language": "sql", "rich_text": [{"type": "text", "text": {"content": "SELECT application_name, count(*) \nFROM pg_stat_activity \nGROUP BY 1 ORDER BY 2 DESC;"}}]}
            },
             {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": "✅ Mitigation"}}]}
            },
             {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Terminate idle connections to free up slots."}}]}
            },
             {
                "object": "block",
                "type": "code",
                "code": {"language": "sql", "rich_text": [{"type": "text", "text": {"content": "SELECT pg_terminate_backend(pid) \nFROM pg_stat_activity \nWHERE state = 'idle' \nAND state_change < current_timestamp - INTERVAL '5 minutes';"}}]}
            }
         ]
    },
    {
        "title": "SRE-005: Redis High Memory / Eviction",
        "tags": ["redis", "cache", "performance"],
        "content_blocks": [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"type": "text", "text": {"content": "SRE-005: Redis OOM & Eviction"}}]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Redis is nearing maxmemory or evicting keys, causing cache misses and latency."}}]}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": "🕵️‍♂️ Investigation"}}]}
            },
             {
                "object": "block",
                "type": "code",
                "code": {"language": "plain text", "rich_text": [{"type": "text", "text": {"content": "redis-cli INFO memory\n# Look for used_memory_human vs maxmemory_human"}}]}
            },
             {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Identify large keys:"}}]}
            },
             {
                "object": "block",
                "type": "code",
                "code": {"language": "bash", "rich_text": [{"type": "text", "text": {"content": "redis-cli --bigkeys"}}]}
            },
             {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": "✅ Mitigation"}}]}
            },
             {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "1. Scale up Redis memory (requires restart or config set if safe).\n2. Delete volatile keys manually if urgent."}}]}
            },
             {
                "object": "block",
                "type": "code",
                "code": {"language": "plain text", "rich_text": [{"type": "text", "text": {"content": "CONFIG SET maxmemory 2gb"}}]}
            }
        ]
    },
    {
        "title": "SRE-006: Disk Usage / PVC Full",
        "tags": ["infrastructure", "storage", "critical"],
        "content_blocks": [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"type": "text", "text": {"content": "SRE-006: Persistent Volume Full"}}]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "A PersistentVolumeClaim is >85% full. Risk of data corruption or DB crash."}}]}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": "🚨 Immediate Action"}}]}
            },
             {
                "object": "block",
                "type": "code",
                "code": {"language": "bash", "rich_text": [{"type": "text", "text": {"content": "kubectl get pvc -n <namespace>"}}]}
            },
             {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Expand the volume (if StorageClass supports it)."}}]}
            },
             {
                "object": "block",
                "type": "code",
                "code": {"language": "bash", "rich_text": [{"type": "text", "text": {"content": "kubectl patch pvc <pvc_name> -p '{\"spec\":{\"resources\":{\"requests\":{\"storage\":\"100Gi\"}}}}'"}}]}
            },
             {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Note: Expansion typically only works online for some storage providers. A pod restart may be needed."}}]}
            }
        ]
    },
    {
        "title": "SRE-007: HPA Max Replicas Reached",
        "tags": ["scaling", "capacity", "warning"],
        "content_blocks": [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"type": "text", "text": {"content": "SRE-007: HPA Max Replicas Limit"}}]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "HorizontalPodAutoscaler has reached `maxReplicas`. It can no longer scale to meet demand."}}]}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": "🕵️‍♂️ Investigation"}}]}
            },
             {
                "object": "block",
                "type": "code",
                "code": {"language": "bash", "rich_text": [{"type": "text", "text": {"content": "kubectl get hpa -n <namespace>"}}]}
            },
             {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Is the load legitimate? Check ingress traffic."}}]}
            },
             {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": "✅ Mitigation"}}]}
            },
             {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Increase the limit if cluster capacity allows."}}]}
            },
             {
                "object": "block",
                "type": "code",
                "code": {"language": "bash", "rich_text": [{"type": "text", "text": {"content": "kubectl patch hpa <hpa_name> -p '{\"spec\":{\"maxReplicas\": 50}}'"}}]}
            }
        ]
    },
    {
        "title": "SRE-008: Deployment Rollout Stuck",
        "tags": ["deployment", "ci/cd", "stuck"],
        "content_blocks": [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"type": "text", "text": {"content": "SRE-008: Deployment Rollout Stuck"}}]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "New pods are not becoming ready, blocking the rollout."}}]}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": "🕵️‍♂️ Diagnostics"}}]}
            },
             {
                "object": "block",
                "type": "code",
                "code": {"language": "bash", "rich_text": [{"type": "text", "text": {"content": "kubectl rollout status deployment <name>\nkubectl get rs # Look for the new ReplicaSet"}}]}
            },
             {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Check limits/quotas. Are you out of CPU/Memory in the namespace?"}}]}
            },
             {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": "✅ Resolution"}}]}
            },
             {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "1. Undo the rollout to restore service."}}]}
            },
             {
                "object": "block",
                "type": "code",
                "code": {"language": "bash", "rich_text": [{"type": "text", "text": {"content": "kubectl rollout undo deployment <name>"}}]}
            }
        ]
    },
    {
        "title": "SRE-009: Ingress 502/503 Errors",
        "tags": ["network", "ingress", "outage"],
        "content_blocks": [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"type": "text", "text": {"content": "SRE-009: Ingress 5xx Errors"}}]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Load Balancer is returning 502 Bad Gateway or 503 Service Unavailable."}}]}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": "🕵️‍♂️ Troubleshooting"}}]}
            },
             {
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": "Step 1: Check Endpoints"}}]}
            },
             {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Does the service have valid endpoints? If empty, no pods match the selector."}}]}
            },
             {
                "object": "block",
                "type": "code",
                "code": {"language": "bash", "rich_text": [{"type": "text", "text": {"content": "kubectl get endpoints <service_name>"}}]}
            },
             {
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": "Step 2: Check Backend Health"}}]}
            },
             {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Can you direct-connect to the pod from inside the cluster?"}}]}
            },
             {
                "object": "block",
                "type": "code",
                "code": {"language": "bash", "rich_text": [{"type": "text", "text": {"content": "kubectl port-forward <pod_name> 8080:8080\ncurl localhost:8080/health"}}]}
            }
        ]
    }
]

# --- Functions ---

def get_or_create_database():
    """
    Verify access to the Notion database.
    If the ID points to a Page, create a new Database inside it.
    Returns the final Database ID to use.
    """
    try:
        # Try retrieving as a Database
        client.databases.retrieve(database_id=NOTION_DATABASE_ID)
        print("✅ Target is a valid Database.")
        return NOTION_DATABASE_ID
    except Exception:
        pass # Not a database, keep checking

    try:
        # Try retrieving as a Page
        page = client.pages.retrieve(page_id=NOTION_DATABASE_ID)
        print(f"⚠️  Target {NOTION_DATABASE_ID} is a PAGE, not a Database.")
        print("🚀 Creating a new 'SRE Runbooks' database inside this page...")
        
        # Create a new Database child
        new_db = client.databases.create(
            parent={"type": "page_id", "page_id": NOTION_DATABASE_ID},
            title=[{"type": "text", "text": {"content": "SRE Runbooks"}}],
            properties={
                "Title": {"title": {}},
                "Tags": {"multi_select": {}}
            }
        )
        new_id = new_db["id"]
        print(f"✅ Created new Database: {new_id}")
        print(f"📝 PLEASE UPDATE YOUR .env FILE:\nNOTION_RUNBOOK_DATABASE_ID={new_id}")
        return new_id
    except Exception as e:
        print(f"❌ Failed to access Page or Database: {e}")
        print(f"👉 TIP: Make sure permissions are granted.")
        sys.exit(1)

def runbook_exists(db_id: str, title: str) -> bool:
    """Check if a runbook with the given title already exists."""
    # Check "Title" property
    try:
        response = client.databases.query(
            database_id=db_id,
            filter={
                "property": "Title",
                "title": {
                    "equals": title
                }
            }
        )
        if len(response.get("results", [])) > 0:
            return True
    except Exception:
        pass

    # Check "Name" property
    try:
         response = client.databases.query(
            database_id=db_id,
            filter={
                "property": "Name",
                "title": {
                    "equals": title
                }
            }
        )
         if len(response.get("results", [])) > 0:
            return True
    except Exception:
         pass
    
    return False

def create_runbook(db_id: str, runbook: Dict[str, Any]):
    """Create a new runbook page in the database."""
    title = runbook["title"]
    blocks = runbook["content_blocks"]
    tags = runbook["tags"]
    
    # Fix unsupported languages
    for block in blocks:
        if block.get("type") == "code":
            lang = block["code"].get("language")
            if lang in ["promql", "bash-script"]:
                block["code"]["language"] = "plain text"
    
    print(f"Creating runbook: {title}...")
    
    # Construct properties payload
    properties = {
        "Title": {
            "title": [
                {"text": {"content": title}}
            ]
        },
        "Tags": {
            "multi_select": [{"name": tag} for tag in tags]
        }
    }

    try:
        client.pages.create(
            parent={"database_id": db_id},
            properties=properties,
            children=blocks
        )
        print(f"✅ Created: {title}")
    except Exception as e:
        error_msg = str(e)
        if "Tags is not a property" in error_msg or "Could not find property with name or id: Tags" in error_msg:
             print(f"⚠️  'Tags' property missing. Retrying without tags...")
             del properties["Tags"]
             try:
                 client.pages.create(
                    parent={"database_id": db_id},
                    properties=properties,
                    children=blocks
                )
                 print(f"✅ Created: {title} (without tags)")
                 return
             except Exception as e2:
                 print(f"❌ Retry failed: {e2}")

        # Fallback to "Name" property
        try:
             # Try renaming Title to Name
             if "Title" in properties:
                 properties["Name"] = properties.pop("Title")
             
             client.pages.create(
                parent={"database_id": db_id},
                properties=properties,
                children=blocks
            )
             print(f"✅ Created: {title} (using 'Name' property)")
        except Exception as e3:
            print(f"❌ Failed to create {title}: {e3}")

def main():
    print(f"🚀 Resolution for Target ID: {NOTION_DATABASE_ID}")
    
    final_db_id = get_or_create_database()
    
    print(f"📂 Using Database ID: {final_db_id}")

    for runbook in RUNBOOKS:
        title = runbook["title"]
        if runbook_exists(final_db_id, title):
            print(f"⏭️  Skipping existing runbook: {title}")
        else:
            create_runbook(final_db_id, runbook)
            time.sleep(1) 

    print("✨ Seeding Complete!")


if __name__ == "__main__":
    main()
