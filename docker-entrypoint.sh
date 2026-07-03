#!/bin/sh
set -e

python - <<'PY'
import os
import sys
import time
from urllib.parse import urlparse

import pymysql

database_url = os.environ["DATABASE_URL"]
parsed = urlparse(database_url)
database = parsed.path.lstrip("/")

for attempt in range(1, 61):
    try:
        connection = pymysql.connect(
            host=parsed.hostname,
            port=parsed.port or 3306,
            user=parsed.username,
            password=parsed.password,
            database=database,
            connect_timeout=3,
        )
        connection.close()
        break
    except Exception as exc:
        print(f"Waiting for MySQL ({attempt}/60): {exc}", flush=True)
        time.sleep(2)
else:
    sys.exit("MySQL did not become available.")
PY

alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
