#!/usr/bin/env bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 Starting SRE SaaS Platform...${NC}"

# Check for .env file at project root
if [ ! -f ../.env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from .env.example...${NC}"
    cp ../.env.example ../.env
    echo -e "${GREEN}✅ .env created. Edit it to set SECRET_KEY and other values.${NC}"
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed.${NC}"
    exit 1
fi

echo -e "${GREEN}📦 Building SaaS Platform...${NC}"
docker compose -f docker-compose.yaml up -d --build

echo -e "${GREEN}⏳ Waiting for health checks...${NC}"
sleep 5
docker compose -f docker-compose.yaml ps

echo -e ""
echo -e "${GREEN}✅ SaaS Platform Running!${NC}"
echo -e ""
echo -e "   🖥️  ${YELLOW}Dashboard:${NC}    http://localhost:3000"
echo -e "   🧠  ${YELLOW}API Server:${NC}   http://localhost:8080/docs"
echo -e ""
echo -e "   👉 To connect a customer cluster: see customer/ directory"
echo -e "   👉 To stop: ./stop.sh"
echo -e "   👉 Logs: docker compose -f platform/docker-compose.yaml logs -f sre-agent-api"
echo -e ""
