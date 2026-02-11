#!/usr/bin/env bash
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting CMPE295A Multi-Agent SRE Assistant...${NC}"

# Check for .env file
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ .env created. You can edit it later to add API keys (Groq, Notion, GitHub).${NC}"
    echo -e "${YELLOW}👉 Defaulting to OLLAMA (Local LLM) - No API Key required for basic smoke test.${NC}"
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker and Docker Compose.${NC}"
    exit 1
fi

echo -e "${GREEN}📦 Building and observing services...${NC}"
cd infrastructure
docker compose up -d --build

echo -e "${GREEN}⏳ Waiting for services to verify health...${NC}"
sleep 5
docker compose ps

echo -e ""
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e ""
echo -e "   🖥️  ${YELLOW}Dashboard:${NC}    http://localhost:3000"
echo -e "   🧠  ${YELLOW}SRE Agent:${NC}    http://localhost:8080/docs"
echo -e "   📊  ${YELLOW}Prometheus:${NC}   http://localhost:9090 (if mapped)"
echo -e ""
echo -e "   👉 To stop: ./stop.sh"
echo -e "   👉 To view logs: docker compose -f infrastructure/docker-compose.yaml logs -f sre-agent"
echo -e ""
