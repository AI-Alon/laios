# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | ✔️ |

## Reporting a Vulnerability

If you discover a security vulnerability in LAIOS, please do **not** open a public GitHub issue.

Instead, report it by opening a [GitHub Security Advisory](https://github.com/AI-Alon/laios/security/advisories/new) so it can be addressed privately before public disclosure.

Please include:
- A clear description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fix (optional)

We will acknowledge your report within 48 hours and aim to release a fix within 14 days of confirmation.

## Scope

Security issues include:
- Shell injection via tool inputs
- Path traversal in filesystem tools
- Authentication bypass in the REST API
- Secrets leaking through logs or responses

Out of scope:
- Issues requiring physical access to the machine
- Social engineering attacks
- Vulnerabilities in third-party LLM providers (report those upstream)
