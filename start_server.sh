fuser -k 8001/tcp
uvicorn hybrid_api:app --host 0.0.0.0 --port 8001
