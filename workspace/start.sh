#!/usr/bin/env bash
# 一键启动：PostgreSQL + Django(8000) + Vite(5173)
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"

# 1. PostgreSQL（首次运行先初始化）
if [ ! -d "$ROOT/pgdata" ]; then
  "$ROOT/pgenv/bin/initdb" -D "$ROOT/pgdata" -U postgres --encoding=UTF8
fi
"$ROOT/pgenv/bin/pg_ctl" -D "$ROOT/pgdata" -l "$ROOT/pgdata.log" -o "-p 5432 -k /tmp" -w start || true
sleep 1
"$ROOT/pgenv/bin/psql" -h /tmp -p 5432 -U postgres -tc "SELECT 1 FROM pg_database WHERE datname='dyeing_db'" | grep -q 1 \
  || "$ROOT/pgenv/bin/psql" -h /tmp -p 5432 -U postgres -c "CREATE DATABASE dyeing_db"

# 2. Django 迁移 + 样例数据 + 启动
cd "$ROOT/backend"
"$ROOT/.venv/bin/python" manage.py migrate
if [ "$1" = "--seed" ]; then
  "$ROOT/.venv/bin/python" manage.py seed
fi
"$ROOT/.venv/bin/python" manage.py runserver 0.0.0.0:8000 &
DJANGO_PID=$!

# 3. 前端
cd "$ROOT/frontend"
npm run dev &
VITE_PID=$!

trap "kill $DJANGO_PID $VITE_PID 2>/dev/null" EXIT
echo "后端: http://localhost:8000  前端: http://localhost:5173"
wait
