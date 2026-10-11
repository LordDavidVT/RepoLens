# Security policy

## Supported versions

Security fixes target the latest released 1.x version. Upgrade before reporting a problem that has already been fixed.

## Reporting a vulnerability

Do not post credentials, private repository data, exploit details, or sensitive logs in public issues.

If this repository offers **Security → Report a vulnerability**, submit a private report there. If that option is unavailable, open a public issue requesting a private reporting channel **without vulnerability details**, and wait for maintainers to arrange one. No private reporting feature is assumed to be enabled automatically.

Include the affected version, impact, a minimal reproduction with synthetic data, and any suggested mitigation. There is no guaranteed response time or bug bounty.

## Intended deployment

RepoLens is a local, single-user application bound to `127.0.0.1`. It has no user authentication and must not be exposed to the internet, other users, or untrusted reverse proxies.

Tokens are transient, but cached Git history may contain private information. DNS/IP checks are a basic safeguard, not a network sandbox. Only analyze repositories and hosts you trust. See [Privacy and security](docs/privacy.md) for the full threat model and limitations.
