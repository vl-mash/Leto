# hooks/

Only one helper is live in v2. The v1 hooks (preflight, standing approvals, learning loop, fact-freshen, cost tracking, doubt-stop) were retired on 2026-10-26 and are in `archive/v1/hooks/`, along with their old README.

## `leto_secrets.py`: one env file for every credential, plus live validation

Every Leto secret lives in `~/.config/leto/leto.env` (mode 600), outside any git work tree. The template and where each key comes from: `../.env.example`.

```bash
python3 hooks/leto_secrets.py --check    # live-probe every credential; exit 1 on failure
python3 hooks/leto_secrets.py --names    # which key resolves from where (never values)
bash scripts/migrate-secrets.sh          # consolidate legacy single-value files
```

Resolution order: environment variable → `leto.env` → legacy `~/.config/leto/<name>` file. Probes: Linear `viewer` · Slack `auth.test` (bot + user) · YouTrack `/users/me`. Transport is `curl`, with config on stdin so tokens never reach argv. This host's `python3` has no system CA bundle. Importable: `from leto_secrets import get, load_env`.
