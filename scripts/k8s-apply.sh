#!/usr/bin/env bash
set -euo pipefail

echo "Applying Kubernetes manifests for kind cluster..."

# Apply kustomization (includes namespace)
kubectl apply -k infrastructure/k8s/base

echo "Waiting for MCP servers to be ready..."
# Wait for real MCP servers (deployments may vary based on what's deployed)
kubectl -n sre rollout status deploy/mcp-k8s-real --timeout=120s || echo "⚠️  mcp-k8s-real not found, skipping..."
kubectl -n sre rollout status deploy/mcp-loki-real --timeout=120s || echo "⚠️  mcp-loki-real not found, skipping..."
kubectl -n sre rollout status deploy/mcp-prometheus-real --timeout=120s || echo "⚠️  mcp-prometheus-real not found, skipping..."
kubectl -n sre rollout status deploy/mcp-notion-real --timeout=120s || echo "⚠️  mcp-notion-real not found, skipping..."
kubectl -n sre rollout status deploy/mcp-github-real --timeout=120s || echo "⚠️  mcp-github-real not found, skipping..."
kubectl -n sre rollout status deploy/mcp-memory-real --timeout=120s || echo "⚠️  mcp-memory-real not found, skipping..."

echo "Waiting for SRE Agent to be ready..."
kubectl -n sre rollout status deploy/sre-agent --timeout=120s

echo "✅ All deployments are ready!"
echo ""
echo "To access the agent:"
echo "  kubectl -n sre port-forward svc/sre-agent 8080:8080"
echo "  curl http://localhost:8080/invocations -H 'content-type: application/json' -d '{\"input\":{\"prompt\":\"list pods\"}}'"
echo ""
echo "To view logs:"
echo "  kubectl -n sre logs -f deploy/sre-agent"
echo "  kubectl -n sre logs -f deploy/mcp-k8s-real"
