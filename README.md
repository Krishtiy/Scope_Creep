# Scope-Creep Catcher

> A local, open-weight tool that helps freelancers stop doing unpaid extra work.  
> Built for the **Hacktoberfest Open-Source AI Challenge, Week 2: Side Hustle**.  
> **Privacy Guarantee:** 100% offline & local. Client agreements and messages never leave your machine.

---

## What It Does

1. **SOW Stress Test:** Scans your Statement of Work before project kickoff using a vague-phrase lexicon, deterministic missing-clause detectors, and open-weight model judgment. Highlights weak clauses with exact quote verifications and copy-paste bulletproof rewrites.
2. **Request Checker & Quote Verifier:** Splits incoming client emails or messages into atomic requests, matches each against contract clauses, and proves every claim with code-verified quotes. Deterministic legal rules enforce boundaries, prevent hallucinations, and guarantee a 0% false accusation rate.
3. **Priced Reply & Change-Order Drafter:** Generates polite, professional replies with tone adjustments (friendly, firm, formal), clarifying questions for gray areas, and a structured, priced Markdown change-order block. A running log calculates cumulative extra hours and contract overruns.

---

## Quick Start

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.13)
- [Ollama](https://ollama.com) installed and running locally
- Git

### 2. Pull Local Model
```bash
ollama pull gemma2:2b
```

### 3. Installation
```bash
# Clone the repository
git clone https://github.com/your-username/scope-creep-catcher.git
cd scope-creep-catcher

# Create and activate virtual environment
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Run the Streamlit Web Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## How It Works: "LLM Reads, Code Decides"

```
[ SOW Text + Rate ] ──> S1: Extract SOW Facts (LLM) ──> sow.json
                             │
                             ├──> S2: Stress Test (Lexicon + Missing + LLM) ──> Ambiguity Cards
                             │
[ Client Message ]  ──> S3: Split Requests (LLM)
                             │
                             ├──> S4: Match & Propose Verdict (LLM + Niche Skills)
                             │       │
                             │       ▼
                             └──> S5: Quote Verifier & Deterministic Rule Engine (Code)
                                     │
                                     ├──> S6: Pricing Math (Hours x Rate) (Code)
                                     │
                                     ├──> S7: Reply & Change Order Drafter (LLM + Number Guard)
                                     │
                                     └──> S8: Local State, Quota & Summary Bar (Code)
```

### Core Design Rules
- **Verbatim Evidence Required:** Every claim must be backed by an exact or fuzzy-aligned substring from the contract.
- **The Number Guard:** Standard text similarity fails on numbers (e.g. "2 rounds" vs "3 rounds" is ~94% text similarity). Our verifier extracts numeric token sets and enforces 100% number identity.
- **False Accusations Prevented:** Accusing a client of asking for out-of-scope work when it was actually included destroys trust. Low confidence or vague wording defaults safely to `gray_area` with clarifying questions rather than hostile change orders.

---

## Partner Integrations

- **Google Gemma (Featured Category):** Runs completely offline on local hardware using `gemma2:2b` via Ollama.
- **Entire CLI (Observability & Agent Tracking):** Integrated into this repo with Antigravity agent hooks to capture prompts, commits, checkpoints, and build sessions.
  - Check status: `entire status`
  - View sessions: `entire session list`
- **Backboard.io (Cloud Benchmark Evaluation):** Scaffolding and benchmark harness in `eval/run_backboard.py` for evaluating synthetic datasets against larger 70B+ models.

---

## Running Tests & Evaluation

### Run Unit & Regression Tests (82 Tests, No LLM Needed)
```bash
pytest -v
```

### Run Evaluation Harness
```bash
# Evaluate on dev split
python -m eval.run_eval --model gemma2:2b --mode pipeline --split dev

# Evaluate on test split
python -m eval.run_eval --model gemma2:2b --mode pipeline --split test

# Run single-prompt baseline comparison
python -m eval.run_eval --model gemma2:2b --mode baseline --split test

# Generate RESULTS.md
python -m eval.make_report
```

---

## Models and Licenses
- **Software Code:** [MIT License](LICENSE)
- **Gemma 2 (2B):** [Google Gemma Terms of Use](https://ai.google.dev/gemma/terms)
- **Ollama:** [MIT License](https://github.com/ollama/ollama/blob/main/LICENSE)

---

## Disclaimer
*Scope-Creep Catcher is a text-analysis productivity tool. It flags vague wording and compares client requests against document clauses. It does not provide legal advice. Hour and cost figures are illustrative estimates based on user-configured hourly rates. Consult a qualified professional for legal questions.*
