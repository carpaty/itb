# AGENTS.md

Guidance for AI coding agents (and humans) working on this repository.

## Project

Infratrix Telegram Bot (ITB): a monitoring bot built on
[python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) v22 and FastAPI,
deployed to Google App Engine standard (`python312`) with Datastore as storage.
Telegram delivers updates through a webhook; App Engine cron calls `/cron` every 10 minutes to
run the site/host monitor.

## Layout

| Path | Purpose |
| --- | --- |
| `src/main.py` | FastAPI app, webhook, `/tg` API, `/cron`, handler registration |
| `src/commands.py` | `/start`, `/help`, reply keyboard and free-text routing |
| `src/menu.py` | Builds keyboards from `menu.yaml` |
| `src/utils.py` | Config loading, shared bot, state helpers, API keys |
| `src/db.py` | Datastore access (`Users`, `Position` kinds), shared lazy client |
| `src/netutils.py` | SSRF-safe network helpers: target validation, port scan, HTTP and TLS checks |
| `src/calls/button_func.py.example` | Tool implementations (copied to `button_func.py`, git-ignored) |
| `src/menu.yaml.example` | Menu definition (copied to `menu.yaml`, git-ignored) |
| `tests/` | pytest suite; no network or GCP credentials required |

## Setup and checks

```bash
python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
cp src/menu.yaml.example src/menu.yaml
cp src/calls/button_func.py.example src/calls/button_func.py

pylint $(git ls-files '*.py' '*.py.example')
pycodestyle --count --max-line-length=120 $(git ls-files '*.py' '*.py.example')
pytest
```

CI (`.github/workflows/main.yaml`) runs the same three checks; deploys from `main` only run after
they pass. Keep pylint at 10/10 and lines at most 120 characters.

Edit the `.example` files, not the copied `menu.yaml` / `button_func.py`: only the examples are
tracked and deployed by CI.

## Adding a tool

1. Add an entry with `name`, `call` and `desc` to `src/menu.yaml.example`.
2. Implement `call` in `src/calls/button_func.py.example` as `(uid, data) -> (text, reply_markup)`;
   it may be `async`. Blocking I/O must run through `asyncio.to_thread`.
3. For Yes/No flows use `confirm(uid, action, data, text)` and register the confirmed handler in
   `CONFIRM_ACTIONS`. Never put user input into `callback_data` (64 byte limit, client controlled).
4. Add tests under `tests/`.

## Security rules

- Every user-supplied host or URL must go through `netutils` (`resolve_public`, `check_url`,
  `scan_ports`, `certificate_info`) so internal and metadata addresses stay unreachable.
- Keep the port limit (`netutils.MAX_PORTS`) and per-user item limit (`MAX_ITEMS_PER_USER`).
- `/webhook` must verify `X-Telegram-Bot-Api-Secret-Token`; `/cron` must require the
  `X-Appengine-Cron` header; `/tg` must validate its body and return 403 for unknown keys.
- Load YAML with `yaml.safe_load` only. Never log tokens, API keys or message bodies at INFO level.
- Secrets come from environment variables (`TELEGRAM_TOKEN`, `TELEGRAM_WEBHOOK_URL`, optional
  `TELEGRAM_WEBHOOK_SECRET`); never commit `app.yaml`.

## Dependencies

All runtime dependencies are pinned in `requirements.txt`; dev tools in `requirements-dev.txt`.
Bump versions deliberately and run the full check suite afterwards.
