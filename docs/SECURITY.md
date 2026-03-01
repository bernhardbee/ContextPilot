# Security Guide

## Overview

ContextPilot implements multiple layers of security to protect your data and ensure safe operation.

## Security Features

### 1. Input Validation

All user inputs are validated before processing:

- **Content Length Limits**: Content is limited to 10,000 characters by default
- **Tag Validation**: Maximum 20 tags, each up to 50 characters
- **Character Sanitization**: Control characters and null bytes are removed
- **Empty Input Rejection**: Empty or whitespace-only inputs are rejected

### 2. Input Sanitization

All text inputs are automatically sanitized:
- Removal of null bytes (`\x00`)
- Removal of control characters (except newlines and tabs)
- Trimming of leading/trailing whitespace
- Preservation of valid Unicode characters

### 3. CORS Configuration

Cross-Origin Resource Sharing (CORS) is configurable via environment variables:

```bash
CONTEXTPILOT_CORS_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]
```

**Security Best Practice**: Never use `["*"]` in production. Always specify exact allowed origins.

### 4. API Key Authentication (Optional)

Enable API key authentication for production deployments:

```bash
CONTEXTPILOT_ENABLE_AUTH=true
CONTEXTPILOT_API_KEY=your-secure-random-key-here
```

When enabled, all API requests must include the header:
```
X-API-Key: your-secure-random-key-here
```

**Generating a Secure API Key**:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 5. Request Signing (Optional, recommended for production)

ContextPilot supports optional HMAC request signing for mutating methods (`POST`, `PUT`, `DELETE` by default).

Enable request signing:

```bash
CONTEXTPILOT_ENABLE_REQUEST_SIGNING=true
CONTEXTPILOT_REQUEST_SIGNING_SECRET=your-shared-signing-secret
CONTEXTPILOT_REQUEST_SIGNING_MAX_AGE_SECONDS=300
CONTEXTPILOT_REQUEST_SIGNING_METHODS=["POST","PUT","DELETE"]
```

When enabled, signed requests must include:

```text
X-Request-Signature: <hex hmac sha256>
X-Request-Timestamp: <unix epoch seconds>
```

Signing payload format:

```text
METHOD\nPATH\nTIMESTAMP\nSHA256(BODY)
```

If signing is enabled but the signing secret is missing, mutating endpoints return `503` until configuration is fixed.

### 6. Rate Limiting

Built-in limits prevent abuse:
- Maximum contexts per request: 20 (configurable)
- Maximum content length: 10,000 characters (configurable)
- Maximum tags per context: 20 (configurable)

Configure via environment variables:
```bash
CONTEXTPILOT_MAX_CONTEXTS_PER_REQUEST=20
CONTEXTPILOT_MAX_CONTENT_LENGTH=10000
CONTEXTPILOT_MAX_TAG_COUNT=20
```

### 7. Security Headers Middleware

ContextPilot now attaches defensive HTTP response headers by default:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(), microphone=(), camera=()`
- `Content-Security-Policy` baseline

For HTTPS requests (`X-Forwarded-Proto: https`), HSTS is added:

- `Strict-Transport-Security: max-age=<configured>; includeSubDomains`

Configuration:

```bash
CONTEXTPILOT_ENABLE_SECURITY_HEADERS=true
CONTEXTPILOT_HSTS_MAX_AGE_SECONDS=31536000
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Security Settings
CONTEXTPILOT_ENABLE_AUTH=true
CONTEXTPILOT_API_KEY=your-secure-key
CONTEXTPILOT_ENABLE_REQUEST_SIGNING=true
CONTEXTPILOT_REQUEST_SIGNING_SECRET=your-shared-signing-secret
CONTEXTPILOT_ENABLE_SECURITY_HEADERS=true
CONTEXTPILOT_HSTS_MAX_AGE_SECONDS=31536000

# CORS Settings
CONTEXTPILOT_CORS_ORIGINS=["https://yourdomain.com"]

# Rate Limits
CONTEXTPILOT_MAX_CONTENT_LENGTH=10000
CONTEXTPILOT_MAX_CONTEXTS_PER_REQUEST=20
```

### Secrets Management (IMPORTANT)

#### Protecting LLM Provider Keys

Never commit API keys or secrets to version control:

```bash
# .gitignore example
.env              # Contains API keys, never commit
.env.local        # Local overrides
backend/.env      # Backend-specific secrets
```

**If you accidentally commit secrets:**

1. Immediately rotate the compromised key in the provider's dashboard
2. Scan git history to ensure previous commits are clean:
   ```bash
   git log --all -- .env | head -20  # View history
   ```
3. Remove the file from git history (if committed):
   ```bash
   git filter-branch --tree-filter 'rm -f .env' -- --all
   git push origin --force --all
   ```

#### Provider API Keys

Ensure these sensitive items are never in version control:

- **OpenAI API Key**: Used for GPT models
- **Anthropic API Key**: Used for Claude models  
- **Ollama URL**: If hosting remote Ollama instance

Store these in:
- Environment variables (development)
- `.env` file (local development only - .gitignored)
- Secrets management system (production):
  - AWS Secrets Manager
  - HashiCorp Vault
  - GitHub Secrets
  - GitLab CI/CD Secrets

#### Model Catalog Security

The `backend/valid_models.json` file defines available models but does **not** contain any secrets:
- Safe to commit to version control
- Used by sync_models.py to keep lists in sync
- Contains only model names and metadata, no API keys

See [MODEL_SYNCHRONIZATION.md](./MODEL_SYNCHRONIZATION.md) for details.

## Production Deployment Checklist

- [ ] Enable authentication (`ENABLE_AUTH=true`)
- [ ] Generate and set a secure API key
- [ ] Enable request signing for mutating endpoints
- [ ] Configure signing secret and timestamp window
- [ ] Configure specific CORS origins (no wildcards)
- [ ] Set appropriate rate limits
- [ ] Use HTTPS/TLS in production
- [ ] Keep dependencies updated
- [ ] Enable logging and monitoring
- [ ] Regular security audits

## Threat Model

### Protected Against

✅ **Input Injection**: All inputs are validated and sanitized  
✅ **Content Length Attacks**: Strict length limits enforced  
✅ **Unauthorized Access**: Optional API key authentication  
✅ **CORS Violations**: Configurable allowed origins  
✅ **Malformed Unicode**: Proper unicode handling

### Not Protected Against (Requires Additional Measures)

⚠️ **DDoS Attacks**: Use a reverse proxy (nginx, Cloudflare) with rate limiting  
⚠️ **Replay Attacks**: Implement request signing or nonces if needed  
⚠️ **Data at Rest**: No encryption of in-memory data (use encrypted storage in production)  
⚠️ **Network Eavesdropping**: Always use HTTPS/TLS

## Security Best Practices

### 1. Use HTTPS

Always deploy behind HTTPS in production:
```nginx
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
    }
}
```

### 2. Use a Reverse Proxy

Deploy behind nginx or similar for:
- Rate limiting
- SSL termination
- Request filtering
- Static file serving

### 3. Regular Updates

Keep dependencies updated:
```bash
pip list --outdated
pip install -U <package>
```

### 4. Monitoring and Logging

Monitor for suspicious activity:
- Failed authentication attempts
- Unusual request patterns
- Input validation failures

## Reporting Security Issues

If you discover a security vulnerability, please email: security@example.com

**Do not** open public GitHub issues for security vulnerabilities.

## Compliance

### Data Privacy

- Data is stored in-memory by default (no persistence)
- No data is sent to external services (except model downloads)
- Embeddings are generated locally

### GDPR Considerations

If storing personal data:
- Implement data deletion on request
- Consider data encryption at rest
- Implement access logging
- Add consent mechanisms

## Additional Resources

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
