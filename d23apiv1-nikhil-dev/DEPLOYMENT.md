# D23Bot Deployment Guide

This guide covers deploying D23Bot to various environments.

## Quick Start

### Local Development

```bash
# 1. Copy and configure environment
cp .env.example .env
# Edit .env with your API keys

# 2. Start with Docker Compose
docker-compose up -d

# Or without Docker
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 9002 --reload
```

### Production Deployment

```bash
# Using Docker Compose
docker-compose -f docker-compose.yml up -d

# Using startup script
./scripts/startup.sh prod
```

---

## Prerequisites

- **Python:** 3.12+ (for local development)
- **Docker:** 24.0+ and Docker Compose 2.0+
- **PostgreSQL:** 16+ (included in Docker setup)
- **Redis:** 7+ (optional, included in Docker setup)

---

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

**Required Variables:**

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key for GPT |
| `WHATSAPP_ACCESS_TOKEN` | WhatsApp Cloud API token |
| `WHATSAPP_PHONE_NUMBER_ID` | WhatsApp phone number ID |
| `WHATSAPP_VERIFY_TOKEN` | Webhook verification token |

**Database Variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | `localhost` | Database host |
| `POSTGRES_PORT` | `5432` | Database port |
| `POSTGRES_USER` | `postgres` | Database user |
| `POSTGRES_PASSWORD` | `postgres` | Database password |
| `POSTGRES_DB` | `d23bot` | Database name |

---

## Docker Deployment

### Build the Image

```bash
# Build production image
docker build -t d23bot:latest .

# Build with specific target
docker build --target production -t d23bot:prod .
docker build --target development -t d23bot:dev .
```

### Run with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f bot

# Stop services
docker-compose down

# With Chainlit UI (development)
docker-compose --profile dev up -d
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| `bot` | 9002 | Main bot API |
| `postgres` | 5432 | PostgreSQL database |
| `redis` | 6379 | Redis cache |
| `chainlit` | 8000 | Web UI (dev profile) |

---

## Database Setup

### Automatic Initialization

The database is automatically initialized when the PostgreSQL container starts using `scripts/init-db.sql`.

### Manual Setup

```bash
# Connect to PostgreSQL
psql -h localhost -U postgres -d d23bot

# Run initialization script
\i scripts/init-db.sql
```

### Tables Created

- `user_profiles` - User birth details and preferences
- `conversation_context` - Multi-turn conversation state
- `reminders` - Scheduled reminders
- `query_history` - Analytics data
- `rate_limits` - Rate limiting data

---

## Health Checks

### Check Service Health

```bash
# Using script
./scripts/health-check.sh

# Or manually
curl http://localhost:9002/
```

### Docker Health Status

```bash
docker-compose ps
docker inspect d23bot --format='{{.State.Health.Status}}'
```

---

## CI/CD Pipeline

### GitHub Actions

The repository includes two workflows:

1. **CI Workflow** (`.github/workflows/ci.yml`)
   - Runs on: Pull requests and pushes
   - Jobs: Lint, Type Check, Test, Security Scan, Build

2. **Deploy Workflow** (`.github/workflows/deploy.yml`)
   - Runs on: Push to main, Manual trigger
   - Jobs: Build & Push, Deploy to Staging, Deploy to Production

### Required Secrets

Configure these in GitHub repository settings:

```
STAGING_HOST       - Staging server hostname
STAGING_USER       - SSH username
STAGING_SSH_KEY    - SSH private key

PRODUCTION_HOST    - Production server hostname
PRODUCTION_USER    - SSH username
PRODUCTION_SSH_KEY - SSH private key
```

---

## Monitoring

### Logs

```bash
# Docker logs
docker-compose logs -f bot

# Application logs
tail -f logs/app.log
```

### LangSmith Tracing

Enable tracing by setting:

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-key
LANGSMITH_PROJECT=d23bot
```

View traces at: https://smith.langchain.com/

---

## Scaling

### Horizontal Scaling

```bash
# Scale bot service
docker-compose up -d --scale bot=3

# Use with load balancer (nginx, traefik)
```

### Resource Limits

Add to docker-compose.yml:

```yaml
services:
  bot:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

---

## Backup & Recovery

### Database Backup

```bash
# Backup
docker exec d23bot-postgres pg_dump -U postgres d23bot > backup.sql

# Restore
docker exec -i d23bot-postgres psql -U postgres d23bot < backup.sql
```

### ChromaDB Backup

```bash
# Backup vector store
tar -czvf chroma_backup.tar.gz db/chroma/

# Restore
tar -xzvf chroma_backup.tar.gz
```

---

## Troubleshooting

### Common Issues

**Bot not responding:**
```bash
# Check logs
docker-compose logs bot

# Check health
./scripts/health-check.sh

# Restart service
docker-compose restart bot
```

**Database connection failed:**
```bash
# Check PostgreSQL status
docker-compose logs postgres

# Test connection
docker exec d23bot-postgres pg_isready
```

**WhatsApp webhook not working:**
1. Verify `WHATSAPP_VERIFY_TOKEN` matches Facebook settings
2. Check webhook URL is accessible (use ngrok for local dev)
3. Verify SSL certificate is valid

### Debug Mode

```bash
# Run with debug logging
LOG_LEVEL=DEBUG docker-compose up bot
```

---

## Security Checklist

- [ ] Change default database passwords
- [ ] Use secrets management (AWS Secrets Manager, Vault)
- [ ] Enable HTTPS in production
- [ ] Configure firewall rules
- [ ] Set up rate limiting
- [ ] Regular security updates
- [ ] Rotate API keys periodically

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        Load Balancer                         │
│                      (nginx/traefik)                         │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│                     D23Bot API (x N)                         │
│                   FastAPI + LangGraph                        │
│                      Port: 9002                              │
└────────┬─────────────────┬─────────────────┬─────────────────┘
         │                 │                 │
         ▼                 ▼                 ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  PostgreSQL │    │    Redis    │    │  ChromaDB   │
│   (state)   │    │   (cache)   │    │  (vectors)  │
└─────────────┘    └─────────────┘    └─────────────┘
```

---

## Support

- **Issues:** https://github.com/your-org/d23bot/issues
- **Documentation:** See readme.md
- **API Reference:** https://api.d23.ai/docs
