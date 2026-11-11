# source local/env.sh after: ollama create status-agent-local -f local/Modelfile
export PROVIDER=openai
export MODEL=status-agent-local
export OPENAI_BASE_URL=http://localhost:11434/v1
# Dummy value for the OpenAI-compatible adapter; this is not a real API key.
export OPENAI_API_KEY=local
export LOCAL_MODEL=1
export PROVIDER_TIMEOUT=300
