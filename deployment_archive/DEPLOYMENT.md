# CallSim AI Call Center - Production Deployment Guide

## 🚀 Quick Start with Docker

### Prerequisites
- Docker & Docker Compose installed
- OpenAI API key
- Domain name (for production)

### 1. Environment Setup

Copy the example environment file and configure:

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` and set:

```bash
# Generate secure keys
FLASK_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Set your OpenAI API key
OPENAI_API_KEY=sk-your-openai-api-key-here

# Configure allowed origins (your frontend URLs)
ALLOWED_ORIGINS=http://localhost,https://yourdomain.com

# Optional: Sentry for error tracking
SENTRY_DSN=your-sentry-dsn-here
```

### 2. Start Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### 3. Initialize Database

```bash
# Run database initialization
docker-compose exec backend python init_db.py
```

This creates:
- All database tables
- Default admin user (admin@callsim.com / Admin123!)
- ⚠️ **Change the default password immediately!**

### 4. Access the Application

- **Frontend**: http://localhost
- **API**: http://localhost/api
- **API Docs**: http://localhost/api/docs
- **Health Check**: http://localhost/api/health

### 5. Stop Services

```bash
docker-compose down

# To remove volumes (WARNING: deletes all data)
docker-compose down -v
```

---

## 📦 Manual Installation (Without Docker)

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### 1. Install PostgreSQL

**Windows:**
```powershell
# Download from: https://www.postgresql.org/download/windows/
# Or use chocolatey:
choco install postgresql

# Create database
psql -U postgres
CREATE DATABASE callsim;
CREATE USER callsim WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE callsim TO callsim;
\q
```

**Linux:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo -u postgres psql
CREATE DATABASE callsim;
CREATE USER callsim WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE callsim TO callsim;
\q
```

### 2. Install Redis

**Windows:**
```powershell
# Download from: https://github.com/microsoftarchive/redis/releases
# Or use WSL2 and install Linux version
```

**Linux:**
```bash
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### 3. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 5. Initialize Database

```bash
python init_db.py
```

### 6. Start Services

**Terminal 1 - Flask API:**
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 app_v2:app
```

**Terminal 2 - Celery Worker:**
```bash
celery -A celery_tasks worker --loglevel=info
```

**Terminal 3 - Celery Beat (periodic tasks):**
```bash
celery -A celery_tasks beat --loglevel=info
```

---

## 🌐 Production Deployment

### AWS Deployment

#### Option 1: Elastic Beanstalk (Easiest)

```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p docker callsim-app

# Create environment
eb create callsim-prod

# Deploy
eb deploy

# Set environment variables
eb setenv FLASK_SECRET_KEY=xxx JWT_SECRET_KEY=xxx OPENAI_API_KEY=xxx
```

#### Option 2: ECS (Recommended for Scale)

1. Build and push Docker image:
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

docker build -t callsim-backend ./backend
docker tag callsim-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/callsim-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/callsim-backend:latest
```

2. Create RDS PostgreSQL database
3. Create ElastiCache Redis cluster
4. Create ECS Task Definition
5. Create ECS Service
6. Set up Application Load Balancer
7. Configure CloudFront for frontend

### Azure Deployment

```bash
# Install Azure CLI
# https://docs.microsoft.com/en-us/cli/azure/install-azure-cli

# Login
az login

# Create resource group
az group create --name callsim-rg --location eastus

# Create container registry
az acr create --resource-group callsim-rg --name callsimacr --sku Basic

# Build and push
az acr build --registry callsimacr --image callsim-backend:latest ./backend

# Create database
az postgres flexible-server create --resource-group callsim-rg --name callsim-db --admin-user callsim --admin-password <password>

# Create Redis cache
az redis create --resource-group callsim-rg --name callsim-redis --location eastus --sku Basic --vm-size c0

# Deploy container
az container create --resource-group callsim-rg --name callsim-app --image callsimacr.azurecr.io/callsim-backend:latest --dns-name-label callsim --ports 5000
```

### Google Cloud Deployment

```bash
# Install gcloud CLI
# https://cloud.google.com/sdk/docs/install

# Login
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Build and push
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/callsim-backend ./backend

# Deploy to Cloud Run
gcloud run deploy callsim-backend \
  --image gcr.io/YOUR_PROJECT_ID/callsim-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars FLASK_ENV=production,OPENAI_API_KEY=xxx

# Create Cloud SQL PostgreSQL
gcloud sql instances create callsim-db --database-version=POSTGRES_15 --tier=db-f1-micro --region=us-central1

# Create Memorystore Redis
gcloud redis instances create callsim-redis --size=1 --region=us-central1
```

---

## 🔒 Security Checklist

### Before Going Live:

- [ ] Change all default passwords
- [ ] Generate new secret keys (never use defaults)
- [ ] Enable HTTPS/SSL certificates
- [ ] Set up firewall rules
- [ ] Configure CORS properly (restrict origins)
- [ ] Enable rate limiting
- [ ] Set up monitoring (Sentry, CloudWatch, etc.)
- [ ] Configure backup strategy
- [ ] Set up CDN for static assets
- [ ] Review and restrict API permissions
- [ ] Enable audit logging
- [ ] Set up security headers (already configured with Talisman)
- [ ] Configure database encryption at rest
- [ ] Set up VPC/network isolation
- [ ] Implement DDoS protection
- [ ] Regular security updates

---

## 📊 Monitoring & Maintenance

### Health Monitoring

```bash
# Check API health
curl http://localhost/api/health

# View application logs
docker-compose logs -f backend

# View database logs
docker-compose logs -f db

# View Redis logs
docker-compose logs -f redis
```

### Database Backups

```bash
# Backup PostgreSQL
docker-compose exec db pg_dump -U callsim callsim > backup_$(date +%Y%m%d).sql

# Restore
docker-compose exec -T db psql -U callsim callsim < backup_20260101.sql
```

### Scaling

```bash
# Scale backend workers
docker-compose up -d --scale backend=4

# Scale Celery workers
docker-compose up -d --scale celery_worker=4
```

---

## 🐛 Troubleshooting

### Database Connection Issues

```bash
# Check database is running
docker-compose ps db

# Check connection
docker-compose exec backend python -c "from database import db_config; print(db_config.health_check())"

# View database logs
docker-compose logs db
```

### Redis Connection Issues

```bash
# Check Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping

# View Redis logs
docker-compose logs redis
```

### API Not Responding

```bash
# Check backend status
docker-compose ps backend

# View backend logs
docker-compose logs backend

# Restart backend
docker-compose restart backend
```

---

## 📈 Performance Optimization

### Database Optimization

```sql
-- Create indexes
CREATE INDEX idx_sessions_user_id ON call_sessions(user_id);
CREATE INDEX idx_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_audit_logs_user_timestamp ON audit_logs(user_id, timestamp);
```

### Redis Configuration

```bash
# Increase max memory
docker-compose exec redis redis-cli CONFIG SET maxmemory 256mb
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### Nginx Tuning

Edit `nginx/nginx.conf`:
```nginx
worker_processes auto;
worker_connections 2048;
keepalive_timeout 30;
```

---

## 📞 Support

For issues or questions:
- Email: support@callsim.com
- Documentation: https://docs.callsim.com
- GitHub Issues: https://github.com/yourorg/callsim/issues

---

## 📝 License

© CallSim • 2026
