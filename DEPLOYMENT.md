# ChangeRadar 1.0 — Production Deployment & Operations Guide

ChangeRadar 1.0 is an enterprise-grade Software Change Intelligence Platform designed for high-confidence change blast-radius analysis, GitHub Pull Request automation, and historical change pattern detection.

---

## 1. System Architecture

```
                                  Internet / GitHub Webhooks
                                              │
                                              ▼
                             ┌──────────────────────────────────┐
                             │    Nginx Reverse Proxy & UI      │
                             │   (Port 80/443, Gzip, CSP)       │
                             └───────────────┬──────────────────┘
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       │                                           │
                       ▼                                           ▼
          ┌──────────────────────────┐               ┌──────────────────────────┐
          │     Static UI Bundle     │               │    FastAPI Application   │
          │   (Vite + React SPA)     │               │   Engine v1.0.0 (:8000)  │
          └──────────────────────────┘               └─────────────┬────────────┘
                                                                   │
                                        ┌──────────────────────────┴────────────┐
                                        │                                       │
                                        ▼                                       ▼
                         ┌─────────────────────────────┐         ┌─────────────────────────────┐
                         │   PostgreSQL 16 Database    │         │  Persistent Storage Volume  │
                         │    (Dual-Dialect Schema)    │         │    (/app/storage/repos)     │
                         └─────────────────────────────┘         └─────────────────────────────┘
```

The system operates across three coordinated tiers:
1. **Frontend / Edge**: Multi-stage Nginx container serving compiled React assets with Gzip compression, HTML5 history routing, security headers (`DENY`, `nosniff`), and reverse-proxying API traffic to the backend.
2. **Application / Engine**: FastAPI application container running Python 3.13 as an unprivileged non-root user (`changeradar`, UID `10001`). Includes Git runtime, AST parser, call-graph engine, background job manager, and cryptographic secret management.
3. **Database**: PostgreSQL 16 container with persistent volumes, automatic Alembic migrations, and health checks.

---

## 2. Prerequisites & Resource Requirements

| Resource | Minimum | Recommended | Notes |
| :--- | :--- | :--- | :--- |
| **CPU** | 2 Cores | 4+ Cores | Required for concurrent AST parsing |
| **Memory (RAM)** | 4 GB | 8 GB | AST and call-graph traversals run in-memory |
| **Disk Storage** | 20 GB SSD | 100 GB SSD | PostgreSQL database + cached Git repositories |
| **Container Engine** | Docker 24.0+ | Docker 26.0+ | Compose v2 required |
| **Network** | Outbound HTTPS | Outbound HTTPS | Required for GitHub API and webhook verification |

---

## 3. Quickstart Production Deployment (Docker Compose)

### Step 1: Clone and Configure Environment

```bash
git clone https://github.com/your-org/changeradar.git
cd changeradar

# Copy environment template
cp .env.production.example .env
```

### Step 2: Generate Encryption Key and Secure Passwords

ChangeRadar requires a 32-byte Fernet symmetric key to encrypt user GitHub Personal Access Tokens and OAuth tokens:

```bash
# Generate Fernet encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Edit `.env` and set:
- `POSTGRES_PASSWORD`: A random 32+ character alphanumeric string.
- `ENCRYPTION_KEY`: The Fernet key generated above.
- `CORS_ORIGINS`: Your production domain (e.g., `https://changeradar.yourdomain.com`).
- `COOKIE_SECURE`: `true` (enforces HTTPS-only cookies).

### Step 3: Launch Containers

```bash
docker compose up -d --build
```

### Step 4: Verify Service Health

Check container health status:

```bash
docker compose ps
```

Verify backend health endpoints:

```bash
# Liveness probe
curl http://localhost:8000/health
# {"status":"healthy","service":"changeradar-api","version":"1.0.0","environment":"production","database":{"connected":true,"dialect":"postgresql","error":null}}

# Readiness probe
curl http://localhost:8000/ready
# {"status":"ready","database":"connected","timestamp":"2026-10-31T00:00:00Z"}
```

---

## 4. Environment Variables Reference

| Variable | Required | Default | Description |
| :--- | :---: | :---: | :--- |
| `ENVIRONMENT` | Yes | `production` | Runtime mode (`production` or `development`) |
| `DATABASE_URL` | Yes | — | PostgreSQL connection string (`postgresql+psycopg2://...`) |
| `ENCRYPTION_KEY` | Yes | — | Fernet key for token encryption |
| `CORS_ORIGINS` | Yes | `http://localhost` | Comma-separated allowed frontend origins |
| `COOKIE_SECURE` | Yes | `true` | Enforces `Secure` flag on session cookies |
| `GITHUB_CLIENT_ID` | Optional | `""` | GitHub OAuth / GitHub App client ID |
| `GITHUB_CLIENT_SECRET` | Optional | `""` | GitHub OAuth / GitHub App client secret |
| `GITHUB_WEBHOOK_SECRET` | Optional | `""` | Secret for HMAC-SHA256 signature verification |
| `REPO_STORAGE_DIR` | Yes | `/app/storage/repositories` | Base directory for cloned repositories |
| `BACKGROUND_WORKER_CONCURRENCY` | No | `4` | Concurrency limit for background analysis workers |
| `ANALYSIS_ENGINE_VERSION` | No | `1.0.0` | Stamp recorded on historical analyses |

---

## 5. Database Operations & Migrations

### Running Alembic Migrations

Migrations execute automatically upon container startup. To execute migrations manually:

```bash
docker compose exec backend alembic upgrade head
```

To inspect current database revision:

```bash
docker compose exec backend alembic current
```

### Database Backup & Restore

**Automated Backup**:
```bash
docker compose exec postgres pg_dump -U changeradar -d changeradar -F c -f /tmp/changeradar_backup_$(date +%Y%m%d_%H%M%S).dump
docker cp changeradar-postgres:/tmp/changeradar_backup_*.dump ./backups/
```

**Restore**:
```bash
docker cp ./backups/changeradar_backup.dump changeradar-postgres:/tmp/restore.dump
docker compose exec postgres pg_restore -U changeradar -d changeradar --clean --if-exists /tmp/restore.dump
```

---

## 6. GitHub Integration Setup

### Webhook Configuration
1. In your GitHub repository or organization, navigate to **Settings > Webhooks > Add webhook**.
2. **Payload URL**: `https://changeradar.yourdomain.com/api/v1/github/webhook`
3. **Content type**: `application/json`
4. **Secret**: Enter the exact value configured in `GITHUB_WEBHOOK_SECRET`.
5. **Which events would you like to trigger this webhook?**: Select **Pull requests**.
6. **Active**: Checked.

ChangeRadar automatically:
- Validates the `X-Hub-Signature-256` HMAC header.
- Deduplicates deliveries using `X-GitHub-Delivery`.
- Triggers impact analysis for `opened`, `synchronize`, and `reopened` actions.
- Updates or creates an idempotent summary comment on the Pull Request.

---

## 7. Kubernetes Probes Configuration

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 15
  periodSeconds: 20
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 2
```

---

## 8. Rollback Procedures

If an upgrade needs to be rolled back:
1. Roll back the Docker container image tag to the prior release.
2. Downgrade the database schema via Alembic:
   ```bash
   docker compose exec backend alembic downgrade -1
   ```
3. Restart backend service:
   ```bash
   docker compose restart backend
   ```
