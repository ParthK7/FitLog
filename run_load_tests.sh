source ./.env

export DATABASE_URL=$TEST_DB_LINK

echo "Starting FastAPI server with Database url set to test_db"
uvicorn app:app --host 0.0.0.0 --port 8000 &

UVICORN_PID=$!

sleep 5

#start locust
echo "Starting locust tests"
locust -f locustfile.py

echo "Load test finished. Shutting down FastAPI server (PID: $UVICORN_PID)..."
kill $UVICORN_PID

echo "Test run complete."
