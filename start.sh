#!/bin/bash
# start.sh — starts both FastAPI backend and React frontend
# Usage: bash start.sh

echo "Starting ResumeIQ..."

# 1. Start FastAPI backend in background
echo "  -> Starting FastAPI on http://localhost:8000"
cd "$(dirname "$0")"
source venv/bin/activate 2>/dev/null || true
uvicorn app.api:app --reload --port 8000 &
BACKEND_PID=$!

# 2. Start React frontend
echo "  -> Starting React on http://localhost:5173"
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "Both servers are running:"
echo "   Frontend -> http://localhost:5173"
echo "   Backend  -> http://localhost:8000"
echo "   API Docs -> http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Stopped.'" EXIT
wait
