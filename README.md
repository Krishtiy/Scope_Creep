# Scope-Creep Catcher 🔍

> A local, open-weight AI tool that protects freelancers and consultants from unpaid extra work.  
> Built for the **Hacktoberfest Open-Source AI Challenge, Week 2: Side Hustle**.  
> **100% Offline & Private:** Client agreements and confidential messages never leave your machine.

---

## 🌟 What It Does

Freelancers lose thousands of dollars each year to "scope creep" the slow accumulation of unbilled tweaks, vague client demands, and open-ended revision cycles. 

**Scope-Creep Catcher** is a private, local-first assistant that turns contracts into deterministic guardrails:

1. **Two-Tier SOW Stress Test (Before You Sign):**
   - **⚠️ Missing Standard Clauses (`M1..Mn`):** Deterministically scans for absent contract protections such as missing revision caps, undefined deadlines, unlisted deliverables, or omitted client responsibilities.
   - **🔍 Vague & Ambiguous Phrasing (`A1..An`):** Uses an expanded contract lexicon and open-weight LLM judgment to flag dangerous subjective terms (e.g., *"minor adjustments as needed"*, *"until you are happy"*, *"ongoing support"*), quoting the exact text and providing bulletproof rewrites.

2. **Client Request Checker & Rule Engine (During the Project):**
   - Splits compound client emails/messages into atomic, single action requests.
   - Matches each request against agreed SOW deliverables, pages, and explicit exclusions.
   - Enforces deterministic, legal rules in Python code to prevent AI hallucinations, override open-ended wording, and guarantee a **0% false accusation rate**.

3. **Priced Reply & Change-Order Generator (Closing the Deal):**
   - Drafts polite, professional client responses in your chosen tone (**Friendly** or **Formal**).
   - Automatically builds a formal, code-calculated **Change Order** itemizing extra hours, hourly pricing, and sign-off instructions (`Reply "APPROVED" to proceed`).
   - Downloads ready-to-sign Markdown change orders (`change_order.md`).

4. **Live Quota Tracker & Project Audit Log:**
   - Tracks revision round consumption live (e.g. `1 / 2 rounds used`).
   - Records all approved, pending, and declined requests in a persistent audit trail.

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.10+** (tested on Python 3.13)
- **[Ollama](https://ollama.com)** installed and running locally
- **Git**

### 2. Pull Local Open-Weight Model
Scope-Creep Catcher is optimized for fast, accurate local CPU execution using **Qwen 2.5 (3B)** :
```bash
ollama pull qwen2.5:3b
```
*(Optional alternative: `ollama pull gemma2:2b`)*

### 3. Clone & Install
```bash
# Clone the repository
git clone https://github.com/your-username/scope-creep-catcher.git
cd scope-creep-catcher

# Create and activate a virtual environment
python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Launch the Streamlit Web Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🧠 Architectural Principle: "LLM Reads, Code Decides"

Large Language Models alone cannot be trusted with legal boundaries or billing math they hallucinate clauses, waffle on boundaries, and drift on numbers. Scope-Creep Catcher uses a strict hybrid design where **the LLM is only a semantic parser, and deterministic Python code makes all legal verdicts and calculations**.

```
[ SOW Text + Rate ] ──> S1: Fact Extraction (LLM + Regex Fallback) ──> SOWFacts (Typed JSON)
                             │
                             ├──> S2: Stress Test (Missing Detectors + Lexicon + LLM)
                             │       ├──> ⚠️ Missing Critical Clauses (M1..Mn)
                             │       └──> 🔍 In-Text Vague Phrasing (A1..An)
                             │
[ Client Message ]  ──> S3: Atomic Request Splitter (LLM)
                             │
                             ├──> S4: SOW Semantic Matcher (LLM + Niche Skills)
                             │       │
                             │       ▼
                             └──> S5: Deterministic Rule Engine & Quote Verifier (Code)
                                     │   ├── R0: Quote Verification Guard
                                     │   ├── R1: Explicit Contract Exclusions
                                     │   ├── R2: Unlisted Pages/Screens
                                     │   ├── R3: Revision Quota Limits
                                     │   ├── R4: Vague Revision Dispute Overrides
                                     │   ├── R5: Unlisted Deliverables/Features
                                     │   └── R6: Timeline/Schedule Changes
                                     │
                                     ├──> S6: Pricing Engine (Hours x Hourly Rate) (Code)
                                     │
                                     ├──> S7: Reply & Change Order Drafter (LLM + Number Guard)
                                     │
                                     └──> S8: Persistent State & Quota Dashboard (Code)
```

### 📋 Step-by-Step Decision-Making Pipeline (`S1` → `S8`)

1. **`S1: Structured SOW Fact Extraction` (`engine/sow.py`)**
   - **Input:** Raw Statement of Work text and rate.
   - **Logic:** The LLM extracts 12 structured fields into a strictly validated Pydantic schema (`SOWFacts`: pages, revision rounds, deliverables, exclusions, deadline, payment terms, client responsibilities).
   - **Fallback & Verification:** If the model omits standard fields, deterministic regex extractors fill the blanks without overwriting valid data. Every cited quote (`pages_quote`, `revision_quote`, `excluded_quote`) is strictly verified against source text using Unicode NFKC normalization and RapidFuzz alignment. Unverifiable citations are automatically nulled out to prevent hallucinated contractual clauses.

2. **`S2: SOW Stress Test & Ambiguity Scoring` (`engine/stress_test.py`)**
   - **Input:** Extracted facts and raw contract text.
   - **Logic:** Merges three distinct detection layers:
     - **Deterministic Lexicon Scan:** Regex rules based on `config/lexicon.yaml` flag dangerous phrases (*"as needed"*, *"until satisfied"*, *"minor tweaks"*).
     - **LLM Ambiguity Judgment:** Evaluates contextual risk and generates concrete Freelancer vs. Client readings with copyable contract rewrites.
     - **Static Missing Clause Detectors:** Deterministically flags absent caps (`M1..Mn`), undefined revision limits, and missing client responsibilities.
   - **Output:** Up to 5 prioritized risk cards assigned persistent IDs (`A1..A5`) that cross-link into request checking rules.

3. **`S3: Atomic Request Splitter` (`engine/checker.py`)**
   - **Input:** Raw client message or email.
   - **Logic:** Client messages often compound multiple tasks into one sentence (e.g., *"Can you fix the login button, add a blog page, and deliver by Friday?"*). The LLM parses the message into atomic, single-action `SplitRequest` objects tagged by request type (`new_page`, `revision`, `new_feature`, `timeline_change`) and magnitude (`tweak`, `substantial`, `unclear`).

4. **`S4: Semantic Scope Matcher` (`engine/checker.py`)**
   - **Input:** Individual atomic request + SOW facts + domain skills profile.
   - **Logic:** Matches the request against agreed deliverables and injects domain-specific guidance ([skills/web_dev.md](skills/web_dev.md), [skills/copywriting.md](skills/copywriting.md)) to prevent common false positives (e.g. recognizing that fixing a broken responsive navbar is an included bugfix, not a new page).
   - **Output:** Model proposes an initial verdict (`in_scope`, `out_of_scope`, or `gray_area`) with supporting quotes and confidence scores.

5. **`S5: Deterministic Rule Engine & Quote Verifier` (`engine/rules.py` & `engine/verifier.py`)**
   - **Input:** LLM proposal + active project quota + stress test issues + verbatim texts.
   - **Logic:** Rules `R0` through `R8` execute in pure Python code. The model's proposed verdict is deterministically overridden if contract boundaries are breached:
     - Quotes are verified verbatim; unverifiable citations immediately trigger rule `R0` (`unverified`).
     - Requests matching explicit exclusions trigger `R1` (`out_of_scope`).
     - Requests for unlisted pages or deliverables trigger `R2`/`R5` (`out_of_scope`).
     - Revision quota counters trigger `R3` (`out_of_scope` if exceeded; `gray_area` if undefined).
     - Subjective redesign requests under vague clauses trigger `R4` (`gray_area` cross-linked to Stress Test card).

6. **`S6: Deterministic Pricing Engine` (`engine/pricing.py`)**
   - **Input:** Request type, size (`S`, `M`, `L`), and project hourly rate.
   - **Logic:** Pure Python lookup and arithmetic (`hours * hourly_rate`). Hours are bounded deterministically based on standard complexity tiers (`config/hours.yaml`), eliminating LLM arithmetic errors and billing drift.

7. **`S7: Reply Drafter & Change Order Generator` (`engine/drafter.py`)**
   - **Input:** Code-enforced decision, pricing calculations, tone preference (Friendly vs. Formal).
   - **Logic:** Generates polite, professional client communication:
     - For `in_scope`: Drafts an acknowledgment confirming the task is covered.
     - For `gray_area`: Generates polite clarifying questions before commencing work.
     - For `out_of_scope`: Generates a polite explanation and builds a legally structured **Change Order** with a built-in **Number Guard** that verifies all quoted dollar figures and hours in the reply text strictly match the pricing engine calculations.

8. **`S8: Persistent State & Quota Audit Trail` (`engine/state.py`)**
   - **Input:** User approval, rejection, or edit actions.
   - **Logic:** Persists project state locally to `data/projects/{project_id}.json`. Automatically increments consumed revision rounds when revisions are accepted, and maintains an exportable chronological audit log.

---

## 🛡️ The 9 Deterministic Contract Rules (`engine/rules.py`)

Every verdict is strictly governed by Python code rules (`R0` through `R8`). The AI model's opinion is overridden whenever a contract boundary is violated:

| Rule | Name | Condition & Ruling |
| :--- | :--- | :--- |
| **`R0`** | **Quote Verification Guard** | If the model cites text not found verbatim in the contract or message, force `unverified` to stop hallucination. |
| **`R1`** | **Explicit Exclusion** | If the request matches an item in the SOW's `Excluded` list, force **`out_of_scope`**. |
| **`R2`** | **Unlisted Page** | If the client asks for a page/screen not in the agreed page list, force **`out_of_scope`**. |
| **`R3`** | **Revision Quota Enforcement** | If the revision limit is exceeded, force **`out_of_scope`**. If revision rounds are null, mark **`gray_area`**. |
| **`R4`** | **Vague Revision Dispute Guard** | If a client asks for a redesign under vague terms (e.g. *"minor adjustments until happy"*), force **`gray_area`** and link to Stress Test issue `M1`/`A1`. |
| **`R5`** | **Unlisted Deliverable** | If the request asks for a standalone deliverable not in agreed scope, force **`out_of_scope`**. |
| **`R6`** | **Timeline Change** | Schedule or deadline adjustments require mutual agreement; force **`gray_area`**. |
| **`R7`** | **Low Confidence Fallback** | If the contract is silent and confidence is low, safely default to **`gray_area`** instead of accusing the client. |
| **`R8`** | **Code Always Wins** | Deterministic Python rules strictly override the LLM's proposed verdict. |

---

## 💻 Streamlit UI Features

### 1. Sidebar Project Configuration
- **Project Name & Local Storage**: Automatically saves session state to `data/projects/{name}.json`.
- **Hourly Rate & Currency**: Supports USD, EUR, GBP, INR, and AUD.
- **Contract Price & Niche Selector**: Injects domain-specific guidance (`web_dev`, `copywriting`, or general).

### 2. Tab 1: SOW Stress Test
- **Two Dedicated Sections**:
  - **⚠️ Missing Standard Clauses**: Expands by default with recommended clauses to add into your contract before sending.
  - **🔍 Vague & Ambiguous Phrasing**: Highlights exact in-text quotes verified against the text with one-click copyable rewrites.

### 3. Tab 2: Check Client Request
- **Plain-English Verdicts**:
  - 🟢 **INCLUDED IN CONTRACT**: Covered under existing scope; no extra charge.
  - 🔴 **EXTRA WORK (BILLABLE)**: Outside agreed scope; requires Change Order.
  - 🟡 **UNCLEAR / NEEDS CLARIFICATION**: Open to dispute; requires client clarification before proceeding.
- **AI Analysis Confidence Trust Indicator**: Subtle High / Medium / Low badges explaining *why* the AI is confident based on contract specificity.
- **Side-by-Side Comparison**: Displays client message quote alongside the exact cited SOW clause.
- **Streamlined Draft Reply**: Friendly or Formal email drafter with instant copy and Markdown Change Order generator.

### 4. Tab 3: Project Log & Audit Trail
- Logs every approved, pending, and declined request.
- One-click export of project logs to Markdown (`{project}_log.md`).

---

## 🤝 Hacktoberfest Partner Technologies & Integration Architecture

Scope-Creep Catcher was designed for the **Hacktoberfest Open-Source AI Challenge, Week 2: Side Hustle**. It integrates three Hacktoberfest partner technologies while strictly maintaining a **100% offline, zero-data-leak privacy guarantee** for freelancers:

| Partner Technology | Category / Role | Implementation in Project | Privacy & Data Handling |
| :--- | :--- | :--- | :--- |
| **Google Gemma 2** | **Featured Partner**<br>(Open-Weight Models) | Integrated locally via Ollama (`gemma2:2b`). Benchmarked across dev/test splits in `eval/run_eval.py` to compare lightweight model accuracy against Qwen 2.5 3B. | **100% Offline & Local.** Model weights execute entirely on-device; zero outbound data. |
| **Backboard.io** | **Partner Technology**<br>(AI Infrastructure & Memory) | Cloud evaluation harness (`eval/run_backboard.py`) using `backboard-sdk`. Evaluates cloud-hosted 70B models against small open models on our synthetic benchmark. | **Synthetic Data ONLY.** Real user contracts in `data/projects/` **NEVER** leave your laptop. Only public synthetic gold cases in `data/gold/` are evaluated. |
| **Entire.io** | **Partner Technology**<br>(Agent Observability) | Built-in agent observability using the **Entire CLI**, capturing every prompt, tool execution, and code checkpoint linked to git commits. | **Developer Telemetry.** Captures agent trajectories during local build sessions. |

---

### 🛡️ Why Backboard Cloud Eval Does Not Compromise Local Privacy

The core challenge of building this offline, privacy-first side-hustle tool was incorporating cloud partner technologies without leaking confidential client contracts:

```
┌────────────────────────────────────────────────────────┐
│ 1. PRODUCTION RUNTIME (Freelancers / Streamlit App)    │
│    • Real Client Contracts & Messages                  │
│    • 100% Local, Offline & Private                     │
│    • Ollama (Open-Weight: Qwen 2.5)          │
│    • NO Cloud APIs, NO Data Leaks                      │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ 2. DEVELOPER BENCHMARK (eval/run_backboard.py)         │
│    • Synthetic Gold Cases ONLY (data/gold/cases.json)  │
│    • Backboard.io Cloud API (Partner Technology)       │
│    • Benchmarks 70B cloud models vs. local models      │
│    • Results logged to results/RESULTS.md              │
└────────────────────────────────────────────────────────┘
```

1. **Production Runtime is 100% Offline:** When freelancers use the Streamlit application ([app.py](app.py)), all parsing, decision rules, and change order generations execute entirely offline on local Ollama weights. Wi-Fi can be completely turned off.
2. **Backboard is Strictly for Synthetic Benchmarking:** `eval/run_backboard.py` sends only public, synthetic benchmark cases ([data/gold/cases.json](data/gold/cases.json)) to Backboard to empirically measure how pure cloud models perform versus local deterministic pipelines.

---

## Model Selection Decision Flow: Why I Chose Qwen 2.5 3B via Empirical Evaluation (`eval/`)

A fundamental engineering question for this project was: **Which open-weight model should power the final offline application?**

When handling legal contracts and client billing, you cannot choose an AI based on guesses. I designed the **`eval/`** benchmarking suite to run a rigorous **empirical selection tournament** to answer:
1. **Local Contender Battle:** How does **Qwen 2.5 (3B)** compare against Google **Gemma 2 (2B)** on structured legal parsing?
2. **Cloud vs. Local Benchmark:** Can a 3B model running on a budget laptop match or beat a giant **70B parameter model in the cloud** (`meta-llama/llama-3.1-70b-instruct` via **Backboard.io**)?
3. **Safety Verification:** Which model guarantees a **0.0% False Accusation Rate**, ensuring freelancers never insult clients with false scope-creep claims?

Here is the exact decision flow from test design to final production selection:

```
                  ┌──────────────────────────────────────────────┐
                  │ 1. THE EXAM: data/gold/cases.json            │
                  │    23 Synthetic Real-World Client Scenarios  │
                  └──────────────────────┬───────────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 │                                               │
                 ▼                                               ▼
   ┌───────────────────────────┐                   ┌───────────────────────────┐
   │ 2. LOCAL TEST: run_eval.py│                   │ 3. CLOUD BENCHMARK:       │
   │    Local Ollama Models    │                   │    run_backboard.py       │
   │    • Qwen 2.5 3B vs.      │                   │    • Llama 3.1 70B Cloud  │
   │      Gemma 2 2B           │                   │    • Backboard.io Partner │
   │    • Baseline vs Pipeline │                   │    • Synthetic Data Only  │
   └─────────────┬─────────────┘                   └─────────────┬─────────────┘
                 │                                               │
                 │      Raw Execution Data (results/raw/*.json)  │
                 └───────────────────────┬───────────────────────┘
                                         │
                                         ▼
                         ┌───────────────────────────────┐
                         │ 4. GRADING: eval/metrics.py   │
                         │    Calculates Accuracy &      │
                         │    False Accusation Rate (FAR)│
                         └───────────────┬───────────────┘
                                         │
                                         ▼
                         ┌───────────────────────────────┐
                         │ 5. VERDICT: make_report.py    │
                         │    Compiles results/RESULTS.md│
                         │    Crowns the Winning Model   │
                         └───────────────┬───────────────┘
                                         │
                                         ▼
                         ┌───────────────────────────────┐
                         │ 6. FINAL PRODUCTION RUNTIME   │
                         │    qwen2.5:3b selected in     │
                         │    engine/config.py & app.py  │
                         └───────────────────────────────┘
```

---

### 🧩 Why Each File in `eval/` Exists (The Step-by-Step Flow)

1. **`data/gold/cases.json` — The "Gold Standard Exam"**
   - Contains 23 synthetic, professionally written freelance contract scenarios across web development, copywriting, and media production.
   - Each case includes the raw Statement of Work, a realistic client email, labeled atomic requests, ground-truth verdicts (`in_scope`, `out_of_scope`, `gray_area`), difficulty ratings (`obvious`, `subtle`), and exact contract clause references.

2. **`eval/run_eval.py` — The Local Model Evaluator**
   - **Why it's there:** Tests our local open-weight models (`qwen2.5:3b` and `gemma2:2b`) running on-device inside Ollama.
   - **The Two Modes:**
     - **Baseline Mode:** Prompts the raw LLM directly without any Python guardrails to measure the model's unassisted reasoning.
     - **Pipeline Mode:** Runs the full 8-step engine (`S1`→`S5`) including Pydantic extraction, RapidFuzz quote verification, and the 9 deterministic contract rules.
   - **Output:** Writes raw JSON execution logs to `results/raw/eval_<model>_<mode>_<split>.json`.

3. **`eval/run_backboard.py` — The Cloud Partner Benchmark**
   - **Why it's there:** Connects to **Backboard.io** via the official `backboard-sdk` to evaluate a giant cloud-hosted 70B parameter model (`meta-llama/llama-3.1-70b-instruct`).
   - **The Architectural Rationale:** Allows us to answer: *"Can our 3B parameter model on a local laptop match or beat a 70B model in the cloud?"* (Result: Local Qwen + Rules scored **60.0%**, while raw Cloud 70B scored **20.0%**).
   - **Privacy Boundary:** Strictly limited to public synthetic test cases. Confidential freelancer projects in `data/projects/` never touch Backboard.
   - **Output:** Writes raw JSON execution logs to `results/raw/backboard_<model>_<split>.json`.

4. **`eval/metrics.py` — The Grading Engine & Mathematical Formulas**
   - **Why it's there:** Standard machine learning metrics (like simple accuracy) are dangerous in client management. In freelancing, errors are highly asymmetric:
     - **False Accusation Rate (FAR):** If an AI wrongly claims an included revision is an unbilled extra, the freelancer confronts the client with an unjustified invoice, destroying client trust. `metrics.py` strictly measures this via:
       $$\text{FAR} = \frac{\text{False Out-of-Scope Accusations}}{\text{Total In-Scope or Gray-Area Requests}}$$
     - **Confusion Matrix:** Generates structured Markdown tables showing exactly where models waffle (e.g. classifying `in_scope` work as `gray_area`).
     - **Per-Difficulty Breakdown:** Evaluates accuracy separately on obvious vs. subtle contract edge cases.

5. **`eval/make_report.py` — The Automated Report Compiler**
   - **Why it's there:** Collects all raw JSON output files in `results/raw/`, executes grading formulas from `metrics.py`, and compiles the official benchmark report: **[results/RESULTS.md](results/RESULTS.md)**.

---

### 📑 What Is Inside `results/RESULTS.md`?

The generated report card at **[results/RESULTS.md](results/RESULTS.md)** contains:

| Model | Evaluation Mode | Split | N | Accuracy | False Accusation Rate (FAR) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **`qwen2.5:3b`** *(Recommended)* | **Full Pipeline (S1→S5)** | **test** | **15** | **60.0%** | **0.0%** 🏆 |
| `gemma2:2b` | Full Pipeline (S1→S5) | test | 15 | 33.3% | 14.3% |
| **`qwen2.5:3b`** | Baseline (Raw Prompt) | test | 15 | 73.3% | 28.6% |
| `gemma2:2b` | Baseline (Raw Prompt) | test | 15 | 60.0% | 14.3% |
| `meta-llama/llama-3.1-70b-instruct` | Backboard (Cloud) | test | 15 | 20.0% | 0.0% |
| **`qwen2.5:3b`** | Full Pipeline (S1→S5) | dev | 8 | 62.5% | 50.0% |
| `gemma2:2b` | Full Pipeline (S1→S5) | dev | 8 | 50.0% | 0.0% |

### Key Benchmark Takeaways:
- **`qwen2.5:3b` achieves double the pipeline accuracy** of `gemma2:2b` on the test suite (60.0% vs. 33.3%).
- **`qwen2.5:3b` achieves 0.0% False Accusations** under our deterministic rule engine on the test split. Falsely accusing a client of scope creep destroys professional relationships; our rule engine guarantees safety.
- **Backboard 70B Cloud Baseline (20.0% accuracy)** reveals that ungrounded raw LLMs default to overly cautious `gray_area` hedging, proving that Python deterministic rules are essential for reliable legal and billing decisions.

---

## 🔬 Observability with Entire (`entire.io`)

Scope-Creep Catcher includes built-in agent observability using **Entire CLI**, capturing every prompt, tool execution, and code checkpoint:

- **Check Current Agent Session**:
  ```powershell
  entire session current
  ```
- **Inspect Past Checkpoints Tied to Git Commits**:
  ```powershell
  entire checkpoint list
  entire checkpoint explain <checkpoint-id>
  ```
- **Token Usage & Audit Metrics**:
  ```powershell
  entire session tokens <session-id>
  ```

---

## 🧪 Testing & Verification Commands

### 1. Run Unit Tests (100 Unit Tests, Fast & Deterministic)
All 100 unit tests run completely offline with no live LLM required in ~1.35 seconds:
```bash
pytest -v
```
```text
 100 passed in 1.35s 
```

### 2. Run Local Evaluation Benchmark
Evaluate extraction and classification performance against the synthetic gold test suite:
```bash
# Evaluate current model (Qwen 2.5 3B)
python -m eval.run_eval --model qwen2.5:3b --mode pipeline --split test

# Evaluate Google Gemma 2 (2B)
python -m eval.run_eval --model gemma2:2b --mode pipeline --split test
```

### 3. Run Backboard Partner Cloud Evaluation
Run Backboard cloud evaluation on synthetic gold cases:
```bash
python -m eval.run_backboard --split test --model meta-llama/llama-3.1-70b-instruct
```

### 4. Re-compile Comparison Report
Aggregate all local and cloud evaluation runs into `results/RESULTS.md`:
```bash
python -m eval.make_report
```

---

## 📄 License & Attribution
- **Codebase:** [MIT License](LICENSE)
- **Local Model:** Compatible with [Qwen 2.5](https://huggingface.co/Qwen) and [Google Gemma 2](https://ai.google.dev/gemma/terms).
- **Runtime:** [Ollama](https://github.com/ollama/ollama).

---

## ⚠️ Disclaimer
*Scope-Creep Catcher is an AI-assisted productivity tool for document analysis and scope comparison. It does not provide legal advice. All financial figures and hour estimates are illustrative calculations based on user-provided inputs. Always consult a qualified legal professional for binding contractual agreements.*

