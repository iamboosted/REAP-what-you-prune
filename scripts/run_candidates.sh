#!/bin/bash
# Stage 1/2 candidate runs: downloads the three GLM candidate quants and
# computes KL-divergence for each against the baseline logits written by
# run_baseline.sh. Per-candidate summaries land in /workspace/kld_<name>.txt.
#
# Run under nohup or tmux:
#   nohup ./run_candidates.sh > candidates.log 2>&1 &

set -e
export HF_HUB_ENABLE_HF_TRANSFER=1
cd /workspace/llama.cpp

hf download unsloth/GLM-4.7-Flash-GGUF --include "*UD-Q4_K_XL*" --local-dir /workspace/models/flash-q4
hf download unsloth/GLM-4.7-Flash-REAP-23B-A3B-GGUF --include "*UD-Q4_K_XL*" --local-dir /workspace/models/reap-q4kxl
hf download unsloth/GLM-4.7-Flash-REAP-23B-A3B-GGUF --include "*IQ4_XS*" --local-dir /workspace/models/reap-iq4xs

for name in flash-q4 reap-q4kxl reap-iq4xs; do
  M=$(find /workspace/models/$name -name "*.gguf" | sort | head -n 1)
  if [ -z "$M" ]; then echo "ERROR: no gguf found for $name - quant name mismatch in repo"; exit 1; fi
  echo "=== KLD run: $name -> $M ==="
  ./build/bin/llama-perplexity \
    -m "$M" \
    -f wikitext-2-raw/wiki.test.raw \
    -ngl 999 --chunks 200 \
    --kl-divergence-base /workspace/glm_base.kld --kl-divergence \
    2>&1 | tee /workspace/kld_$name.txt
done
echo "ALL DONE"
