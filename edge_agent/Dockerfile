# =============================================================================
# Customer Edge Relay — Lightweight bridge to SaaS Platform
# =============================================================================
# Polls the SaaS platform for tool_call jobs, executes them against local
# MCP servers, and returns results. NO AI/LLM runs in this container.
#
# Build context: customer/ (this directory)
#   docker build -f Dockerfile -t sre-edge-relay .
# =============================================================================

FROM python:3.12-slim-bookworm

WORKDIR /app

# Install only lightweight dependencies (no ML, no LLM, no heavy libs)
RUN pip install --no-cache-dir \
    httpx>=0.27.0 \
    langchain-mcp-adapters>=0.1.9 \
    langchain-core>=0.3.72 \
    pydantic>=2.0.0

# Copy only the edge relay script
COPY edge_relay.py ./

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

CMD ["python", "edge_relay.py"]
