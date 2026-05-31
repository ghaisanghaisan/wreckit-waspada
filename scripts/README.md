# Scripts

## Register organization

Registers or updates an organization plus its tenant configuration.

```bash
/home/ghaisan/projects/wreckit-waspada/.venv/bin/python /home/ghaisan/projects/wreckit-waspada/scripts/register_organization.py \
  --name "Org Alpha" \
  --keywords "Polri,Polda Metro Jaya" \
  --keywords "Bareskrim,Kapolri" \
  --contexts "performa polisi,prestasi polisi" \
  --contexts "opini publik terhadap polisi"
```

### Options

- `--name`: Organization name (required).
- `--keywords`: Comma-separated keywords (repeatable, required).
- `--contexts`: Comma-separated sentiment contexts (repeatable, required).
- `--dsn`: Optional PostgreSQL DSN (overrides environment defaults).

### Environment variables

If `--dsn` is not provided, the script uses:

- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `DATABASE_URL` (optional shortcut)
