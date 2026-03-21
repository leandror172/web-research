#!/usr/bin/env bash
# Full extraction benchmark: 6 models × 4 URLs × 2 tasks = 48 runs
# Excludes qwen3.5:9b (failed on all prior tests)
set -e

FOCUS="installation and quickstart"
MODELS=(
    "qwen2.5-coder:14b"
    "qwen3:14b"
    "qwen3:8b"
    "deepseek-r1:14b"
    "deepseek-coder-v2:16b"
    "qwen3:30b-a3b"
)

URLS=(
    "https://modelcontextprotocol.io/llms-full.txt"
    "https://huggingface.co/"
    "https://en.wikipedia.org/wiki/Large_language_model"
    "https://htmx.org/"
)

total=$((${#MODELS[@]} * ${#URLS[@]} * 2))
count=0

for url in "${URLS[@]}"; do
    echo ""
    echo "================================================================"
    echo "URL: $url"
    echo "================================================================"

    for model in "${MODELS[@]}"; do
        count=$((count + 1))
        echo ""
        echo "[$count/$total] $model — OPEN — $url"
        uv run python -m spike.extract "$url" --model "$model" 2>&1 || echo "FAILED: $model open $url"

        count=$((count + 1))
        echo ""
        echo "[$count/$total] $model — FOCUSED — $url"
        uv run python -m spike.extract "$url" --model "$model" \
            --prompt-type focused --focus "$FOCUS" 2>&1 || echo "FAILED: $model focused $url"
    done
done

echo ""
echo "========== BENCHMARK COMPLETE =========="
echo "JSON files generated:"
ls spike/output/*.json 2>/dev/null | wc -l
echo ""
echo "=== TIMING SUMMARY ==="
for f in spike/output/*-extracted.json; do
    python3 -c "
import json
d = json.load(open('$f'))
m = d['model']
pt = d.get('prompt_type','?')
dur = d['duration_seconds']
feats = len(d['data'].get('key_features', d['data'].get('relevant_facts', [])))
name = d['data'].get('name', '?')
print(f'{m:30s} {pt:8s} {dur:6.1f}s  items={feats}  name={name[:40]}')
" 2>/dev/null || true
done
