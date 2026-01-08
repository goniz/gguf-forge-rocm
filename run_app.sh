#!/bin/bash
set -e

source venv/bin/activate
uv sync

uv run python app_gguf.py
