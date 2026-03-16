#!/usr/bin/env bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🛑 Stopping SaaS Platform...${NC}"
docker compose -f docker-compose.yaml down
echo -e "${GREEN}✅ SaaS Platform stopped.${NC}"
