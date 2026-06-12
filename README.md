# Does GLM-4.7-Flash (or its REAP-pruned variant) dethrone gpt-oss-20b? A ~$2 eval on a rented GPU

**TL;DR:** No. gpt-oss-20b keeps the belt. The REAP-pruned GLM diverges *massively* from its parent at the token-distribution level (12× the divergence of Q4 quantization alone, different top token on ~31% of positions) — yet ties the full model on actual tasks. Doesn't matter: both GLM variants lost to gpt-oss-20b at equal-or-larger VRAM footprints. Total cost: about two dollars of Runpod time.

---

## The question

My local champion is **gpt-oss-20b** (MXFP4, ~12.8 GB) on a 2×12 GB rig (RTX 3060 + RTX 4070 Super, llama.cpp, `-ctk q8_0 -ctv q8_0`). Two challengers:

- **`unsloth/GLM-4.7-Flash-GGUF`** — full model, 30B-A3B MoE
- **`unsloth/GLM-4.7-Flash-REAP-23B-A3B-GGUF`** — same model with 25% of experts pruned via REAP (Cerebras, [arXiv:2510.13999](https://arxiv.org/abs/2510.13999)). 30B → 23B total params, active stays ~3B. A memory win, not a compute win.

Cerebras claims REAP is "practically lossless." The published evidence for this checkpoint is exactly two benchmarks — HumanEval (94.5 → 95.1) and HumanEval+ (89.0 → 89.0) — run by Cerebras themselves, on the BF16 model, in vLLM. The unsloth repo just mirrors those numbers (confirmed in the repo discussions — unsloth didn't run them). HumanEval is saturated enough that a model can change a third of its token picks and still ace it. So: measure, don't trust.

Three questions:

1. **Quant pick:** within REAP, is IQ4_XS (12.6 GB) as good as UD-Q4_K_XL (14.2 GB)?
2. **Pruning cost:** how much did REAP actually change the model vs full Flash?
3. **The verdict:** does any GLM configuration beat gpt-oss-20b on real tasks?

## Setup

Rented a **Runpod RTX A6000 (48 GB)** at ~$0.36/hr after a community-cloud 3090 and an A40 both flaked. The 48 GB matters: the Q8_0 reference model (~32 GB) runs fully on-GPU, no CPU-expert offload needed. Lessons paid for in restarts:

- Pod volumes die with the pod. Nothing carries over.
- Web terminals silently drop and SIGHUP your jobs. Run everything under `nohup` (or tmux) and watch a log file.
- `-DCMAKE_CUDA_ARCHITECTURES=native` makes the llama.cpp build portable across whatever card you land on.

GLM run requirements throughout (per unsloth's docs): current llama.cpp build (a scoring_func bug was fixed Jan 2026), `--jinja`, repeat-penalty off, **not Ollama**.

## Stage 1+2: KL-divergence instead of perplexity

The original plan was perplexity for the quant pick and KLD for the pruning cost. Collapsed into one KLD pass, because:

- **Perplexity is self-referential and blunt.** A REAP model with pruned-away coding experts can post a lovely wikitext perplexity — wikitext never asks for those experts. Quantization can even *improve* corpus PPL while degrading capability.
- **KLD is relative**, which is the point: it measures how far each candidate's output distribution drifted from a reference ("what the model is supposed to say"). Candidates compared against each other tell you they *differ*, not which one is *wrong* — like judging JPEG compression by comparing two JPEGs.
- **REAP keeps the parent's tokenizer**, so full Flash at high precision is a valid KLD baseline for the REAP quants too. One baseline answers everything. (gpt-oss has a different tokenizer — no PPL/KLD comparison is valid against it. That's what Stage 3 is for.)

**Baseline:** full Flash at **Q8_0** (~32 GB). True BF16 (~60 GB) doesn't fit on a 48 GB card, but Q8's own divergence from BF16 (~0.002–0.004 mean KLD, 99%+ top-token agreement) is an order of magnitude below the Q4-class signal being measured, and it offsets all candidates roughly equally. Measuring centimeters with a ruler that's off by a millimeter.

```bash
# baseline pass: writes full-vocab logits (~15 GB for 200×512-token chunks at GLM's ~151k vocab)
llama-perplexity -m GLM-4.7-Flash-Q8_0.gguf -f wiki.test.raw \
  -ngl 999 --chunks 200 --kl-divergence-base glm_base.kld

# each candidate
llama-perplexity -m <candidate>.gguf -f wiki.test.raw \
  -ngl 999 --chunks 200 --kl-divergence-base glm_base.kld --kl-divergence
```

### Results

| vs Flash-Q8_0 baseline | Median KLD | Same top token | RMS Δp | Mean Δp |
|---|---|---|---|---|
| **Flash UD-Q4_K_XL** (quant loss yardstick) | 0.019 | 90.1 % | 7.0 % | −0.13 % |
| **REAP UD-Q4_K_XL** | 0.235 | 69.3 % | 23.3 % | −7.8 % |
| **REAP IQ4_XS** | 0.233 | 69.5 % | 23.1 % | −8.3 % |

Three findings:

1. **Pruning cost is ~12× quant cost.** REAP picks a different most-likely token than its parent on nearly 1 in 3 positions. Mean Δp of −8% means it systematically strips probability from the tokens the full model wanted, and the tail is ugly: on ~1% of positions, tokens the full model was near-certain about get cratered by −95% or more. In distribution-distance terms, REAP-at-Q4 behaves like the full model quantized to Q2–Q3 territory. "Practically lossless" does not describe this distribution.
2. **The two REAP quants are identical.** 0.233 vs 0.235; 69.5% vs 69.3%. Pruning damage so thoroughly dominates that the extra 1.6 GB of Q4_K_XL buys nothing. Question 1 closed: **IQ4_XS, for free.**
3. **Caveat that turned out to matter:** KLD measures *different*, not necessarily *worse*. Foreshadowing.

## Stage 3: blind hand-graded tasks

Distribution drift is the warning light; tasks are the verdict. Ten prompts — 5 coding (interval merging with edge-case asserts, bug-finding on a booby-trapped snippet, PostgreSQL window-function query with tie handling, bounded-concurrency asyncio, LRU cache from scratch with a self-proving demo) and 5 reasoning (logic grid, rate/work problem with a non-empty starting tank, Bayes with base rates, knights-and-knaves, and an anti-memorization iteration task: the 3n+**5** map, not the famous 3n+1, which has a genuine 8-cycle).

Protocol:

- Three models: gpt-oss-20b (MXFP4), Flash UD-Q4_K_XL, REAP IQ4_XS.
- Each at its **recommended deployment samplers** (gpt-oss: temp 1.0 / top-p 1.0 / top-k 0; GLM: temp 1.0 / top-p 0.95 / min-p 0.01 / repeat-penalty off, `--jinja`) — the question is "which model serves me as deployed," and GLM specifically misbehaves off its recommended settings.
- Models shuffled into **blind labels A/B/C at runtime** by the runner script; the key stayed sealed until all 30 answers were scored.
- Graded against pre-computed answer keys by the same LLM (Claude) that designed the prompts, before unmasking. Every code answer traced by hand, every assert and demo actually checked.

### Results

| | Coding /50 | Reasoning /50 | Total |
|---|---|---|---|
| **gpt-oss-20b** (was "A") | 43 | 49.5 | **92.5** |
| **Flash UD-Q4_K_XL** (was "B") | 37.5 | 49 | **86.5** |
| **REAP IQ4_XS** (was "C") | 38 | 48 | **86** |

All three models swept the reasoning section substantively — every logic puzzle, every calculation, the anti-memorization cycle, all correct, with only presentation nits separating them. **The entire separation came from coding self-verification:**

- **gpt-oss-20b's** one real wound: a correct LRU implementation whose demo comments claim an eviction order the code doesn't produce.
- **Full Flash** wrote an interval-merge assert that fails against its own correct code, and a SQL query with `RANK() OVER` inside a WHERE clause — PostgreSQL rejects it outright. The query doesn't run.
- **REAP** diagnosed both bugs in the bug-finding task, then shipped a "corrected" version that raises `KeyError` on first use. Its SQL runs perfectly and returns every customer of every month — the top-3 filter, the entire point of the prompt, is simply absent.

## Conclusions

**1. gpt-oss-20b retains the title.** The gap wasn't intelligence — it was discipline. All three produced working core algorithms; gpt-oss made the fewest unverified claims about its own output.

**2. REAP's "near-lossless" claim survived the task eval despite failing the distribution eval.** This is the genuinely interesting result: 12× the distributional divergence, 31% top-token disagreement — and a task-score tie with its parent (86 vs 86.5, well within noise), with *different* failures rather than degraded ones. The KLD tail damage is real but apparently lives in regions these 10 prompts never visited. REAP isn't lossless; it's lossless *here*. If your workload is weirder than mine, measure yours.

**3. It's all moot, because the whole GLM family lost** — at equal (REAP, 12.6 GB) or larger (full Flash, ~17 GB) VRAM than the incumbent. This is the thing no vendor benchmark table could ever surface: Cerebras only compares REAP to its own parent. Their table was even directionally honest about REAP-vs-Flash parity. It just can't tell you that both lose to the model already on your disk.

## Caveats

n=10 prompts, single samples at temp 1.0 (the gpt-oss gap came from discrete failure counts, so it's probably real, but a 3× rerun of the discriminating prompts would cost ~$0.40 to confirm). One LLM grader, albeit blind and key-checked. KLD corpus was wikitext-2 only. Published REAP numbers are BF16/vLLM; everything here is Q4-class GGUF in llama.cpp — quant damage and pruning damage are confounded in the REAP rows by design, because the combination is what you'd actually ship.

## Cost & time

| Item | |
|---|---|
| Hardware | Runpod RTX A6000 48 GB, ~$0.36/hr |
| Wall clock | ~3 hours (mostly downloads + one llama.cpp build) |
| Downloads | ~90 GB (Q8 baseline, 3 candidate quants, gpt-oss) |
| Total spend | **~$2** (plus two dead pods' worth of patience) |

## Repository contents

- `scripts/` — everything needed to reproduce on any 40GB+ CUDA pod
- `results/kld/` — full llama-perplexity KLD summary outputs
- `results/stage3/` — blind answers, the unmasking key, and per-prompt grading

Stack: llama.cpp (`llama-perplexity` for KLD, `llama-server` + a ~100-line Python runner for the blind task eval), `huggingface_hub[hf_transfer]` for downloads, `nohup` for everything.
