#!/bin/bash
# =============================================================================
# D23Bot Startup Script
# =============================================================================
# Usage: ./scripts/startup.sh [dev|staging|prod]
# =============================================================================

set -e

ENVIRONMENT=${1:-dev}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "D23Bot Startup Script"
echo "Environment: $ENVIRONMENT"
echo "Project Dir: $PROJECT_DIR"
echo "=========================================="

cd "$PROJECT_DIR"

# -----------------------------------------------------------------------------
# Pre-flight checks
# -----------------------------------------------------------------------------
echo "Running pre-flight checks..."

# Check for .env file
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found!"
    echo "Copy .env.example to .env and configure it."
    exit 1
fi

# Check for required environment variables
source .env
REQUIRED_VARS="OPENAI_API_KEY WHATSAPP_ACCESS_TOKEN WHATSAPP_PHONE_NUMBER_ID"
for var in $REQUIRED_VARS; do
    if [ -z "${!var}" ]; then
        echo "ERROR: Required environment variable $var is not set!"
        exit 1
    fi
done
echo "Environment variables: OK"

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
if [ "$PYTHON_VERSION" != "3.12" ] && [ "$PYTHON_VERSION" != "3.11" ]; then
    echo "WARNING: Python $PYTHON_VERSION detected. Recommended: 3.12"
fi
echo "Python version: $PYTHON_VERSION"

# -----------------------------------------------------------------------------
# Start based on environment
# -----------------------------------------------------------------------------
case $ENVIRONMENT in
    dev)
        echo "Starting development server..."

        # Check if Docker is running
        if command -v docker &> /dev/null && docker info &> /dev/null; then
            echo "Starting services with Docker Compose..."
            docker-compose up -d postgres redis
            sleep 5  # Wait for services
        else
            echo "Docker not available, using local services..."
        fi

        # Start with hot reload
        uvicorn main:app --host 0.0.0.0 --port ${BOT_PORT:-9002} --reload
        ;;

    staging)
        echo "Starting staging server..."
        docker-compose -f docker-compose.yml up -d
        docker-compose logs -f bot
        ;;

    prod)
        echo "Starting production server..."

        # Pull latest image
        docker-compose pull bot

        # Start with zero-downtime deployment
        docker-compose up -d --no-deps --scale bot=2 bot
        sleep 10
        docker-compose up -d --no-deps --scale bot=1 bot

        echo "Production deployment complete!"
        docker-compose ps
        ;;

    docker)
        echo "Starting all services with Docker Compose..."
        docker-compose up -d
        echo "Services started. Logs:"
        docker-compose logs -f
        ;;

    *)
        echo "Usage: $0 [dev|staging|prod|docker]"
        exit 1
        ;;
esac

echo "=========================================="
echo "Startup complete!"
echo "=========================================="
