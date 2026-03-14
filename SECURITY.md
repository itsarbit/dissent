# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Email**: itsarbit@gmail.com
2. **Subject**: `[SECURITY] dissent - <brief description>`
3. **Do not** open a public issue for security vulnerabilities

### What to include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response timeline

- **48 hours**: Acknowledgment of your report
- **7 days**: Fix for critical issues
- **30 days**: Fix for non-critical issues

### Scope

- Prompt injection via crafted diffs that could cause unintended LLM behavior
- API key exposure through logs or output
- Arbitrary code execution via persona YAML files
- Dependency vulnerabilities

## Responsible Disclosure

We ask that you give us reasonable time to address vulnerabilities before public disclosure. We will credit reporters in the fix announcement unless anonymity is requested.
