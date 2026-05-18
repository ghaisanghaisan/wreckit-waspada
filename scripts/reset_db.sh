#!/usr/bin/env bash
set -euo pipefail

# Reset the PostgreSQL database by dropping all tables in the public schema
# and re-applying the `database/init.sql` schema script.
#
# Usage:
#   ./scripts/reset_db.sh
# or set environment variables to override defaults:
#   POSTGRES_USER POSTGRES_PASSWORD POSTGRES_HOST POSTGRES_PORT POSTGRES_DB

DB_USER=${POSTGRES_USER:-postgres}
DB_PASS=${POSTGRES_PASSWORD:-gulingkanan}
DB_HOST=${POSTGRES_HOST:-localhost}
DB_PORT=${POSTGRES_PORT:-5432}
DB_NAME=${POSTGRES_DB:-waspada}

DB_DSN="postgresql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

echo "Using DSN: $DB_DSN"

if ! command -v psql >/dev/null 2>&1; then
  echo "Error: psql is not installed or not in PATH" >&2
  exit 2
fi

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
INIT_SQL="$SCRIPT_DIR/database/init.sql"

if [ ! -f "$INIT_SQL" ]; then
  echo "Error: init.sql not found at $INIT_SQL" >&2
  exit 1
fi

echo "Dropping all tables in public schema..."
psql "$DB_DSN" -v ON_ERROR_STOP=1 <<'PSQL'
DO $$ DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
END $$;
PSQL

echo "Reinitializing database from $INIT_SQL..."
psql "$DB_DSN" -v ON_ERROR_STOP=1 -f "$INIT_SQL"

echo "Database reset complete."
