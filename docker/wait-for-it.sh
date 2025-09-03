#!/usr/bin/env bash
host=$(echo $1 | cut -d: -f1)
port=$(echo $1 | cut -d: -f2)
shift
cmd="$@"

echo "Waiting for $host:$port to be ready..."

until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$host" -U "$POSTGRES_USER" -p "$port" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; do
  echo "Postgres is unavailable - sleeping"
  sleep 2
done

echo "Postgres is up - executing command"
exec $cmd
