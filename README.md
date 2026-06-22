# RAG Debug Assistant Demo YAMLs

This package gives you a clean on-prem demo shape:

- Jira replacement: local YAML bug reports under `bugs/`
- P4 replacement: local Git repo under `repos/simulator-core`
- DB: Postgres + pgvector
- LLM host: Ollama
- Backend placeholder: FastAPI mounted at `app/`

## Run

```bash
docker compose up -d postgres ollama
```

For fastest Mac inference, install Ollama natively instead of Docker Ollama, then point backend to `http://host.docker.internal:11434`.

## Pull model

```bash
ollama pull llama3.1:8b
```

## Next files to add

- `app/main.py`
- ingestion script for `bugs/*.yaml`
- Git diff ingestion from `repos/simulator-core`
- retrieval API
