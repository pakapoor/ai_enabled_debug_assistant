docker exec -it rag-demo-postgres psql -U raguser -d ragdemo -c "SELECT COUNT(*) FROM chunks;"
