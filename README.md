# Scope-Creep Catcher 🔍

> A local, open-weight AI tool that protects freelancers and consultants from unpaid extra work.  
> Built for the **Hacktoberfest Open-Source AI Challenge, Week 2: Side Hustle**.  
> **100% Offline & Private:** Client agreements and confidential messages never leave your machine.

---

## 🌟 What It Does

Freelancers and agency owners lose thousands of dollars each year to **"scope creep"** the slow, sneaky accumulation of unbilled tweaks, vague client demands, and endless revision rounds that turn a profitable gig into unpaid overtime.

To solve this, **Scope-Creep Catcher** is built around **4 Core Features** that protect you across the three phases of any client contract:

```
                  ┌────────────────────────────────────────────────────────┐
                  │          THE FREELANCE PROJECT LIFECYCLE               │
                  └──────────────────────────┬─────────────────────────────┘
                                             │
      ┌──────────────────────────────────────┼──────────────────────────────────────┐
      ▼                                      ▼                                      ▼
[ BEFORE YOU SIGN ]                 [ DURING THE PROJECT ]                 [ CLOSING THE DEAL ]
Feature 1: SOW Stress Test          Feature 2: Request Checker             Feature 3: Change Orders
• Scans contract traps              • Splits compound emails               • Auto-calculates hours & fees
• Detects missing clauses (M1..Mn)  • 0% false accusations                 • Friendly or formal pushback
• Instant bulletproof rewrites      • Traffic-light verdicts               • Ready-to-sign Markdown agreements
      │                                      │                                      │
      └──────────────────────────────────────┼──────────────────────────────────────┘
                                             ▼
                               [ THROUGHOUT THE PROJECT ]
                               Feature 4: Live Quota Tracker & Audit Log
                               • Tracks revision rounds used (e.g., 1 of 2 used)
                               • Local JSON audit ledger of every approved change
```

### 🌟 The 4 Core Features

| # | Feature Name | Project Phase | What It Does for You | Real-World Example |
|:---:|---|---|---|---|
| **1** | **Two-Tier SOW Stress Test** | **Before You Sign** | • Detects **missing standard clauses** (`M1..Mn`) like undefined deadlines or omitted revision caps.<br>• Flags **dangerous ambiguous phrasing** (`A1..An`) with one-click bulletproof rewrites. | Catches traps like *"minor adjustments as needed"* and rewrites them to *"up to 2 rounds of design revisions, capped at 4 hours total"*. |
| **2** | **Client Request Checker** | **During the Project** | • Splits compound client messages into atomic, single-action requests.<br>• Matches requests against agreed pages, features, and exclusions.<br>• Issues **traffic-light verdicts** (🟢 Included, 🔴 Billable Extra, 🟡 Clarification Needed) with 0% false accusations. | When a client asks to *"fix the mobile menu and also add a blog section"*, it separates them: menu fix is 🟢 Included, blog is 🔴 Billable Extra. |
| **3** | **Priced Reply & Change-Order Generator** | **Closing the Deal** | • Automatically calculates extra billable hours and fees from your hourly rate.<br>• Drafts polite pushback emails in your preferred tone (**Friendly** or **Formal**).<br>• Code-generates itemized, ready-to-sign Markdown Change Orders (`change_order.md`). | Generates: *"I'd love to build the blog! That falls outside the agreed 5-page scope. Here is Change Order #1 for 6 hours ($450). Reply 'APPROVED' to proceed."* |
| **4** | **Live Quota Tracker & Audit Log** | **Throughout the Project** | • Automatically decrements your available revision budget when changes are approved (e.g. `1 / 2 rounds consumed`).<br>• Maintains a local JSON chronological audit trail of all approved requests. | When a client asks for a 3rd round of changes, the system flags that their 2-round quota is exhausted and prompts a billable change order. |

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.10+** (tested on Python 3.13)
- **[Ollama](https://ollama.com)** installed and running locally
- **Git**

### 2. Pull Local Open-Weight Model
Scope-Creep Catcher is optimized for fast, accurate local CPU execution using **Qwen 2.5 (3B)**:
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

### Why This Principle Is Essential
When managing client contracts and billing, relying on a raw language model to decide whether work is included or extra causes three catastrophic failure modes:
1. **Hallucinated Clauses:** LLMs invent contract terms or conditions that were never agreed upon.
2. **Arithmetic Inconsistency:** LLMs cannot guarantee mathematical precision for billable hours, rates, and totals.
3. **Tone Bias (Sycophancy):** When clients write polite or persuasive emails (*"Could you quickly do this tiny favor?"*), LLMs are easily swayed by tone and mistakenly classify billable work as included.

In client services, a single false accusation of scope creep destroys professional trust. Conversely, failing to catch out-of-scope work results in unpaid labor.

### The Architectural Solution: Strict Separation of Concerns
To eliminate these risks, Scope-Creep Catcher enforces a strict separation between linguistic parsing and legal/financial decision-making:

| Responsibility | Component | Exact Technical Function |
|---|---|---|
| **Reading & Structuring** | **Local LLM (`qwen2.5:3b`)** | Translates unstructured human language (in contracts and compound emails) into validated, strongly-typed Pydantic data schemas. Suggests an initial semantic interpretation. |
| **Verification & Rulings** | **Deterministic Python Code (`engine/`)** | Verifies verbatim text citations with RapidFuzz, applies 9 contract rules (`R0`–`R8`) that strictly override the model, computes billing math ($h \times \text{rate}$), and issues the binding verdict. |

> **Core Constraint:** The LLM is strictly an information extractor. It is never permitted to issue a final verdict or calculate billing prices. **Deterministic Python code always has final authority.**

---

## ⚙️ How the Engine Works: The 8-Step Assembly Line (`S1` → `S8`)

When you run Scope-Creep Catcher, there are two main parts:
1. **The Frontend (`app.py`):** The visual Streamlit dashboard you interact with in your browser.
2. **The Backend Engine (`engine/`):** The Python processing machinery under the hood that parses contracts, checks quotes, enforces rules, and runs calculations.

### Automated 8-step assembly line `S1` to `S8`
The Engine is an **automated 8-step assembly line**. Every contract and client message passes through these sequential steps:

```
[ SOW Contract Text ] ──> S1: Fact Extraction (AI reads text into structured schema)
                               │
                               ├──> S2: Stress Test (Lexicon scan + missing clause check)
                               │
[ Client Email/Message ] ──> S3: Message Splitter (AI breaks email into single requests)
                               │
                               ├──> S4: Scope Matcher (AI suggests a tentative opinion)
                               │       │
                               │       ▼
                               └──> S5: Code Rule Engine (Python inspects AI & overrides errors)
                                       │   (Rules R0-R8 enforce contract boundaries in pure code)
                                       │
                                       ├──> S6: Pricing Engine (Python computes: Hours × Rate)
                                       │
                                       ├──> S7: Response Drafter (AI writes email + Code Number Guard)
                                       │
                                       └──> S8: Project Ledger (Python saves audit state to disk)
```

### The 8 Steps Explained Step-by-Step

#### `Step 1 (S1): Structured SOW Fact Extraction` (`engine/sow.py`)
- **What happens:** When you upload or paste a contract (Statement of Work), the AI reads the messy text and extracts 12 essential contract facts into a structured, validated Pydantic schema (`SOWFacts`: agreed pages, revision round limits, deliverables, explicit exclusions, deadlines, payment terms, client responsibilities).
- **Safety Guard:** If the small local model leaves a standard field blank, deterministic Python regex fallbacks automatically find and fill it. Every extracted quote is verified verbatim against the raw text using Unicode NFKC normalization and RapidFuzz string alignment. Unverifiable citations are nulled out to prevent hallucinated clauses.

#### `Step 2 (S2): Pre-Flight Contract Stress Test` (`engine/stress_test.py`)
- **What happens:** Before you sign the contract, this step stress-tests it for traps using a 3-layer merged scan:
  - *Layer 1 (Code):* Scans `config/lexicon.yaml` for dangerous open-ended words (*"as needed"*, *"until satisfied"*).
  - *Layer 2 (AI):* Evaluates realistic dispute risks, writing concrete Freelancer vs. Client interpretations with copyable contract rewrites.
  - *Layer 3 (Code):* Detects missing protective clauses (`M1..Mn`) like missing revision caps or undefined delivery dates.
- **Output:** Up to 5 prioritized risk cards assigned persistent IDs (`A1..A5`) that cross-link directly into mid-project request checking.

#### `Step 3 (S3): Atomic Request Splitter` (`engine/checker.py`)
- **What happens:** Clients rarely send single, clean requests—they send messy compound emails (e.g., *"Can you fix the header button, build a new blog page, and deliver by Friday?"*).
- **Action:** The AI breaks compound messages apart into distinct, single-action `SplitRequest` items, tagging each with its request type (`new_page`, `revision`, `new_feature`, `timeline_change`) and magnitude (`tweak`, `substantial`, `unclear`).

#### `Step 4 (S4): Semantic Scope Matcher` (`engine/checker.py`)
- **What happens:** Compares each atomic request against the agreed deliverables from Step 1.
- **Domain Intelligence:** Injects specialized industry profiles ([skills/web_dev.md](skills/web_dev.md), [skills/copywriting.md](skills/copywriting.md)) so the AI understands standard industry practices (e.g., recognizing that fixing responsive mobile CSS is an included bugfix, but adding an e-commerce shopping cart is a billable new feature).
- **Output:** The AI provides an initial *tentative opinion* (`in_scope`, `out_of_scope`, or `gray_area`). **However, this is NOT the final verdict!**

#### `Step 5 (S5): The Deterministic Rule Engine & Quote Verifier` (`engine/rules.py` & `engine/verifier.py`)
- **What happens:** **This is where Python code takes over from the AI.** Python rules `R0` through `R8` inspect the AI's tentative opinion against hard contract boundaries.
- **The Override:** If the AI was tricked by polite client phrasing, Python code overrides the AI and forces the legally correct verdict (detailed below).

#### `Step 6 (S6): Deterministic Pricing Engine` (`engine/pricing.py`)
- **What happens:** Pure Python math calculates extra billable hours and fees (`hours * hourly_rate`). Hours are looked up deterministically from standard complexity tiers (`config/hours.yaml`), eliminating AI arithmetic hallucinations and random pricing drift.

#### `Step 7 (S7): Client Response Writer & Change Order Drafter` (`engine/drafter.py`)
- **What happens:** Generates professional client communication:
  - For `in_scope`: Drafts a friendly confirmation that the work is covered.
  - For `gray_area`: Drafts polite clarifying questions before starting work.
  - For `out_of_scope`: Explains the scope boundary politely and attaches an itemized **Change Order** with sign-off instructions.
- **Number Guard:** A Python regex guard double-checks that the hours and dollar amounts in the generated email text *exactly match* the numbers computed by the pricing engine in Step 6.

#### `Step 8 (S8): Project Ledger & Quota Tracker` (`engine/state.py`)
- **What happens:** Automatically updates project records in `data/projects/{project_id}.json`. When revision requests are approved, it decrements the client's revision quota (e.g. `1 / 2 rounds consumed`), and updates the persistent audit trail.

---

## 🛡️ Step 5 Deep Dive: Where Contract Rules Live & How They Override the AI

### Exactly Where Do These Rules Fit in the Pipeline?
Notice the critical position of Step 5:
```
[ Step 4: AI Tentative Suggestion ]
                 │
                 ▼
[ STEP 5: PYTHON RULE ENGINE (engine/rules.py) ]  <─── HERE IS WHERE CODE OVERRIDES AI
                 │
                 ▼
[ Step 6: Pricing Engine & Change Order ]
```
In Step 4, the AI generates a guess. But because LLMs can be tricked by polite wording or suffer from contract amnesia, **Step 5 sits between the AI and the client output as a hard firewall**.

### How Code Overrides the AI (Real-World Before & After Examples)

To understand where and why rules make changes, consider these actual examples from the empirical evaluation benchmark:

| Real-World Scenario | What the AI Guessed in Step 4 | Which Rule Triggered in Step 5? | What Code Changed (The Final Verdict) | Why Code Overrode the AI |
|---|:---:|:---:|:---:|---|
| **Client asks for SEO meta tags, but SOW says: `"Excluded: Search engine optimization (SEO)"`** | 🟢 `in_scope`<br>*(AI thinks SEO is a common web task)* | **`R1: Explicit Exclusion`** | 🔴 **`out_of_scope`** | The contract explicitly excluded SEO. The AI was swayed by general web norms, but Python code saw the exact exclusion and forced an extra billable charge. |
| **Client requests a 3rd round of layout revisions, but SOW allows `"Up to 2 revision rounds"`** | 🟢 `in_scope`<br>*(AI sees word "revision" and assumes free)* | **`R3: Revision Quota Enforcement`** | 🔴 **`out_of_scope`** | Python checked the project ledger (`data/projects/`) and saw `rounds_used (2) >= rounds_max (2)`. Free revisions were exhausted. |
| **AI cites a contract sentence to justify extra work, but the quote does not exist in the contract** | 🔴 `out_of_scope`<br>*(AI hallucinates a clause)* | **`R0: Quote Verification Guard`** | 🟡 **`unverified`** | Python's RapidFuzz verifier proved the cited quote was an AI hallucination. Code nulls the citation so the freelancer never sends a fake claim to the client. |
| **Client asks for a completely new `"Affiliate Dashboard"` not in the 4 agreed pages** | 🟡 `gray_area`<br>*(AI waffles because client asked nicely)* | **`R2: Unlisted Page`** | 🔴 **`out_of_scope`** | Python checked the approved page list `['Home', 'About', 'Pricing', 'Contact']`. The dashboard was not on the list. Code strictly labeled it billable extra work. |

### The 9 Deterministic Rules in Strict Execution Priority (`R0` → `R8`)

The rule engine in `engine/rules.py` evaluates these 9 checks in strict sequence:

| Priority | Rule ID | Rule Name | Trigger Condition | Code Action & Verdict Override |
|:---:|:--- |:--- |:--- |:--- |
| **1** | **`R0`** | **Quote Verification Guard** | The AI quotes text that does not exist verbatim in the contract or email. | Immediately forces **`unverified`** to stop AI hallucinations from reaching the client. |
| **2** | **`R1`** | **Explicit Exclusion** | The request matches an item listed in the SOW's `Excluded:` section. | Overrides the AI and strictly forces **`out_of_scope`**. |
| **3** | **`R2`** | **Unlisted Page** | The client asks for a new screen/page not in the agreed SOW page list. | Overrides the AI and strictly forces **`out_of_scope`** (or `gray_area` if no page list was defined). |
| **4** | **`R3`** | **Revision Quota Enforcement** | The client has already used up all agreed revision rounds (e.g. 2 of 2 used). | Overrides the AI and strictly forces **`out_of_scope`**. If revision rounds were left undefined in SOW, forces **`gray_area`**. |
| **5** | **`R4`** | **Vague Revision Dispute Guard** | Client asks for a major redesign under subjective wording (*"tweak until happy"*). | Overrides the AI and forces **`gray_area`**, cross-linking to the exact warning card `A1` from Step 2. |
| **6** | **`R5`** | **Unlisted Deliverable** | Client asks for a major standalone feature not mentioned in deliverables. | Overrides the AI and strictly forces **`out_of_scope`**. |
| **7** | **`R6`** | **Timeline Change** | Client requests a deadline change or delivery acceleration. | Deadlines require mutual agreement; forces **`gray_area`**. |
| **8** | **`R7`** | **Low Confidence Fallback** | The AI reports low confidence and no hard rule applies. | Safely defaults to **`gray_area`** instead of falsely accusing the client. |
| **9** | **`R8`** | **Code Always Wins** | Any discrepancy between Python rules and the AI's proposal. | Python code verdict takes absolute precedence over the model's opinion. |

---

## 💻 Streamlit UI Features

### 1. Sidebar Project Configuration
- **Project Name & Local Storage**: Automatically saves session state to `data/projects/{name}.json`.
- **Hourly Rate & Currency**: Supports USD ($), EUR (€), GBP (£), INR (₹), and AUD (A$).
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

## 🛠️ Technology Stack

| Layer | Technology | Purpose & Implementation |
| :--- | :--- | :--- |
| **Core Language** | **Python 3.10+** (Tested on Python 3.13) | Backend architecture, rule engine, pricing math, and file persistence. |
| **User Interface** | **Streamlit** (`streamlit>=1.38`) | Clean, responsive, wide-layout web dashboard with 3 dedicated workflow tabs. |
| **Local AI Engine** | **Ollama** (`ollama>=0.3.3`) | Local open-weight LLM execution (`qwen2.5:3b`, `gemma2:2b`) running 100% offline. |
| **Schema Validation**| **Pydantic v2** (`pydantic>=2.8`) | Strict JSON-schema constrained decoding for structured model responses. |
| **Text Matching** | **RapidFuzz** (`rapidfuzz>=3.9`) | 3-tier verbatim quote verification and fuzzy token alignment with number token guards. |
| **Configuration** | **PyYAML** (`pyyaml>=6.0`) | Domain complexity hours (`config/hours.yaml`) and risk lexicons (`config/lexicon.yaml`). |
| **Cloud Eval Harness**| **Backboard SDK** (`backboard-sdk>=1.5`) | Async cloud benchmark harness evaluating 70B models strictly on synthetic data. |
| **Observability** | **Entire CLI** (`entire.io`) | Local agent observability capturing prompts, tool calls, and git checkpoints. |
| **Testing** | **Pytest & Pytest-Cov** | Deterministic test suite with 100 passing unit tests. |

---

## 📁 Repository Directory & File Structure

```text
scope-creep-catcher/
├── app.py                      # Main Streamlit web application (UI & Tab Routing)
├── engine/                     # Core backend engine ("LLM Reads, Code Decides")
│   ├── config.py               # Model settings, context sizes, and directory paths
│   ├── sow.py                  # Step 1 (S1): SOW extraction & regex fallback
│   ├── stress_test.py          # Step 2 (S2): SOW ambiguity & missing clause scan
│   ├── checker.py              # Step 3 & 4 (S3-S4): Atomic request splitter & matcher
│   ├── rules.py                # Step 5 (S5): 9 Deterministic contract rules (R0-R8)
│   ├── verifier.py             # 3-Tier quote verifier & number token mismatch guard
│   ├── pricing.py              # Step 6 (S6): Hours estimation & price calculation
│   ├── drafter.py              # Step 7 (S7): Email drafter & change-order generator
│   ├── state.py                # Step 8 (S8): Project persistence & quota audit tracker
│   ├── schemas.py              # Pydantic v2 schemas passed to Ollama format
│   ├── lexicon.py              # Loads and scans subjective contract phrasing
│   └── llm.py                  # Single robust wrapper around Ollama chat API
├── eval/                       # Model selection evaluation lab & benchmark harness
│   ├── run_eval.py             # Evaluates local Ollama models (Baseline vs. Pipeline)
│   ├── run_backboard.py        # Evaluates cloud benchmark via Backboard.io (synthetic only)
│   ├── metrics.py              # Strict grading: Accuracy, False Accusation Rate (FAR), Confusion Matrix
│   └── make_report.py          # Automatically compiles results into RESULTS.md
├── data/
│   ├── gold/                   # 23 Synthetic gold benchmark test cases and SOWs
│   │   ├── cases.json          # Ground-truth labeled requests across dev/test splits
│   │   └── sows/               # Synthetic Statements of Work (bakery, auth, CRM, etc.)
│   └── projects/               # Local JSON project files storing state & quota history
├── config/
│   ├── hours.yaml              # Complexity hour lookup tables (S, M, L)
│   └── lexicon.yaml            # Lexicon of dangerous, ambiguous contract terms
├── skills/                     # Domain knowledge profiles injected during matching
│   ├── web_dev.md              # Web development scope boundaries and standards
│   └── copywriting.md          # Copywriting revision boundaries and norms
├── tests/                      # 100 Deterministic offline unit tests (100% passing)
├── results/
│   ├── RESULTS.md              # Official benchmark report card & confusion matrices
│   └── raw/                    # Raw JSON execution logs from all model evaluations
├── requirements.txt            # Python dependencies
└── README.md                   # Comprehensive project documentation
```

---

---

## 🤝 Hacktoberfest Partner Technologies & The Evaluation Story

Scope-Creep Catcher was designed for the **Hacktoberfest Open-Source AI Challenge, Week 2: Side Hustle**. The challenge featured three designated partner technologies:
- 🌟 **Google Gemma 2** (Featured Partner: Open-Weight Models)
- ☁️ **Backboard.io** (Featured Partner: AI Cloud Infrastructure & Memory)
- 🔍 **Entire.io** (Featured Partner: Agent Observability)

### 🛡️ The Privacy Firewall: 100% Offline Runtime vs. Cloud Evaluation

A fundamental principle of this project is that **freelancers' client contracts, rates, and emails must remain strictly confidential**. Therefore, I built an architectural firewall between the production app and developer benchmarking:

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. PRODUCTION RUNTIME (Freelancers / Streamlit App: app.py)            │
│    • Real Client Contracts, Rates & Messages                           │
│    • 100% Local, Offline & Private (Ollama on CPU)                     │
│    • NO Cloud APIs, NO Internet Needed, ZERO Data Leaks                │
└────────────────────────────────────────────────────────────────────────┘

                                 VS.

┌────────────────────────────────────────────────────────────────────────┐
│ 2. DEVELOPER BENCHMARK (eval/run_backboard.py)                         │
│    • Synthetic Public Test Cases ONLY (data/gold/cases.json)           │
│    • Backboard.io Cloud Platform (evaluating Llama 3.1 70B Cloud)      │
│    • Measures how a giant 70B cloud model compares to a laptop model   │
│    • Real client projects in data/projects/ NEVER touch Backboard      │
└────────────────────────────────────────────────────────────────────────┘
```

1. **Production Runtime is 100% Offline:** When freelancers use the Streamlit application ([app.py](app.py)), all parsing, decision rules, and change order generations execute entirely offline on local Ollama weights. Wi-Fi can be completely turned off.
2. **Backboard is Strictly for Synthetic Benchmarking:** `eval/run_backboard.py` sends only public, synthetic benchmark cases ([data/gold/cases.json](data/gold/cases.json)) to Backboard to empirically measure how pure cloud models perform versus local deterministic pipelines.

---

## 🏆 Model Selection Decision Flow: How I Chose the Engine Model

When building an AI tool for solo freelancers, choosing an LLM cannot be based on guesswork or hype. I followed a strict **5-stage engineering decision process** to evaluate and choose the right engine:

### Stage 1: Hardware & Privacy Constraints (CPU vs. GPU)
Freelancers and solo agency owners do not carry $10,000 GPU servers. They work on standard laptops (MacBooks, Intel/AMD CPUs with 8GB to 16GB of RAM) often in coffee shops or while traveling.
* **100% Offline & Private:** Client contracts and billing rates are strictly confidential; no data could be sent to external cloud APIs during daily use.
* **CPU Execution:** The model had to run smoothly on a standard laptop CPU without thermal throttling or heavy lag.
* **Model Class (2B–3B parameters):** Large 7B+ models are too slow and resource-heavy for CPU execution, so I restricted the search to the modern **2B to 3B parameter class** running locally via [Ollama](https://ollama.com).

### Stage 2: Narrowing Down to the 2 Viable Contenders
Looking at the open-weight ecosystem, two standout models met the CPU and memory criteria:
1. **Google Gemma 2 (2B)** (`gemma2:2b`): Google's cutting-edge compact architecture, and a **featured Hacktoberfest partner model**. Extremely lightweight and fast on consumer laptops.
2. **Qwen 2.5 (3B)** (`qwen2.5:3b`): Alibaba's compact model renowned for outstanding structured JSON instruction-following and coding logic.

### Stage 3: The Empirical Tournament (`eval/`)
Rather than simply picking the featured partner model blindly, I built an automated benchmark suite (`eval/`) with **23 synthetic real-world freelance contract scenarios** (`data/gold/cases.json`) across web dev, copywriting, and media production.

To see whether a laptop model could even compete with cloud giants, I also used **Backboard.io** (cloud partner) to evaluate a massive 70-billion-parameter cloud model (`meta-llama/llama-3.1-70b-instruct`) on the exact same synthetic test cases.

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
   │    • Qwen 2.5 3B          │                   │    • Llama 3.1 70B Cloud  │
   │    • Google Gemma 2 2B    │                   │    • Backboard.io Partner │
   │    • Tested Offline       │                   │    • Synthetic Data Only  │
   └─────────────┬─────────────┘                   └─────────────┬─────────────┘
                 │                                               │
                 │      Raw Execution Logs (results/raw/*.json)  │
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
                         │    Selects the Winner         │
                         └───────────────┬───────────────┘
                                         │
                                         ▼
                         ┌───────────────────────────────┐
                         │ 6. FINAL PRODUCTION APP       │
                         │    qwen2.5:3b locked into     │
                         │    engine/config.py & app.py  │
                         └───────────────────────────────┘
```

### Stage 4: Test Findings & The Issues Discovered with Gemma 2
When running `gemma2:2b` through the evaluation pipeline, three concrete technical issues emerged:
1. **Field Omissions in SOW Parsing:** Gemma 2:2b frequently dropped required fields (such as `pages`, `revision_rounds`, and `client_responsibilities`) during contract extraction. I had to write extensive regex fallbacks in `engine/sow.py` specifically to rescue fields that Gemma omitted.
2. **Paraphrasing vs. Verbatim Quotes:** When citing contract clauses, Gemma tended to paraphrase rather than copying verbatim text. This caused the deterministic RapidFuzz verifier to reject citations as unverified.
3. **The 14.3% False Accusation Rate (FAR):** In freelance client management, falsely accusing a client of scope creep on work they already paid for is catastrophic. Gemma 2:2b scored only 33.3% test accuracy and falsely accused clients in **14.3% of test cases**.

### Stage 5: Final Production Selection (Qwen 2.5 3B)
In contrast, `qwen2.5:3b` solved all three issues:
* Followed strict Pydantic JSON schemas reliably without dropping fields.
* Extracted high-fidelity verbatim quotes that passed RapidFuzz verification.
* Achieved **60.0% pipeline accuracy** on the test suite (nearly double Gemma's 33.3%).
* Achieved a **0.0% False Accusation Rate (zero false accusations)** under the rule engine.

**Final Decision:**  
I selected **`qwen2.5:3b`** as the default production model in `engine/config.py` and `app.py`. At the same time, I preserved full compatibility for **`gemma2:2b`** (`ollama pull gemma2:2b`), so users who prefer Google's ultra-lightweight partner model can still run it seamlessly.

---

### 🧪 The `eval/` Benchmark Suite
The `eval/` directory is the automated testing lab used to measure model accuracy and client safety before deploying to production:
* **`data/gold/cases.json`**: 23 synthetic, professionally written freelance contract scenarios with ground-truth verdicts across web dev, copywriting, and design.
* **`eval/run_eval.py`**: Benchmarks local Ollama models (`qwen2.5:3b`, `gemma2:2b`) in both raw baseline and full pipeline modes.
* **`eval/run_backboard.py`**: Evaluates the cloud 70B model baseline via Backboard.io strictly using public synthetic test cases.
* **`eval/metrics.py`**: Calculates classification accuracy and the critical **False Accusation Rate (FAR)** to ensure no client is wrongly charged.
* **`eval/make_report.py`**: Compiles all raw evaluation runs from `results/raw/` into the consolidated report at **[results/RESULTS.md](results/RESULTS.md)**.

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
- **`qwen2.5:3b` achieves 0.0% False Accusations** under the deterministic rule engine on the test split. Falsely accusing a client of scope creep destroys professional relationships; the rule engine guarantees safety.
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

