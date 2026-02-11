import requests
import json
import time
import sys

API_URL = "http://localhost:8080"

def verify():
    print("🔍 Starting Zero-Touch Configuration Verification...")
    
    # 0. Login
    try:
        login_data = {"username": "admin@example.com", "password": "admin"}
        # Auth router has prefix /auth
        res = requests.post(f"{API_URL}/auth/token", data=login_data)
        if res.status_code != 200:
             # Try registration if login fails (first run)
             print("⚠️ Login failed, trying to register admin...")
             reg_data = {"email": "admin@example.com", "password": "admin", "full_name": "Admin", "org_name": "SRE Org"}
             requests.post(f"{API_URL}/auth/register", json=reg_data)
             res = requests.post(f"{API_URL}/auth/token", data=login_data)
        
        res.raise_for_status()
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("🔑 Authenticated successfully.")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return

    # 1. Get Clusters
    try:
        res = requests.get(f"{API_URL}/api/v1/clusters", headers=headers)
        res.raise_for_status()
        clusters = res.json()
        print(f"✅ Found {len(clusters)} clusters.")
    except Exception as e:
        print(f"❌ Failed to list clusters: {e}")
        return

    if not clusters:
        # Create a cluster if none exist
        print("⚠️ No clusters found. Creating one...")
        try:
             res = requests.post(f"{API_URL}/api/v1/clusters", json={"name": "Test Cluster"}, headers=headers)
             res.raise_for_status()
             cluster_id = res.json()["id"]
             print(f"✅ Created Test Cluster: {cluster_id}")
        except Exception as e:
             print(f"❌ Failed to create cluster: {e}")
             return
    else:
        cluster_id = clusters[0]['id']

    print(f"🎯 Targeting Cluster ID: {cluster_id}")

    # 2. Trigger Job
    dummy_kubeconfig = """
apiVersion: v1
clusters:
- cluster:
    server: https://1.2.3.4
  name: dummy-cluster
contexts:
- context:
    cluster: dummy-cluster
    user: dummy-user
  name: dummy-context
current-context: dummy-context
kind: Config
preferences: {}
users: []
"""
    
    payload = {
        "job_type": "configure_cluster",
        "payload": json.dumps({
            "kubeconfig": dummy_kubeconfig
        })
    }
    
    try:
        res = requests.post(f"{API_URL}/api/v1/clusters/{cluster_id}/jobs/trigger", json=payload, headers=headers)
        res.raise_for_status()
        job = res.json()
        print(f"✅ Job Triggered Successfully! Job ID: {job['id']}")
        print(f"   Status: {job['status']}")
    except Exception as e:
        print(f"❌ Failed to trigger job: {e}")
        if hasattr(e, 'response') and e.response:
             print(f"   Response: {e.response.text}")

if __name__ == "__main__":
    verify()
