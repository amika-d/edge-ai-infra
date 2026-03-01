#!/bin/sh

MODEL_PATH="/models/${MODEL_ID}"

SERVED_MODEL="${SERVED_MODEL:-qwen-7b}"
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.80}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-2048}"

echo "Starting Edge AI Node..."
echo "Model Path: ${MODEL_PATH}"
echo "Served As: ${SERVED_MODEL}"
echo "Context Window: ${MAX_MODEL_LEN}"
echo "GPU Utilization: ${GPU_MEMORY_UTILIZATION}"

if [ ! -d "$MODEL_PATH" ]; then
  echo "Model not found at ${MODEL_PATH}"
  echo "Run: python scripts/download_model.py"
  exit 1
fi

echo "Model found. Launching vLLM..."

exec python3 -m vllm.entrypoints.openai.api_server \
  --model "${MODEL_PATH}" \
  --served-model-name "${SERVED_MODEL}" \
  --host 0.0.0.0 \
  --port 8000 \
  --gpu-memory-utilization "${GPU_MEMORY_UTILIZATION}" \
  --max-model-len "${MAX_MODEL_LEN}" \
  --enforce-eager
