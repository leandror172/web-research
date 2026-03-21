#!/usr/bin/env bash
# Extraction model benchmark: 7 models × 2 tasks (open + focused)
set -e

URL="https://crawl4ai.com"
FOCUS="installation and quickstart"
MODELS=(
    "qwen2.5-coder:14b"
    "qwen3:14b"
    "qwen3:8b"
    "qwen3.5:9b"
    "deepseek-r1:14b"
    "deepseek-coder-v2:16b"
    "qwen3:30b-a3b"
)

for model in "${MODELS[@]}"; do
    echo ""
    echo "########## $model — OPEN ##########"
    uv run python -m spike.extract "$URL" --model "$model" 2>&1 || echo "FAILED: $model open"

    echo ""
    echo "########## $model — FOCUSED ##########"
    uv run python -m spike.extract "$URL" --model "$model" \
        --prompt-type focused --focus "$FOCUS" 2>&1 || echo "FAILED: $model focused"
done

echo ""
echo "========== BENCHMARK COMPLETE =========="
ls -la spike/output/*.json 2>/dev/null | wc -l
echo "JSON files generated"
