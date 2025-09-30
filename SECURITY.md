# 🔒 Security Notice

## ⚠️ Educational Purpose Only

This repository contains **intentionally vulnerable code** designed for educational purposes and security training.

**DO NOT USE IN PRODUCTION ENVIRONMENTS**

## 🎯 Vulnerabilities Included

This CTF challenge intentionally includes the following vulnerabilities for educational purposes:

1. **Server-Side Request Forgery (SSRF)** - Unvalidated URL fetching
2. **Cross-Site Scripting (XSS)** - Unescaped HTML rendering
3. **PKCE Downgrade Attack** - Weak code challenge method validation
4. **GraphQL Introspection** - Schema exposure in production
5. **OAuth Scope Escalation** - Insufficient authorization checks

## 🚨 Security Warnings

- **Hardcoded Secrets**: Contains intentional hardcoded secrets for CTF purposes
- **No Input Validation**: Many endpoints lack proper input validation
- **Weak Authentication**: Uses predictable tokens and weak encryption
- **Information Disclosure**: Exposes sensitive data intentionally

## 🛡️ Safe Usage Guidelines

1. **Isolated Environment Only**: Run only in isolated, non-production environments
2. **No Real Data**: Never use with real user data or credentials
3. **Educational Context**: Use only for learning and training purposes
4. **Responsible Disclosure**: If you find additional vulnerabilities, please report them for educational improvement

## 📝 Reporting Security Issues

If you discover security issues beyond the intended vulnerabilities:

1. **DO NOT** create public GitHub issues
2. Email: [security@example.com] (replace with actual contact)
3. Provide detailed reproduction steps
4. Allow time for response before public disclosure

## 🎓 Learning Resources

This CTF is designed to teach:
- OAuth 2.0 security best practices
- Common web application vulnerabilities
- Secure coding techniques
- Penetration testing methodologies

## ⚖️ Legal Notice

By using this code, you agree to:
- Use it only for educational and authorized testing purposes
- Not deploy it in production or public-facing environments
- Take full responsibility for any misuse
- Comply with all applicable laws and regulations

---

**Remember: With great power comes great responsibility. Use these tools ethically and legally.**