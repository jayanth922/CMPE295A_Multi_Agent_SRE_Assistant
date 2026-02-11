FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY server.py .

# Expose port (for SSE/HTTP transport)
EXPOSE 3000

# Run server with SSE transport for HTTP access
ENV MCP_TRANSPORT=sse
CMD ["python", "server.py"]
