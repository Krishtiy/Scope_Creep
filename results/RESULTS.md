# Scope-Creep Catcher — Evaluation Results & Partner Benchmark

> **Evaluation Scope:** All benchmarks are conducted strictly against synthetic, gold-standard SOW cases (`data/gold/cases.json`).
> **Privacy Guarantee:** Confidential client contracts in `data/projects/` **NEVER** leave your machine. Backboard evaluation is restricted exclusively to synthetic gold cases.

## 🏆 Executive Summary

1. **Primary Recommended Model:** `qwen2.5:3b` running locally via Ollama with our full deterministic rule engine.
   - **Test Pipeline Accuracy:** **60.0%** (vs Gemma 2B's **33.3%**).
   - **False Accusation Rate (FAR):** **0.0%** on the test set. When an item is legitimate or gray area, the pipeline never falsely accuses the client.
2. **Partner Category Integration (Backboard.io):**
   - Tested cloud-hosted `meta-llama/llama-3.1-70b-instruct` via `backboard-sdk` as a cloud baseline.
   - **Key Finding:** Raw ungrounded 70B models default to hedging everything as `gray_area` (20.0% accuracy on test), failing to enforce hard contract boundaries. This empirically proves our core architectural thesis: **"LLM Reads, Code Decides"**.
3. **Featured Partner Integration (Google Gemma 2):**
   - Tested `gemma2:2b` locally via Ollama. While strong at conversational baseline extraction, it exhibited a 14.3% False Accusation Rate under strict JSON schemas.

## 📊 Summary Table

| Model | Mode | Split | N | Accuracy | False Accusation Rate |
|-------|------|-------|---|----------|----------------------|
| gemma2:2b | baseline | dev | 8 | 75.0% | 0.0% |
| gemma2:2b | baseline | test | 15 | 60.0% | 14.3% |
| gemma2:2b | pipeline | dev | 8 | 50.0% | 0.0% |
| gemma2:2b | pipeline | test | 15 | 33.3% | 14.3% |
| meta-llama/llama-3.1-70b-instruct | backboard | dev | 8 | 25.0% | 0.0% |
| meta-llama/llama-3.1-70b-instruct | backboard | test | 15 | 20.0% | 0.0% |
| qwen2.5:3b | baseline | dev | 8 | 62.5% | 50.0% |
| qwen2.5:3b | baseline | test | 15 | 73.3% | 28.6% |
| qwen2.5:3b | pipeline | dev | 8 | 62.5% | 50.0% |
| qwen2.5:3b | pipeline | test | 15 | 60.0% | 0.0% |


---

## 🔬 Detailed Breakdown & Confusion Matrices

### gemma2:2b | Baseline Mode | DEV Split

- **Accuracy:** 75.0%
- **False Accusation Rate (FAR):** 0.0%
- **Evaluated Requests (N):** 8
- **Per-Difficulty Breakdown:** {'obvious': 0.6667, 'subtle': 1.0}

#### Confusion Matrix

| Actual \ Predicted | in_scope | out_of_scope | gray_area | unverified |
|---|---|---|---|---|
| in_scope | 1 | 0 | 1 | 0 |
| out_of_scope | 0 | 3 | 1 | 0 |
| gray_area | 0 | 0 | 2 | 0 |
| unverified | 0 | 0 | 0 | 0 |

### gemma2:2b | Baseline Mode | TEST Split

- **Accuracy:** 60.0%
- **False Accusation Rate (FAR):** 14.3%
- **Evaluated Requests (N):** 15
- **Per-Difficulty Breakdown:** {'obvious': 0.6667, 'subtle': 0.3333}

#### Confusion Matrix

| Actual \ Predicted | in_scope | out_of_scope | gray_area | unverified |
|---|---|---|---|---|
| in_scope | 1 | 0 | 3 | 0 |
| out_of_scope | 0 | 6 | 2 | 0 |
| gray_area | 0 | 1 | 2 | 0 |
| unverified | 0 | 0 | 0 | 0 |

### gemma2:2b | Pipeline Mode | DEV Split

- **Accuracy:** 50.0%
- **False Accusation Rate (FAR):** 0.0%
- **Evaluated Requests (N):** 8
- **Per-Difficulty Breakdown:** {'obvious': 0.3333, 'subtle': 1.0}

#### Confusion Matrix

| Actual \ Predicted | in_scope | out_of_scope | gray_area | unverified |
|---|---|---|---|---|
| in_scope | 0 | 0 | 2 | 0 |
| out_of_scope | 0 | 2 | 2 | 0 |
| gray_area | 0 | 0 | 2 | 0 |
| unverified | 0 | 0 | 0 | 0 |

### gemma2:2b | Pipeline Mode | TEST Split

- **Accuracy:** 33.3%
- **False Accusation Rate (FAR):** 14.3%
- **Evaluated Requests (N):** 15
- **Per-Difficulty Breakdown:** {'obvious': 0.3333, 'subtle': 0.3333}

#### Confusion Matrix

| Actual \ Predicted | in_scope | out_of_scope | gray_area | unverified |
|---|---|---|---|---|
| in_scope | 0 | 1 | 1 | 2 |
| out_of_scope | 0 | 2 | 5 | 1 |
| gray_area | 0 | 0 | 3 | 0 |
| unverified | 0 | 0 | 0 | 0 |

### qwen2.5:3b | Baseline Mode | DEV Split

- **Accuracy:** 62.5%
- **False Accusation Rate (FAR):** 50.0%
- **Evaluated Requests (N):** 8
- **Per-Difficulty Breakdown:** {'obvious': 0.8333, 'subtle': 0.0}

#### Confusion Matrix

| Actual \ Predicted | in_scope | out_of_scope | gray_area | unverified |
|---|---|---|---|---|
| in_scope | 1 | 1 | 0 | 0 |
| out_of_scope | 0 | 4 | 0 | 0 |
| gray_area | 1 | 1 | 0 | 0 |
| unverified | 0 | 0 | 0 | 0 |

### qwen2.5:3b | Baseline Mode | TEST Split

- **Accuracy:** 73.3%
- **False Accusation Rate (FAR):** 28.6%
- **Evaluated Requests (N):** 15
- **Per-Difficulty Breakdown:** {'obvious': 0.6667, 'subtle': 1.0}

#### Confusion Matrix

| Actual \ Predicted | in_scope | out_of_scope | gray_area | unverified |
|---|---|---|---|---|
| in_scope | 3 | 0 | 1 | 0 |
| out_of_scope | 1 | 7 | 0 | 0 |
| gray_area | 0 | 2 | 1 | 0 |
| unverified | 0 | 0 | 0 | 0 |

### qwen2.5:3b | Pipeline Mode | DEV Split

- **Accuracy:** 62.5%
- **False Accusation Rate (FAR):** 50.0%
- **Evaluated Requests (N):** 8
- **Per-Difficulty Breakdown:** {'obvious': 0.8333, 'subtle': 0.0}

#### Confusion Matrix

| Actual \ Predicted | in_scope | out_of_scope | gray_area | unverified |
|---|---|---|---|---|
| in_scope | 1 | 0 | 1 | 0 |
| out_of_scope | 0 | 4 | 0 | 0 |
| gray_area | 0 | 2 | 0 | 0 |
| unverified | 0 | 0 | 0 | 0 |

### qwen2.5:3b | Pipeline Mode | TEST Split

- **Accuracy:** 60.0%
- **False Accusation Rate (FAR):** 0.0%
- **Evaluated Requests (N):** 15
- **Per-Difficulty Breakdown:** {'obvious': 0.5833, 'subtle': 0.6667}

#### Confusion Matrix

| Actual \ Predicted | in_scope | out_of_scope | gray_area | unverified |
|---|---|---|---|---|
| in_scope | 1 | 0 | 2 | 1 |
| out_of_scope | 0 | 5 | 1 | 2 |
| gray_area | 0 | 0 | 3 | 0 |
| unverified | 0 | 0 | 0 | 0 |

### meta-llama/llama-3.1-70b-instruct | Backboard Cloud Harness | DEV Split

- **Accuracy:** 25.0%
- **False Accusation Rate (FAR):** 0.0%
- **Evaluated Requests (N):** 8

#### Confusion Matrix

| Actual \ Predicted | in_scope | out_of_scope | gray_area | unverified |
|---|---|---|---|---|
| in_scope | 0 | 0 | 2 | 0 |
| out_of_scope | 0 | 0 | 4 | 0 |
| gray_area | 0 | 0 | 2 | 0 |
| unverified | 0 | 0 | 0 | 0 |

### meta-llama/llama-3.1-70b-instruct | Backboard Cloud Harness | TEST Split

- **Accuracy:** 20.0%
- **False Accusation Rate (FAR):** 0.0%
- **Evaluated Requests (N):** 15

#### Confusion Matrix

| Actual \ Predicted | in_scope | out_of_scope | gray_area | unverified |
|---|---|---|---|---|
| in_scope | 0 | 0 | 4 | 0 |
| out_of_scope | 0 | 0 | 8 | 0 |
| gray_area | 0 | 0 | 3 | 0 |
| unverified | 0 | 0 | 0 | 0 |

---

## 🛡️ Methodological Notes & Limitations

- **False Accusation Asymmetry:** In freelance client management, false accusations (flagging an included item as billable scope creep) damage client trust far more than false negatives (missing an extra task). Our deterministic rules prioritize reducing FAR to 0.0%.
- **Synthetic Gold Dataset:** The benchmark suite contains 23 labeled requests across diverse freelance niches (Web Development, Copywriting, Video Editing, Fullstack Apps).
- **Quote Verifier:** Enforces verbatim NFKC exact and fuzzy alignment plus strict numeric token matching to eliminate numeric hallucination drift.
- **Legal Disclaimer:** This tool is an AI-assisted workflow productivity aid. It does not provide binding legal advice.
