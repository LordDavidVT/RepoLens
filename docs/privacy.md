# Privacy and security

## Data flow

The browser communicates with the local Python server. That server contacts the repository host over HTTPS for Git history and metadata; GitHub metadata uses `api.github.com`. There are no analytics trackers, external fonts, telemetry endpoints, or hosted chart services in the interface.

Repository names/URLs and public contributor names are displayed. Author emails are used server-side for grouping but are not included in dashboard reports or CSV. Raw Git history in the cache still contains commit metadata, including emails and messages.

## Tokens

- Tokens are supplied in the local JSON request body, not a URL or command-line argument.
- Git uses a temporary askpass script with the token in its process environment.
- Clone URLs and persistent Git configuration do not contain the token.
- Tokens are not written to browser storage or application logs, and the input is cleared once a job is accepted.
- The temporary helper is removed after repository loading; the server removes the token from job options when analysis finishes.
- Python/process memory is not cryptographically erased. Other processes running as the same user or with elevated privileges may inspect memory/environment. This tool does not defend against a compromised local account.

Cache keys are SHA-256 hashes derived from the normalized repository URL and token. That separates credentials’ caches, but is not encryption or an access-control boundary. Token permissions can change without removing an existing cached repository.

## Disk and memory

`.cache/` contains bare Git repositories and transient download/helper directories. It may include private history or blobs if the host ignores partial-clone filtering. The application requests private directory permissions on POSIX; platform filesystem/account permissions still govern access. Keep the directory out of source control and shared storage.

Stop the application before deleting `.cache/`. Restarting clears reports in memory. Retention cleanup happens when a new analysis starts: completed jobs older than one hour are removed, and older completed results are trimmed to keep approximately 20. Running work is not evicted. The cache has no automatic disk-size limit or expiry.

## Network and application boundaries

Only HTTPS port 443 is supported for repository access. Private, loopback, and non-global resolved host addresses are rejected. Git and metadata redirects are disabled. DNS checks are **not** hardened against rebinding or every proxy/network configuration; analyze only trusted hosts. Proxy environment variables may still affect outbound requests.

The server checks Host and Origin, requires JSON for POSTs, limits request bodies, sends a restrictive content security policy, and serves only explicit static routes. These are defense-in-depth measures, not authentication. Do not expose the service beyond localhost or use it as a public multi-user system.

Git hooks and user/global Git configuration are ignored for remote operations. External repository text is escaped before rendering, and CSV cells receive formula-injection protection. No code or hooks from the analyzed repository are intentionally executed.

## Sharing results

CSV and screenshots can reveal project names, contributor display names, timing, and activity levels. Review them before sharing. The bundled screenshot is generated from synthetic data and contains no real accounts, credentials, or repository activity. Follow [SECURITY.md](../SECURITY.md) for vulnerability reports.
