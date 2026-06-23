#!/bin/bash

echo "Starting Debug Assistant..."

# Start Postgres
echo "[1/4] Starting Postgres..."
docker compose up -d postgres

# Wait for Postgres to be healthy
echo "Waiting for Postgres to be ready..."
until docker exec rag-demo-postgres pg_isready -U raguser -d ragdemo > /dev/null 2>&1; do
  sleep 1
done
echo "Postgres ready."

# Kill anything on ports 8001 and 8002
fuser -k 8001/tcp 2>/dev/null
fuser -k 8002/tcp 2>/dev/null

# Start hybrid search API on port 8001
echo "[2/4] Starting hybrid search API on port 8001..."
uvicorn hybrid_api:app --host 0.0.0.0 --port 8001 &
sleep 2

# Start answer API on port 8002
echo "[3/4] Starting answer API on port 8002..."
uvicorn answer_api:app --host 0.0.0.0 --port 8002 &
sleep 2

# Start React UI
echo "[4/4] Starting React UI on port 3000..."
cd debug-assistant-ui && npm start &

echo ""
echo "All services started!"
echo "  Hybrid search API: http://localhost:8001"
echo "  Answer API:        http://localhost:8002"
echo "  React UI:          http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services."

wait
