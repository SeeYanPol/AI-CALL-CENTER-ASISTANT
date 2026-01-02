# 🚀 CallSim v2.0 - Quick Start Checklist

## ✅ Pre-Deployment Checklist

### 1. Prerequisites
- [ ] Docker & Docker Compose installed
- [ ] OpenAI API key obtained
- [ ] Domain name registered (for production)
- [ ] Git repository set up

### 2. Environment Configuration
```bash
cd backend
cp .env.example .env
```

Edit `.env` and configure:
- [ ] Generate `FLASK_SECRET_KEY` (run: `python -c "import secrets; print(secrets.token_hex(32))"`)
- [ ] Generate `JWT_SECRET_KEY` (run: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- [ ] Add `OPENAI_API_KEY=sk-your-key-here`
- [ ] Set `ALLOWED_ORIGINS` to your frontend URLs
- [ ] (Optional) Add `SENTRY_DSN` for error tracking

### 3. First Deployment
```bash
# Start all services
docker-compose up -d

# Initialize database
docker-compose exec backend python init_db.py

# Verify services
docker-compose ps
```

### 4. Verify Installation
- [ ] Visit http://localhost (Frontend loads)
- [ ] Visit http://localhost/api/health (Returns "healthy")
- [ ] Visit http://localhost/api/docs (Swagger UI loads)
- [ ] Login with admin@callsim.com / Admin123!

### 5. Security Setup
- [ ] Change default admin password
- [ ] Review and restrict `ALLOWED_ORIGINS`
- [ ] Verify all secret keys are unique
- [ ] Enable HTTPS (production only)

---

## 🔐 Post-Deployment Checklist

### 1. User Management
- [ ] Create test users with different roles
- [ ] Test user registration flow
- [ ] Test user login flow
- [ ] Verify JWT tokens work
- [ ] Test role-based access control

### 2. Functionality Testing
- [ ] Start a call session
- [ ] Send chat messages
- [ ] Test AI responses
- [ ] Test TTS functionality
- [ ] End session and verify transcript
- [ ] Check data persists after restart

### 3. API Testing
```bash
# Health check
curl http://localhost/api/health

# Register user
curl -X POST http://localhost/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test123!","full_name":"Test User"}'

# Login
curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test123!"}'
```

### 4. Performance Verification
- [ ] Check database connections (should not exceed pool size)
- [ ] Check Redis connections (should be active)
- [ ] Monitor response times (should be <200ms)
- [ ] Test concurrent users (start with 10)
- [ ] Check Celery workers are processing tasks

### 5. Monitoring Setup
- [ ] Check logs: `docker-compose logs -f backend`
- [ ] Verify health endpoint returns all services healthy
- [ ] Set up Sentry (if configured)
- [ ] Set up uptime monitoring (optional)

---

## 🐛 Troubleshooting Checklist

### Database Issues
- [ ] PostgreSQL is running: `docker-compose ps db`
- [ ] Can connect to database: `docker-compose exec db psql -U callsim -d callsim`
- [ ] Tables exist: `docker-compose exec backend python -c "from database import db_config; print(db_config.health_check())"`

### Redis Issues
- [ ] Redis is running: `docker-compose ps redis`
- [ ] Can connect to Redis: `docker-compose exec redis redis-cli ping`
- [ ] Check memory usage: `docker-compose exec redis redis-cli INFO memory`

### Backend Issues
- [ ] Backend is running: `docker-compose ps backend`
- [ ] Check logs: `docker-compose logs backend`
- [ ] Health check passes: `curl http://localhost/api/health`
- [ ] Environment variables loaded: `docker-compose exec backend env | grep FLASK`

### Frontend Issues
- [ ] Nginx is running: `docker-compose ps nginx`
- [ ] Can access frontend: `curl http://localhost`
- [ ] Check nginx logs: `docker-compose logs nginx`
- [ ] CORS headers present: `curl -I http://localhost/api/health`

---

## 📊 Production Readiness Checklist

### Security
- [ ] All default passwords changed
- [ ] Secret keys are unique and secure
- [ ] HTTPS enabled and enforced
- [ ] CORS properly configured (not using *)
- [ ] Rate limiting active
- [ ] Security headers enabled
- [ ] Audit logging enabled
- [ ] Firewall rules configured
- [ ] Database encrypted at rest
- [ ] Backups configured

### Performance
- [ ] Database indexes created
- [ ] Redis cache working
- [ ] CDN configured for static assets
- [ ] Gzip compression enabled
- [ ] Connection pooling optimized
- [ ] Load testing completed
- [ ] Scaling strategy defined

### Reliability
- [ ] Automated backups scheduled
- [ ] Health checks configured
- [ ] Auto-restart enabled
- [ ] Log rotation configured
- [ ] Disk space monitoring
- [ ] Database backups tested
- [ ] Disaster recovery plan documented

### Monitoring
- [ ] Error tracking (Sentry) active
- [ ] Logging centralized
- [ ] Metrics collection configured
- [ ] Alerts set up for critical issues
- [ ] Uptime monitoring active
- [ ] Performance monitoring active

### Documentation
- [ ] API documentation accessible
- [ ] Deployment guide reviewed
- [ ] Runbooks created
- [ ] Team trained
- [ ] Support contacts documented

---

## 🎯 User Acceptance Testing Checklist

### Admin User
- [ ] Can view all users
- [ ] Can access admin endpoints
- [ ] Can manage user roles
- [ ] Can view system logs

### Trainer User
- [ ] Can create call sessions
- [ ] Can view trainee sessions
- [ ] Cannot access admin endpoints
- [ ] Can generate reports

### Trainee User
- [ ] Can register and login
- [ ] Can start call sessions
- [ ] Can chat with AI
- [ ] Can end sessions and view transcripts
- [ ] Cannot access other users' data
- [ ] Cannot access admin endpoints

### General Functionality
- [ ] Chat responses are relevant
- [ ] TTS works and sounds natural
- [ ] Session persistence works
- [ ] Transcripts are accurate
- [ ] Performance scores calculate
- [ ] UI is responsive

---

## 📈 Scaling Checklist

When you need to scale:

### Horizontal Scaling (More Users)
```bash
# Scale backend workers
docker-compose up -d --scale backend=4

# Scale Celery workers
docker-compose up -d --scale celery_worker=4
```

### Vertical Scaling (More Resources)
- [ ] Increase database connection pool
- [ ] Increase Redis max memory
- [ ] Increase Gunicorn workers
- [ ] Increase server RAM/CPU

### Database Optimization
```sql
-- Create performance indexes
CREATE INDEX idx_sessions_user_id ON call_sessions(user_id);
CREATE INDEX idx_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_users_email ON users(email);
```

### Caching Optimization
- [ ] Enable TTS response caching
- [ ] Cache common AI responses
- [ ] Implement browser caching
- [ ] Use CDN for static assets

---

## 🔄 Maintenance Checklist

### Daily
- [ ] Check health endpoint
- [ ] Review error logs
- [ ] Monitor disk space

### Weekly
- [ ] Review user activity
- [ ] Check database size
- [ ] Review API usage
- [ ] Check for security updates

### Monthly
- [ ] Database backup verification
- [ ] Performance review
- [ ] Security audit
- [ ] Update dependencies
- [ ] Clean up old sessions
- [ ] Review and rotate logs

### Quarterly
- [ ] Disaster recovery drill
- [ ] Full security audit
- [ ] Capacity planning review
- [ ] User feedback review

---

## 📞 Support Contacts

**Technical Issues:**
- Error logs: `docker-compose logs -f`
- Database issues: Check DEPLOYMENT.md
- Redis issues: Check DEPLOYMENT.md

**Documentation:**
- API Docs: http://localhost/api/docs
- Deployment Guide: DEPLOYMENT.md
- Implementation Details: IMPLEMENTATION_SUMMARY.md

**Emergency Commands:**
```bash
# Restart all services
docker-compose restart

# View all logs
docker-compose logs -f

# Stop everything
docker-compose down

# Nuclear option (reset everything - DANGER!)
docker-compose down -v
docker-compose up -d
docker-compose exec backend python init_db.py
```

---

## ✅ Final Go-Live Checklist

Before making the system public:

- [ ] All tests passing
- [ ] Security audit completed
- [ ] Performance testing completed
- [ ] Backups configured and tested
- [ ] Monitoring active
- [ ] Documentation complete
- [ ] Team trained
- [ ] Rollback plan documented
- [ ] Support process defined
- [ ] Legal/compliance review (if needed)
- [ ] Marketing assets ready
- [ ] User communication sent

---

**Last Updated:** January 1, 2026  
**Version:** 2.0.0  
**Status:** Production Ready ✅
