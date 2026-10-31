# Development Workflow

## Environment Setup with uv
This project requires Python 3.12+ and `uv`.

### 1. Install Dependencies
```bash
uv sync
```

### 2. Configure Environment Secrets
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Ensure `WEBHOOK_API_KEY` matches what you set up in your ThingsBoard Rule Engine or local test scripts.

### 3. Run Development Server
```bash
uv run uvicorn app.main:app --reload --port 8000
```
- Interactive API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Alternative Redoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 4. Running Tests & Linting
```bash
# Run unit & integration tests
uv run pytest

# Check code formatting and linting
uv run ruff check .
```
