#!/bin/bash
# =============================================================================
# D23Bot Health Check Script
# =============================================================================
# Usage: ./scripts/health-check.sh
# Returns: 0 if healthy, 1 if unhealthy
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Configuration
BOT_URL="${BOT_URL:-http://localhost:9002}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "D23Bot Health Check"
echo "=========================================="

HEALTHY=true

# -----------------------------------------------------------------------------
# Check Bot API
# -----------------------------------------------------------------------------
echo -n "Bot API ($BOT_URL)... "
if curl -sf "$BOT_URL/" > /dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
    HEALTHY=false
fi

# -----------------------------------------------------------------------------
# Check PostgreSQL
# -----------------------------------------------------------------------------
echo -n "PostgreSQL ($POSTGRES_HOST:$POSTGRES_PORT)... "
if command -v pg_isready &> /dev/null; then
    if pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${RED}FAILED${NC}"
        HEALTHY=false
    fi
elif command -v docker &> /dev/null; then
    if docker exec d23bot-postgres pg_isready > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${RED}FAILED${NC}"
        HEALTHY=false
    fi
else
    echo -e "${YELLOW}SKIP (no pg_isready)${NC}"
fi

# -----------------------------------------------------------------------------
# Check Redis
# -----------------------------------------------------------------------------
echo -n "Redis ($REDIS_HOST:$REDIS_PORT)... "
if command -v redis-cli &> /dev/null; then
    if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${YELLOW}UNAVAILABLE${NC}"
    fi
elif command -v docker &> /dev/null; then
    if docker exec d23bot-redis redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${YELLOW}UNAVAILABLE${NC}"
    fi
else
    echo -e "${YELLOW}SKIP (no redis-cli)${NC}"
fi

# -----------------------------------------------------------------------------
# Check External APIs (optional)
# -----------------------------------------------------------------------------
echo ""
echo "External Services:"

echo -n "OpenAI API... "
if [ -n "$OPENAI_API_KEY" ]; then
    # Don't actually call the API, just check key format
    if [[ "$OPENAI_API_KEY" == sk-* ]]; then
        echo -e "${GREEN}KEY CONFIGURED${NC}"
    else
        echo -e "${YELLOW}KEY FORMAT UNKNOWN${NC}"
    fi
else
    echo -e "${RED}NOT CONFIGURED${NC}"
fi

echo -n "WhatsApp API... "
if [ -n "$WHATSAPP_ACCESS_TOKEN" ] && [ -n "$WHATSAPP_PHONE_NUMBER_ID" ]; then
    echo -e "${GREEN}CONFIGURED${NC}"
else
    echo -e "${RED}NOT CONFIGURED${NC}"
fi

# -----------------------------------------------------------------------------
# Check Docker containers (if using Docker)
# -----------------------------------------------------------------------------
if command -v docker &> /dev/null && docker info &> /dev/null 2>&1; then
    echo ""
    echo "Docker Containers:"
    docker ps --filter "name=d23bot" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || true
fi

# -----------------------------------------------------------------------------
# Memory and disk usage
# -----------------------------------------------------------------------------
echo ""
echo "System Resources:"
echo -n "Memory: "
free -h 2>/dev/null | grep Mem | awk '{print $3 "/" $2 " used"}' || echo "N/A"

echo -n "Disk: "
df -h "$PROJECT_DIR" 2>/dev/null | tail -1 | awk '{print $3 "/" $2 " used (" $5 ")"}' || echo "N/A"

# -----------------------------------------------------------------------------
# Result
# -----------------------------------------------------------------------------
echo ""
echo "=========================================="
if $HEALTHY; then
    echo -e "${GREEN}Health Check: PASSED${NC}"
    exit 0
else
    echo -e "${RED}Health Check: FAILED${NC}"
    exit 1
fi
