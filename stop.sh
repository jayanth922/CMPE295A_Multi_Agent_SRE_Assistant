#!/usr/bin/env bash
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🛑 Stopping SRE Assistant Stack...${NC}"

cd infrastructure
docker compose down

echo -e "${GREEN}✅ All services stopped.${NC}"
