#!/bin/bash
set -e

OLLAMA_HOST="${OLLAMA_BASE_URL:-http://localhost:11434}"
MODEL_NAME="${OLLAMA_MODEL:-llama3.2}"

echo "Waiting for Ollama at $OLLAMA_HOST..."
until curl -s "$OLLAMA_HOST/api/version" > /dev/null; do
  echo "Ollama not ready, retrying in 2s..."
  sleep 2
done

echo "Checking if model '$MODEL_NAME' exists..."
if curl -s "$OLLAMA_HOST/api/tags" | grep -q "\"$MODEL_NAME\""; then
  echo "Model '$MODEL_NAME' already exists."
else
  echo "Model '$MODEL_NAME' not found. Pulling..."
  curl -X POST "$OLLAMA_HOST/api/pull" -d "{\"name\": \"$MODEL_NAME\"}"
  echo "Model '$MODEL_NAME' pulled successfully."
fi
