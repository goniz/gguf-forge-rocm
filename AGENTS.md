# AGENTS.md - Coding Agent Instructions for GGUF Forge

## Project Overview

**GGUF Forge** is a FastAPI-based web application for automated conversion of HuggingFace models to GGUF format using llama.cpp. The application features OAuth authentication, request/approval workflows, real-time WebSocket updates, and multi-database support (SQLite/MSSQL).

**Tech Stack:** Python 3.10+, FastAPI, async/await, Jinja2, WebSockets, SQLite/MSSQL

## Build, Lint, and Test Commands

### Running the Application
```bash
# Development mode
python app_gguf.py

# Production with uvicorn
uvicorn app_gguf:app --host 0.0.0.0 --port 8000

# With custom port
PORT=8080 python app_gguf.py
```

### Building Executable
```bash
# Build standalone executable with PyInstaller
python build.py

# Manual PyInstaller command
pyinstaller --noconfirm --onefile --name GGUF-Forge \
  --add-data "templates;templates" \
  --hidden-import passlib.handlers.argon2 \
  --hidden-import argon2-cffi \
  --hidden-import uvicorn \
  --hidden-import python_multipart \
  --clean app_gguf.py
```

### Testing
**Note:** No testing framework currently configured. To add tests:
```bash
# Install pytest and dependencies
pip install pytest pytest-asyncio httpx

# Run all tests (once implemented)
pytest

# Run specific test file
pytest tests/test_workflow.py -v

# Run specific test function
pytest tests/test_workflow.py::test_download_model -v

# Run tests matching pattern
pytest -k "test_auth" -v

# Run with coverage
pytest --cov=. --cov-report=html
```

### Linting and Formatting
**Note:** No linting/formatting tools currently configured. Recommended setup:
```bash
# Install tools
pip install black flake8 isort mypy ruff

# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .
# or use ruff (faster alternative)
ruff check .

# Type checking
mypy .
```

## Code Style Guidelines

### Imports
- Group imports in order: stdlib, third-party, local
- Use absolute imports for local modules
- Alphabetize within groups
```python
# Standard library
import os
import sys
from pathlib import Path

# Third-party
from fastapi import FastAPI, Request
from huggingface_hub import HfApi

# Local
from database import Database
from models import ConversionRequest
```

### Formatting
- **Line length:** ~100-120 characters (flexible)
- **String quotes:** Double quotes for strings, single quotes for dict keys
- **Indentation:** 4 spaces (no tabs)
- **Blank lines:** 2 between top-level functions/classes, 1 within functions

### Type Hints
- Add type hints for function parameters and return values
- Use `Optional[T]` for nullable values
- Use `Dict`, `List`, `Tuple` from `typing` module
```python
from typing import Optional, List, Dict

async def get_user_requests(user_id: str, limit: int = 10) -> List[Dict[str, any]]:
    """Fetch user requests from database."""
    pass
```

### Naming Conventions
- **Functions/variables:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `UPPER_CASE`
- **Private functions/methods:** `_leading_underscore`
- **Async functions:** Prefix with `async_` if ambiguous, otherwise use `async def` keyword
```python
MAX_RETRIES = 3

class ModelConverter:
    def _prepare_workspace(self):
        pass
    
    async def download_model(self, model_id: str) -> Path:
        pass
```

### Docstrings
- Use module-level docstrings for all files
- Use triple double-quotes `"""`
- Follow Google or NumPy style for complex functions
```python
"""
Module for managing model conversion workflows.
Handles download, conversion, quantization, and upload.
"""

async def convert_model(model_id: str, output_dir: Path) -> bool:
    """
    Convert a HuggingFace model to GGUF format.
    
    Args:
        model_id: HuggingFace model identifier (e.g., 'meta-llama/Llama-2-7b')
        output_dir: Directory to save converted model
    
    Returns:
        True if conversion successful, False otherwise
    """
    pass
```

### Async/Await Patterns
- Use `async def` for all I/O-bound operations (database, HTTP, file operations)
- Always `await` async functions
- Use `asyncio.gather()` for parallel async operations
- Use async context managers with `async with`
```python
async def process_request(request_id: int):
    # Parallel operations
    model_data, user_data = await asyncio.gather(
        db.get_model(model_id),
        db.get_user(user_id)
    )
    
    # Async context manager
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
```

### Error Handling
- Use specific exception types
- Log errors with context
- Return meaningful error responses
- Use `HTTPException` for API errors
```python
from fastapi import HTTPException

async def approve_request(request_id: int):
    try:
        request = await db.get_request(request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        await process_conversion(request)
    except Exception as e:
        logger.error(f"Failed to approve request {request_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### Comments
- Use inline comments for complex logic
- Use section separators for logical blocks
```python
# --- Setup conversion environment ---
workspace = Path(f".cache/{model_id}")
workspace.mkdir(parents=True, exist_ok=True)

# Calculate required disk space (model size + 20% buffer)
required_space = model_size * 1.2
```

## Project Structure

```
automaticConversion/
├── app_gguf.py          # Main FastAPI application entry point
├── database.py          # Database abstraction (SQLite + MSSQL)
├── security.py          # Rate limiting, bot detection, spam protection
├── models.py            # Pydantic request/response models
├── managers.py          # LlamaCpp and HuggingFace managers
├── workflow.py          # Model conversion pipeline
├── websocket_manager.py # Real-time WebSocket updates
├── routes/              # API route modules
│   ├── auth.py         # Authentication (admin login + HF OAuth)
│   ├── models.py       # Model processing endpoints
│   ├── requests.py     # User request system endpoints
│   └── tickets.py      # Discussion/ticket system endpoints
├── static/              # Static assets (images, JS)
├── templates/           # Jinja2 HTML templates
└── requirements.txt     # Python dependencies
```

## Architecture Patterns

### Dependency Injection
Routes use FastAPI dependency injection for database and managers:
```python
from fastapi import Depends

async def get_db():
    return database_instance

@app.get("/models")
async def list_models(db: Database = Depends(get_db)):
    return await db.get_all_models()
```

### Background Tasks
Long-running operations use FastAPI BackgroundTasks:
```python
from fastapi import BackgroundTasks

@app.post("/convert")
async def convert_model(request: ConversionRequest, bg_tasks: BackgroundTasks):
    bg_tasks.add_task(run_conversion, request)
    return {"status": "queued"}
```

### WebSocket Updates
Real-time updates via WebSocket channels:
```python
await websocket_manager.broadcast(f"job:{job_id}", {
    "status": "running",
    "progress": 50
})
```

## Environment Configuration

Required environment variables (see `.env.example`):
- `HF_TOKEN` - HuggingFace API token (required)
- `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`, `OAUTH_REDIRECT_URI` - OAuth config
- `ADMIN_USERS` - Comma-separated admin usernames
- `DB_TYPE` - `sqlite` or `mssql` (default: sqlite)
- `MSSQL_*` - MSSQL connection settings (if using MSSQL)
- `PARALLEL_QUANT_JOBS` - Concurrent quantization jobs (default: 2)
- `LLAMA_CPP_DIR` - Custom llama.cpp location (optional)

## Common Patterns

### Database Operations
```python
# Always use async methods
async with db:
    result = await db.execute("SELECT * FROM requests WHERE id = ?", (request_id,))
    row = await result.fetchone()
```

### HuggingFace Operations
```python
from managers import HuggingFaceManager

hf = HuggingFaceManager(token=hf_token)
model_path = await hf.download_model(model_id, cache_dir=".cache")
await hf.upload_model(local_path, repo_id)
```

### LlamaCpp Operations
```python
from managers import LlamaCppManager

llama = LlamaCppManager(llama_cpp_dir="llama.cpp")
await llama.build()  # Compile llama.cpp
await llama.convert(model_path, output_path)
await llama.quantize(input_path, output_path, quant_type="Q4_K_M")
```

## Testing Guidelines (When Implementing Tests)

### Test Structure
- Place tests in `tests/` directory
- Mirror source structure: `tests/test_workflow.py` for `workflow.py`
- Use `pytest-asyncio` for async tests
- Use `httpx.AsyncClient` for FastAPI endpoint tests

### Async Test Example
```python
import pytest
from httpx import AsyncClient
from app_gguf import app

@pytest.mark.asyncio
async def test_list_models():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/models")
        assert response.status_code == 200
```

## Important Notes

- **First run:** Application creates database and generates admin credentials in `creds.txt`
- **llama.cpp:** Cloned and built automatically on first conversion
- **Security:** Rate limiting and bot detection enabled by default
- **WebSockets:** Connect to `/ws/{channel}` for real-time updates
- **Database:** SQLite by default, MSSQL requires additional setup (see `MSSQL_SETUP.md`)
- **Quantization types:** Q2_K, Q3_K_S, Q3_K_M, Q3_K_L, Q4_K_S, Q4_K_M, Q5_K_S, Q5_K_M, Q6_K, Q8_0, F16, F32

## Resources

- **Main Documentation:** See `README.md` for comprehensive setup and usage
- **MSSQL Setup:** See `MSSQL_SETUP.md` for database configuration
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **llama.cpp:** https://github.com/ggerganov/llama.cpp
