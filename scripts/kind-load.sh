#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="sre"

echo "Building SRE Agent image..."
docker build -t ghcr.io/jayanth922/sre-agent:local .

echo "Loading SRE Agent image into kind cluster..."
kind load docker-image ghcr.io/jayanth922/sre-agent:local --name ${CLUSTER_NAME}

echo "Building MCP server images..."
# Build and load each real MCP server
for server in k8s_real prometheus_real loki_real notion_real github_real memory_real; do
    if [ -d "mcp_servers/${server}" ]; then
        echo "Building ${server}..."
        docker build -t ghcr.io/jayanth922/mcp-${server}:local mcp_servers/${server}
        echo "Loading ${server} image into kind cluster..."
        kind load docker-image ghcr.io/jayanth922/mcp-${server}:local --name ${CLUSTER_NAME}
    fi
done

echo "✅ Images loaded successfully!"
echo "Next step: Run ./scripts/k8s-apply.sh to deploy"
