# Troubleshooting

## Python or Git is not found

Install the required software, restart the terminal, and verify `python --version` and `git --version`. Try `python3` on macOS/Linux or `py` on Windows. Python 3.10+ and Git 2.27+ are required.

## The port is already in use

Use `python app.py --port 8090` or `--port 0` to choose an available port. Open the URL printed at startup. The server only accepts matching localhost/loopback Host headers.

## Repository not found or access denied

Use the main repository HTTPS page. Check spelling, token repository access, read permissions, expiry, organization SSO, and provider policy. Tokens must be re-entered for a new private-repository job. Never place a token in the URL.

## Repository URL or host rejected

SSH, HTTP, branch/file/issue links, URL credentials, custom ports, and private-network hosts are unsupported. GitLab supports nested namespaces and public self-hosted HTTPS instances. GitHub enterprise-specific URLs/APIs are not currently a dedicated provider integration.

## Metadata is unavailable

History and file charts use Git independently of metadata. API rate limits or insufficient token scopes can leave stars/forks/license/issues unavailable. GitLab private metadata needs `read_api`; GitHub license and issue values may depend on repository permissions. An unavailable license field is not a licensing determination.

## Charts are empty

Try **All history**. Recent-period presets end today, so inactive repositories can legitimately show zero. Check UTC range endpoints and merge exclusion. Only commits reachable from the analyzed default branch are included.

## Numbers differ from provider graphs

Providers can use different branches, timestamp rules, bot filters, merge rules, or contributor identity mappings. RepoLens uses committer time in UTC and author identity for grouping. See [Analytics definitions](analytics.md).

## Analysis is slow or times out

First-time clones can be large even with partial-clone filtering. Allow sufficient disk/memory and network time; clone/fetch operations time out after 15 minutes. Cached reruns with refresh disabled avoid another history download, but still attempt provider metadata. There is no cancellation endpoint or automatic cache quota.

## Filters say the analysis expired

Restarting the app clears reports. New analysis submissions may also evict older/expired results. Analyze the repository again to rebuild the source for filtering; the disk cache can speed this up.

## Browser tools fail

Developer browser tests need `npm ci` and `npx playwright install chromium`. Missing Linux system libraries may require Playwright’s `--with-deps` installer. These tools are optional and are not needed to use RepoLens.

## Reporting an unresolved issue

Include version, OS, Python/Git versions, exact steps, and redacted errors in the bug template. Do not attach `.cache/`, private exports, tokens, or unredacted screenshots. Use [SECURITY.md](../SECURITY.md) for vulnerabilities.
