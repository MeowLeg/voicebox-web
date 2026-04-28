#!/bin/bash
cd /mnt/d/Github/voicebox-web/auth_backend
rm -f auth.db
export PYTHONPATH=/mnt/d/Github/voicebox-web/auth_backend
exec python -m uvicorn main:app --port 17494 --host 0.0.0.0
