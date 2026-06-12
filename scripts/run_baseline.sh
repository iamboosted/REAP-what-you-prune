#!/bin/bash
# Stage 1/2 baseline pass: builds llama.cpp, downloads GLM-4.7-Flash Q8_0,
# and writes full-vocab baseline logits for KL-divergence comparison.
#
# Requirements: CUDA GPU with 40GB+ VRAM (Q8 is ~32GB), ~50GB free disk
# for the model + ~15GB for the logits file. Run under nohup or tmux:
#   nohup ./run_baseline.sh > baseline.log 2>&1 &
#
# On a 24GB card instead: add `--cpu-moe` to the llama-perplexity line
# (parks the MoE experts in system RAM; needs ~40GB RAM, runs slower).

set -e

# --- one-time deps (skip if already present) ---
apt-get update && apt-get install -y cmake
pip install -U "huggingface_hub[hf_transfer]"
export HF_HUB_ENABLE_HF_TRANSFER=1

# --- build llama.cpp ---
cd /workspace
if [ ! -d llama.cpp ]; then git clone --depth 1 https://github.com/ggml-org/llama.cpp; fi
cd llama.cpp
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=native
cmake --build build -j $(nproc) --target llama-perplexity llama-server

# --- eval corpus ---
if [ ! -f wikitext-2-raw/wiki.test.raw ]; then bash scripts/get-wikitext-2.sh; fi

# --- baseline model (~32GB) ---
hf download unsloth/GLM-4.7-Flash-GGUF --include "*Q8_0*" --local-dir /workspace/models/flash-q8

MODEL=$(find /workspace/models/flash-q8 -name "*.gguf" | sort | head -n 1)
echo "Baseline model: $MODEL"

# --- write baseline logits (~15GB for 200 chunks at GLM's ~151k vocab) ---
./build/bin/llama-perplexity \
  -m "$MODEL" \
  -f wikitext-2-raw/wiki.test.raw \
  -ngl 999 \
  --chunks 200 \
  --kl-divergence-base /workspace/glm_base.kld
