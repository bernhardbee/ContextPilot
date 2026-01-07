# Deployment Guide

## Overview

This guide covers deploying ContextPilot to production environments.

## Prerequisites

- Python 3.9 or higher
- At least 2GB RAM (for the embedding model)
- Linux/macOS/Windows server
- (Optional) nginx or similar reverse proxy
- (Optional) SSL certificate for HTTPS

## Deployment Options

### Option 1: Docker Deployment (Recommended)

Coming soon - Docker configuration will be added in a future update.

### Option 2: Direct Deployment

#### Step 1: Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd ContextPilot/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Production .env configuration**:
```bash
# Server
CONTEXTPILOT_HOST=127.0.0.1  # Bind to localhost, use nginx as proxy
CONTEXTPILOT_PORT=8000
CONTEXTPILOT_LOG_LEVEL=WARNING

# CORS - Set your actual domain
CONTEXTPILOT_CORS_ORIGINS=["https://yourdomain.com"]

# Security
CONTEXTPILOT_ENABLE_AUTH=true
CONTEXTPILOT_API_KEY=<generate-secure-key>

# Limits
CONTEXTPILOT_MAX_CONTENT_LENGTH=10000
CONTEXTPILOT_MAX_CONTEXTS_PER_REQUEST=20

# Prompt Logging (Optional)
PROMPT_LOG_MAX_SIZE=10000  # Maximum logs to keep in memory
```

**Important**: Create logs directory and set permissions:
```bash
mkdir -p logs
chmod 700 logs
chown www-data:www-data logs  # Match your service user
```

#### Step 3: Run as System Service

Create systemd service file: `/etc/systemd/system/contextpilot.service`

```ini
[Unit]
Description=ContextPilot API Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/ContextPilot/backend
Environment="PATH=/path/to/ContextPilot/backend/venv/bin"
ExecStart=/path/to/ContextPilot/backend/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable contextpilot
sudo systemctl start contextpilot
sudo systemctl status contextpilot
```

### Option 3: Using Gunicorn (Production WSGI Server)

Install gunicorn:
```bash
pip install gunicorn
```

Run with gunicorn:
```bash
gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --log-level warning
```

## Nginx Configuration

### Basic Configuration

Create `/etc/nginx/sites-available/contextpilot`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    # API Proxy
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    # Access Logs
    access_log /var/log/nginx/contextpilot-access.log;
    error_log /var/log/nginx/contextpilot-error.log;
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/contextpilot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## SSL Certificate (Let's Encrypt)

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
sudo systemctl reload nginx
```

## Monitoring and Logging

### Application Logs

Configure logging in `.env`:
```bash
CONTEXTPILOT_LOG_LEVEL=WARNING
```

View logs:
```bash
sudo journalctl -u contextpilot -f
```

### Health Checks

Set up monitoring to check `/health` endpoint:
```bash
curl https://yourdomain.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-07T12:00:00.000000"
}
```

### Resource Monitoring

Monitor CPU, memory, and disk:
```bash
# Install monitoring tools
sudo apt-get install htop iotop

# Check resource usage
htop
```

## Backup and Recovery

### Data Persistence

By default, ContextPilot stores data in-memory. For production:

1. **Option A**: Implement periodic exports
2. **Option B**: Use persistent storage (requires code modification)

### Export/Import Contexts

Add to your deployment scripts:
```python
# Export contexts to JSON
import json
from storage import context_store

contexts = context_store.list_all(include_superseded=True)
with open('backup.json', 'w') as f:
    json.dump([c.dict() for c in contexts], f)
```

## Performance Optimization

### Model Caching

The embedding model is loaded once on startup. Ensure:
- Model is downloaded before deployment
- Sufficient memory (2GB+) available

### Resource Limits

Set resource limits in systemd:
```ini
[Service]
MemoryLimit=4G
CPUQuota=200%
```

### Scaling

For high traffic:
1. Run multiple workers with gunicorn
2. Use load balancer (nginx, HAProxy)
3. Consider caching layer (Redis)

## Security Hardening

### Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### File Permissions

```bash
# Set proper permissions
chmod 600 .env
chmod 755 venv/bin/*
chown -R www-data:www-data /path/to/ContextPilot
```

### Regular Updates

```bash
# Update system packages
sudo apt-get update && sudo apt-get upgrade

# Update Python dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

## Troubleshooting

### Common Issues

**Service won't start**:
```bash
# Check logs
sudo journalctl -u contextpilot -n 50

# Check port availability
sudo lsof -i :8000
```

**High memory usage**:
- The embedding model requires ~500MB
- Each context with embedding adds ~1KB
- Monitor with: `ps aux | grep python`

**Slow response times**:
- Check embedding generation performance
- Consider caching frequently used contexts
- Monitor with: `time curl https://yourdomain.com/health`

## Production Checklist

- [ ] Environment variables configured
- [ ] Authentication enabled
- [ ] HTTPS/TLS configured
- [ ] Nginx reverse proxy setup
- [ ] Rate limiting configured
- [ ] Logging enabled
- [ ] Monitoring setup
- [ ] Backup strategy implemented
- [ ] Firewall configured
- [ ] SSL certificate installed
- [ ] Health check endpoint tested
- [ ] Load testing completed

## Support

For deployment issues:
- Check logs: `sudo journalctl -u contextpilot`
- Review [SECURITY.md](SECURITY.md)
- Check [ARCHITECTURE.md](ARCHITECTURE.md)

## Additional Resources

- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt](https://letsencrypt.org/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
