# Smart ERP — Command Reference

## Quick Start

```bash
./scripts/smart-erp.sh up       # Start all services (default mode)
./scripts/smart-erp.sh dev      # Start with hot-reload (recommended for development)
```

Web UI: `http://erpnext.localhost:8080` — Login: `Administrator` / `admin`

---

## Restart & Stop

| Command | Description |
|---|---|
| `./scripts/smart-erp.sh restart` | Restart all containers + re-apply fixes |
| `./scripts/smart-erp.sh stop` | Stop containers (keep state) |
| `./scripts/smart-erp.sh down` | Stop & remove containers (data persists in volumes) |
| `./scripts/smart-erp.sh ps` | Show running container status |

## Applying Codebase Changes

### Python changes (`.py` files in `smart_erp_ai/`)

**Dev mode (recommended):** `smart_erp_ai` is bind-mounted, gunicorn auto-reloads on save.
```bash
./scripts/smart-erp.sh dev          # Start dev mode with auto-reload
```

**Default mode:** Restart backend to pick up changes.
```bash
./scripts/smart-erp.sh restart
```

### Template / HTML changes (`www/`, `templates/`)

Clear Frappe's cache so the new templates are served:
```bash
./scripts/smart-erp.sh bench clear-cache
```

Or in dev mode, templates are served fresh (developer_mode = 1).

### DocType changes (`.json` in `doctype/`)

Run migration to apply schema changes:
```bash
./scripts/smart-erp.sh migrate
```

### Frappe / ERPNext submodule changes (apps/frappe, apps/erpnext)

Rebuild the Docker image (these are baked in, not bind-mounted):
```bash
./scripts/smart-erp.sh build
./scripts/smart-erp.sh up
```

### Frontend asset changes (JS/CSS in `public/`)

In dev mode, esbuild watches and rebuilds automatically — just refresh the browser.

In default mode, rebuild assets:
```bash
./scripts/smart-erp.sh bench build --app smart_erp_ai
./scripts/smart-erp.sh restart
```

### When things break (DB connection, missing app, stale assets)

```bash
./scripts/smart-erp.sh fix            # Re-apply DB grant + assets manifest + app registration
./scripts/smart-erp.sh bench clear-cache   # Clear Frappe cache
```

---

## Full Command List

| Command | Description |
|---|---|
| `./scripts/smart-erp.sh up` | Start all services |
| `./scripts/smart-erp.sh down` | Stop & remove containers |
| `./scripts/smart-erp.sh stop` | Stop containers |
| `./scripts/smart-erp.sh restart` | Restart all services + re-apply fixes |
| `./scripts/smart-erp.sh ps` | Show container status |
| `./scripts/smart-erp.sh logs [svc]` | Tail logs (default: backend) |
| `./scripts/smart-erp.sh build` | Rebuild Docker image from source |
| `./scripts/smart-erp.sh fix` | Re-apply DB grant + assets + app registration |
| `./scripts/smart-erp.sh shell` | Bash inside backend container |
| `./scripts/smart-erp.sh bench <args>` | Run any bench command on the site |
| `./scripts/smart-erp.sh migrate` | `bench --site <site> migrate` |
| `./scripts/smart-erp.sh backup` | `bench --site <site> backup` |
| `./scripts/smart-erp.sh db` | MariaDB root shell |

### Dev Mode (hot-reload)

| Command | Description |
|---|---|
| `./scripts/smart-erp.sh dev` | Start with live reload (Python + frontend) |
| `./scripts/smart-erp.sh dev-down` | Stop dev-mode stack |
| `./scripts/smart-erp.sh dev-logs [svc]` | Tail watcher logs (default: watch) |
| `./scripts/smart-erp.sh dev-fix` | Re-enable developer_mode |

### L2 Analytics Demo (Smart ERP AI)

| Command | Description |
|---|---|
| `./scripts/smart-erp.sh seed [N]` | Seed N dummy P2P cases (default 300) |
| `./scripts/smart-erp.sh reseed` | Delete seed batch |
| `./scripts/smart-erp.sh demo` | Run F1/F2/F3/F7 analytics demo |

---

## Common Scenarios

**"I edited a Python file in smart_erp_ai and changes don't show up"**
```bash
./scripts/smart-erp.sh dev          # Switch to dev mode for auto-reload
# OR
./scripts/smart-erp.sh restart      # Restart in default mode
./scripts/smart-erp.sh bench clear-cache
```

**"I edited chat.html and the page didn't change"**
```bash
./scripts/smart-erp.sh bench clear-cache
# Then hard-refresh browser (Ctrl+Shift+R)
```

**"I changed a DocType JSON"**
```bash
./scripts/smart-erp.sh migrate
./scripts/smart-erp.sh bench clear-cache
```

**"I changed hooks.py"**
```bash
./scripts/smart-erp.sh restart
./scripts/smart-erp.sh bench clear-cache
```

**"Complete reset (keep DB data)"**
```bash
./scripts/smart-erp.sh down
./scripts/smart-erp.sh up
./scripts/smart-erp.sh fix
```

**"Run a bench command directly"**
```bash
./scripts/smart-erp.sh bench console
./scripts/smart-erp.sh bench --version
./scripts/smart-erp.sh bench execute smart_erp_ai.scripts.seed_demo_data.run
```
