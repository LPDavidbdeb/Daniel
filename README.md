# Daniel

## One-command local development

Start Django and Vite together from the project root:

```bash
python scripts/dev.py
```

Defaults:
- Django: `http://0.0.0.0:8080`
- Vite: `http://localhost:5173`

If your virtual environment is active, the launcher uses `./.venv/bin/python` when available.

### Dry run

```bash
python scripts/dev.py --dry-run
```

### Individual servers

```bash
./.venv/bin/python manage.py runserver 0.0.0.0:8080
cd frontend && npm run dev -- --host 0.0.0.0 --port 5173
```

