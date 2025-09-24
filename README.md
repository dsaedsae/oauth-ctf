# OAuth CTF Challenge

## Setup
```bash
docker-compose up
```

Access: http://localhost:5000

## Challenge Overview
5-stage OAuth attack chain:
1. SSRF via Client Registration
2. XSS to steal Authorization Code
3. PKCE Downgrade Attack
4. GraphQL Introspection
5. Scope Escalation

## Rules
- Complete stages in order
- No brute forcing
- Flag format: CTF{...}

## Getting Started
1. Register an OAuth client at /auth/register
2. Find and exploit the SSRF vulnerability
3. Continue through each stage...

## 🎮 5-Stage Attack Chain

### **Stage 1**: SSRF via OAuth Client Registration
- **Target**: `/auth/register` endpoint
- **Vulnerability**: Unvalidated `logo_uri` parameter
- **Goal**: Access internal services (AWS metadata, localhost services)
- **Flag**: `CTF{ssrf_client_registration_exposed}`

### **Stage 2**: XSS in Guestbook System (Self-Contained)
- **Target**: `/app/guestbook` message system
- **Vulnerability**: Unsanitized HTML rendering
- **Goal**: Capture admin data via XSS when bot visits
- **Flag**: `CTF{xss_authorization_code_stolen}`

**Self-Contained Attack Flow:**
1. Post XSS payload: `<script>fetch('/capture',{method:'POST',body:JSON.stringify({client_id:'YOUR_ID',data:document.cookie})})</script>`
2. Trigger admin visit: `GET /admin/simulate-visit/YOUR_CLIENT_ID`
3. Check results: `GET /check-capture/YOUR_CLIENT_ID`

### **Stage 3**: PKCE Bypass & JWT Manipulation
- **Target**: `/token/exchange` endpoint
- **Vulnerability**: PKCE downgrade + scope escalation
- **Goal**: Escalate from user to admin privileges
- **Flag**: `CTF{pkce_downgrade_jwt_confusion}`

### **Stage 4**: GraphQL Introspection
- **Target**: `/graphql` endpoint
- **Vulnerability**: Introspection enabled in production
- **Goal**: Discover admin schema and endpoints
- **Flag**: `CTF{graphql_introspection_admin_scope}`

### **Stage 5**: Scope Escalation
- **Target**: `/token/refresh` endpoint
- **Vulnerability**: Refresh token scope escalation
- **Goal**: Escalate to ADMIN_SECRETS scope
- **Final Flag**: `CTF{refresh_token_scope_escalation}`

## 🛠️ Testing

Run the automated solution:
```bash
python test_solution.py
```

Check client progress:
```bash
curl http://localhost:5000/progress/{client_id}
```

## 🎯 API Endpoints

**Main Challenge:**
- `POST /auth/register` - Register OAuth client (Stage 1)
- `POST /app/guestbook` - Post guestbook message (Stage 2)
- `POST /token/exchange` - Exchange authorization code (Stage 3)
- `POST /graphql` - GraphQL endpoint (Stage 4)
- `POST /token/refresh` - Refresh token (Stage 5)

**Self-Contained XSS:**
- `POST /capture` - Endpoint for XSS payloads to send data
- `GET /check-capture/{client_id}` - Check captured XSS data
- `GET /admin/simulate-visit/{client_id}` - Simulate admin bot visit
- `GET /debug/xss-result/{client_id}` - Debug XSS execution results

**Progress Tracking:**
- `GET /progress/{client_id}` - Check overall progress

## 🐛 Debugging

```bash
# View logs
docker-compose logs -f web

# Check Redis keys
docker-compose exec redis redis-cli
> KEYS client:*

# Health check
curl http://localhost:5000/health
```

## ⚠️ Security Notice

This application contains intentional vulnerabilities for educational purposes only. Never deploy in production.