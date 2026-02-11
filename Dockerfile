# Use official Python image
FROM python:3.12-slim-bookworm

WORKDIR /app

# Install uv and wget (for Docker healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends wget \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

# Copy uv files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy SRE agent module, MCP servers, and UI
COPY sre_agent/ ./sre_agent/
COPY mcp_servers/ ./mcp_servers/

# Set environment variables
# Note: Set DEBUG=true to enable debug logging and traces
ENV PYTHONPATH="/app" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Expose ports
EXPOSE 8080 8501

# Run application with OpenTelemetry instrumentation
CMD ["uv", "run", "uvicorn", "sre_agent.agent_runtime:app", "--host", "0.0.0.0", "--port", "8080"] 