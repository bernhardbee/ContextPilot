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

### 5. Rate Limiting

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

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Security Settings
CONTEXTPILOT_ENABLE_AUTH=true
CONTEXTPILOT_API_KEY=your-secure-key

# CORS Settings
CONTEXTPILOT_CORS_ORIGINS=["https://yourdomain.com"]

# Rate Limits
CONTEXTPILOT_MAX_CONTENT_LENGTH=10000
CONTEXTPILOT_MAX_CONTEXTS_PER_REQUEST=20
```

## Production Deployment Checklist

- [ ] Enable authentication (`ENABLE_AUTH=true`)
- [ ] Generate and set a secure API key
- [ ] Configure specific CORS origins (no wildcards)
- [ ] Set appropriate rate limits
- [ ] Use HTTPS/TLS in production
- [ ] Keep dependencies updated
- [ ] Enable logging and monitoring
- [ ] Configure prompt log retention/export schedule
- [ ] Secure the logs directory with appropriate permissions
- [ ] Implement log backup and archival strategy
- [ ] Review privacy/compliance requirements for prompt logs
- [ ] Regular security audits

## 6. Prompt Logging & Audit Trail

All AI prompt generations are automatically logged for traceability:

- **Complete Audit Trail**: Every prompt generation is logged with full context
- **Secure Storage**: Logs stored in-memory with automatic rotation
- **Authenticated Access**: All log endpoints require API key authentication
- **Export Capability**: Logs can be exported to timestamped JSON files

**Logs Directory Security**:
```bash
# Ensure logs directory has restricted permissions
chmod 700 backend/logs/
chown contextpilot:contextpilot backend/logs/
```

**Log Contents**:
Logs contain sensitive information including:
- User task descriptions
- Context content
- Generated prompts

**Best Practices**:
- Regularly export and archive logs to secure storage
- Implement log retention policies
- Encrypt exported log files if they contain sensitive data
- Monitor log access via audit logs
- Consider GDPR/privacy requirements for user data in logs

See [PROMPT_LOGGING.md](PROMPT_LOGGING.md) for complete documentation.

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
