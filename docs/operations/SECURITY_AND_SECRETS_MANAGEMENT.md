# Security & Secrets Management Guide

**Edge AI Traffic Monitoring System**  
**Grand Canyon University - CST 590 Capstone Project**

---

## 🔐 Overview

This guide covers secure management of credentials, secrets, and sensitive configuration for the Edge AI Traffic Monitoring System.

---

## ⚠️ Critical Security Rules

### Never Commit Secrets
❌ **NEVER** commit these files to git:
- `.env` (actual environment file)
- `secrets.txt`
- `credentials.json`
- `*.key`, `*.pem`, `*.crt` (certificate files)
- Any file containing passwords, API keys, or tokens

✅ **ALWAYS** use:
- `.env.example` with placeholder values
- Environment variables for runtime
- Secure secret stores for production

---

## 🚀 Quick Start

### 1. Initial Setup

```bash
# Copy the example file
cp .env.example .env

# Generate secure secrets
python scripts/system/generate_secrets.py

# Edit .env and paste the generated secrets
nano .env  # or your preferred editor
```

### 2. Verify .env is Ignored

```bash
# Check git status - .env should NOT appear
git status

# If .env appears, make sure .gitignore contains:
# .env
# !.env.example
```

### 3. Set Production Secrets

For production deployment, use strong, unique secrets:

```bash
# Generate secrets
python scripts/system/generate_secrets.py > /tmp/secrets.txt

# View secrets
cat /tmp/secrets.txt

# Copy to .env file
# Then SECURELY DELETE the temporary file
shred -vfz -n 10 /tmp/secrets.txt  # Linux
# or
rm /tmp/secrets.txt  # macOS/Windows
```

---

## 🔑 Required Secrets

### Database Password
**Variable**: `POSTGRES_PASSWORD`  
**Purpose**: PostgreSQL database authentication  
**Requirements**:
- Minimum 16 characters
- Mix of uppercase, lowercase, numbers, special characters
- No dictionary words

**Generate**:
```python
import secrets
password = secrets.token_urlsafe(32)
```

### Flask Secret Key
**Variable**: `SECRET_KEY`  
**Purpose**: Session encryption, CSRF protection  
**Requirements**:
- Minimum 32 characters
- Cryptographically random
- URL-safe characters

**Generate**:
```python
import secrets
secret_key = secrets.token_urlsafe(32)
```

### JWT Secret
**Variable**: `JWT_SECRET`  
**Purpose**: JWT token signing  
**Requirements**:
- Minimum 32 characters
- Different from SECRET_KEY
- Cryptographically random

**Generate**:
```python
import secrets
jwt_secret = secrets.token_urlsafe(32)
```

### Redis Password (Optional)
**Variable**: `REDIS_PASSWORD`  
**Purpose**: Redis authentication  
**Requirements**:
- Required for production
- Minimum 16 characters
- Strong random password

---

## 🏭 Production Deployment

### Secret Storage Options

#### Option 1: Environment Variables (Recommended for Docker)
```bash
# Set in docker-compose.yml
environment:
  - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
  - SECRET_KEY=${SECRET_KEY}
  - JWT_SECRET=${JWT_SECRET}

# Load from .env automatically
docker-compose --env-file .env up -d
```

#### Option 2: Docker Secrets (Recommended for Swarm)
```bash
# Create secrets
echo "strong_password_here" | docker secret create postgres_password -
echo "secret_key_here" | docker secret create secret_key -

# Reference in docker-compose.yml
secrets:
  - postgres_password
  - secret_key
```

#### Option 3: External Secret Store (Enterprise)
- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault
- Google Cloud Secret Manager

---

## 🔄 Secret Rotation

### When to Rotate

Rotate secrets immediately if:
- ❗ Secret is compromised
- ❗ Employee with access leaves
- ❗ System breach detected

Rotate secrets regularly:
- 🔄 Every 90 days (recommended)
- 🔄 Every 180 days (minimum)

### Rotation Procedure

1. **Generate New Secrets**
   ```bash
   python scripts/system/generate_secrets.py > new_secrets.txt
   ```

2. **Update .env File**
   ```bash
   # Backup current .env
   cp .env .env.backup
   
   # Update with new secrets
   nano .env
   ```

3. **Restart Services**
   ```bash
   # For Docker Compose
   docker-compose down
   docker-compose up -d
   
   # For systemd services
   sudo systemctl restart traffic-monitoring
   ```

4. **Verify Services**
   ```bash
   # Check all services are running
   docker-compose ps
   
   # Test API endpoint
   curl http://localhost:5000/api/health
   ```

5. **Update Production Systems**
   ```bash
   # Deploy to production
   # (specific commands depend on your deployment method)
   ```

6. **Delete Old Secrets**
   ```bash
   # Securely delete backup
   shred -vfz -n 10 .env.backup
   rm new_secrets.txt
   ```

---

## 🛡️ Security Best Practices

### Development Environment
- ✅ Use weak passwords for local development
- ✅ Document default credentials in README
- ✅ Never use development credentials in production
- ✅ Keep .env.example up to date

### Production Environment
- ✅ Generate strong, unique secrets for each environment
- ✅ Use different secrets for staging vs. production
- ✅ Limit access to production .env files (chmod 600)
- ✅ Use secret stores when available
- ✅ Enable audit logging for secret access
- ✅ Implement secret rotation schedule

### Code Practices
- ✅ Never hardcode secrets in source code
- ✅ Use environment variables or config files
- ✅ Redact secrets in logs
- ✅ Don't log .env file contents
- ✅ Use `***REDACTED***` in error messages

---

## 🚨 Security Checklist

### Pre-Deployment
- [ ] .env file is in .gitignore
- [ ] No secrets in git history
- [ ] .env.example has placeholder values
- [ ] Strong secrets generated for production
- [ ] Secrets are unique per environment
- [ ] .env file has restricted permissions (600)

### Post-Deployment
- [ ] Services start successfully
- [ ] Database authentication works
- [ ] API authentication works
- [ ] No secrets in log files
- [ ] Health checks pass
- [ ] Monitoring alerts configured

### Ongoing
- [ ] Secret rotation schedule defined
- [ ] Access to secrets is limited
- [ ] Audit logs reviewed monthly
- [ ] Incident response plan documented

---

## 📚 Additional Resources

### Scripts
- `scripts/system/generate_secrets.py` - Secret generation utility
- `.env.example` - Template configuration file

### Documentation
- [Docker Secrets](https://docs.docker.com/engine/swarm/secrets/)
- [12-Factor App - Config](https://12factor.net/config)
- [OWASP Secret Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

---

## 🆘 Incident Response

### If Secrets Are Compromised

1. **Immediate Actions**
   - Rotate all affected secrets immediately
   - Restart all services with new secrets
   - Review access logs for unauthorized access
   - Notify security team/stakeholders

2. **Investigation**
   - Determine how secrets were exposed
   - Check git history: `git log -p --all -S 'SECRET_KEY'`
   - Review application logs
   - Audit who had access

3. **Remediation**
   - Remove secrets from git history if committed
   - Update documentation and procedures
   - Implement additional safeguards
   - Conduct security training if needed

4. **Prevention**
   - Enable pre-commit hooks to detect secrets
   - Use git-secrets or similar tools
   - Regular security audits
   - Principle of least privilege

---

## 📧 Support

For security concerns:
- **Email**: [security contact - add here]
- **Issues**: [GitHub Issues](https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project/issues) (for non-sensitive issues only)

**Remember**: Never post actual secrets in issues or pull requests!

---

**Last Updated**: October 7, 2025  
**Version**: 1.0  
**Status**: ✅ Production Ready
