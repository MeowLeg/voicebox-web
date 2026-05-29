#!/bin/bash
PORT=17494
PID=$(lsof -ti tcp:"$PORT" 2>/dev/null)

if [ -n "$PID" ]; then
  echo "Killing auth_backend (PID $PID) on port $PORT..."
  kill "$PID"
  echo "Stopped."
else
  echo "No auth_backend process found on port $PORT."
fi
