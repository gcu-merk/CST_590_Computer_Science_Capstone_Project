# Security TODOs (OWASP Compliance)

This list tracks open security and OWASP-related concerns for the Raspberry Pi 5 Edge ML Traffic Monitoring System. Each item should be reviewed and checked off as it is addressed.

## 1. Authentication & Authorization
- [ ] Enforce authentication and authorization on all API and WebSocket endpoints (Flask, REST, dashboard).
- [ ] Implement role-based access control where appropriate.
- [ ] Disable SSH password authentication; require SSH keys only.

## 2. Sensitive Data Exposure
- [ ] Ensure no secrets, passwords, or API keys are hardcoded in code or configs.
- [ ] Use HTTPS/TLS for all network traffic (API, WebSocket, dashboard) in production.
- [ ] Enable disk encryption for sensitive data at rest.

## 3. Input Validation & Injection
- [ ] Validate and sanitize all user input (API, WebSocket, config files).
- [ ] Sanitize arguments to any shell commands (os.system, subprocess, etc.).

## 4. Session Management
- [ ] Use secure session management for any web UI (HttpOnly, Secure, SameSite cookies, session expiration).

## 5. Logging & Error Handling
- [ ] Ensure sensitive data is never logged.
- [ ] Avoid exposing stack traces or debug info to users in production.

## 6. Configuration & Secrets Management
- [ ] Manage all secrets via environment variables or secure vaults, not in code or public repos.

## 7. Dependencies
- [ ] Regularly update dependencies and scan for vulnerabilities (pip-audit, safety, etc.).

## 8. Access Control & Least Privilege
- [ ] Limit OS user accounts and permissions; run containers as non-root where possible.

## 9. Network Security
- [ ] Enable and configure firewall; only required ports should be open.
- [ ] Disable unused services and ports.

## 10. Data Privacy & Compliance
- [ ] Anonymize or properly handle any PII (vehicle images, logs) per compliance requirements.
- [ ] Implement data retention and deletion policies.

## 11. Other Concerns
- [ ] Validate file uploads and scan for malware (if any file upload is supported).
- [ ] Avoid unsafe deserialization (pickle, yaml.load, etc.).
- [ ] Implement rate limiting (Flask-Limiter or similar) to prevent API abuse.
- [ ] Use CSRF tokens and output encoding for any web UI.

---

**Review this list regularly and update as new security issues are discovered or resolved.**
