# Scope-Creep Catcher 🔍

> A local, open-weight AI tool that protects freelancers and consultants from unpaid extra work.  
> Built for the **Hacktoberfest Open-Source AI Challenge, Week 2: Side Hustle**.  
> **100% Offline & Private:** Client agreements and confidential messages never leave your machine.

---

## 🌟 What It Does

Freelancers lose thousands of dollars each year to "scope creep"—the slow accumulation of unbilled tweaks, vague client demands, and open-ended revision cycles. 

**Scope-Creep Catcher** is a private, local-first assistant that turns contracts into deterministic guardrails:

1. **Two-Tier SOW Stress Test (Before You Sign):**
   - **⚠️ Missing Standard Clauses (`M1..Mn`):** Deterministically scans for absent contract protections—such as missing revision caps, undefined deadlines, unlisted deliverables, or omitted client responsibilities.
   - **🔍 Vague & Ambiguous Phrasing (`A1..An`):** Uses an expanded contract lexicon and open-weight LLM judgment to flag dangerous subjective terms (e.g., *"minor adjustments as needed"*, *"until you are happy"*, *"ongoing support"*), quoting the exact text and providing bulletproof rewrites.

2. **Client Request Checker & Rule Engine (During the Project):**
   - Splits compound client emails/messages into atomic, single-action requests.
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
Scope-Creep Catcher is optimized for fast, accurate local CPU/GPU execution using **Qwen 2.5 (3B)** or **Gemma 2 (2B)**:
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

Large Language Models alone cannot be trusted with legal boundaries or billing math—they hallucinate clauses, waffle on boundaries, and drift on numbers. Scope-Creep Catcher uses a strict hybrid design where **the LLM is only a semantic parser, and deterministic Python code makes all legal verdicts and calculations**.

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

## 🧪 Testing & Verification

### Run Unit Tests (83 Unit Tests, Fast & Deterministic)
All unit tests run completely offline with no live LLM required:
```bash
pytest -v
```
```text
============================= 83 passed in 0.98s =============================
```

### Run Benchmark Evaluation Harness
Evaluate extraction and classification performance against the gold test suite (`data/gold/cases.json`):
```bash
python -m eval.run_eval --model qwen2.5:3b --mode pipeline --split test
```

---

## 📄 License & Attribution
- **Codebase:** [MIT License](LICENSE)
- **Local Model:** Compatible with [Qwen 2.5](https://huggingface.co/Qwen) and [Google Gemma 2](https://ai.google.dev/gemma/terms).
- **Runtime:** [Ollama](https://github.com/ollama/ollama).

---

## ⚠️ Disclaimer
*Scope-Creep Catcher is an AI-assisted productivity tool for document analysis and scope comparison. It does not provide legal advice. All financial figures and hour estimates are illustrative calculations based on user-provided inputs. Always consult a qualified legal professional for binding contractual agreements.*

