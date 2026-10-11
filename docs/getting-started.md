# Getting started

## Requirements

- Python **3.10+** available as `python`, `python3`, or Windows `py`.
- Git **2.27+** on `PATH`.
- A current browser with JavaScript enabled.
- Internet access for repository analysis; the initial demo and interface work offline.

The application uses Python’s standard library and native browser features. A virtual environment, Node.js, and package installation are not required for normal use.

## Install and run

Download the project source or a source release, extract it, and open a terminal in the directory containing `app.py`.

```bash
python app.py --open
```

If needed, replace `python` with `python3` on macOS/Linux or `py` on Windows. Open `http://localhost:8080` manually if automatic opening is unavailable.

### Command-line options

| Option          | Default | Meaning                                         |
| --------------- | ------- | ----------------------------------------------- |
| `--port NUMBER` | `8080`  | Local HTTP port; `0` requests an available port |
| `--open`        | Off     | Open the dashboard using the system browser     |
| `--help`        | —       | Show command-line help                          |

The bind address is intentionally fixed to `127.0.0.1`. A usable port is a number from 1 to 65535, or 0 for automatic allocation.

## First analysis

1. Paste the main HTTPS page of a GitHub or GitLab repository, not a branch or file URL.
2. For a private repository, open **Access & options** and provide a read-only token.
3. Select **Analyze repository** and wait for the history download.
4. Explore views, change date ranges/grouping, and export the current view as CSV.

Repository URLs may omit `https://` or end in `.git`. GitLab nested namespaces are supported. Public self-hosted GitLab hosts must use HTTPS port 443 and resolve to public addresses.

## Platforms

The app is designed for Linux, macOS, and Windows with Git installed. Windows Git must provide its normal shell environment for the temporary askpass helper. Git credential prompting is disabled; use the token field rather than an interactive login.

Developer CI exercises Python tests on all three operating systems. Browser checks run with Chromium on Linux; this is not a claim that every browser/platform combination has been manually certified.

## Stop, upgrade, and local data

Stop with Ctrl+C. An in-progress Git operation may need to finish before shutdown completes. Replacing the source with a newer version updates the application; preserve `.cache/` only if you want to reuse downloaded history.

To remove cached data, stop the app and delete only its `.cache/` directory using your file manager. Do not upload that directory. Restarting clears in-memory reports but not the disk cache.
