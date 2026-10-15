# Scope-Creep Catcher: Theoretical Foundations & Architecture Rationale

## 1. The Core Philosophy: "LLM Reads, Code Decides"

Modern generative models excel at contextual comprehension, natural language synthesis, and unstructured text parsing. However, when applied to contractual interpretation and billing boundaries, pure LLM systems exhibit critical failure modes:
- **Hallucinated clauses**: Inventing contract terms that sound plausible to justify a verdict.
- **Sycophancy & inconsistency**: Changing verdicts based on subtle prompt rephrasing.
- **Arithmetic errors**: Inaccurately calculating hours, totals, or percentage overruns.
- **Numeric citation drift**: Quoting "3 revision rounds" when the contract states "2 revision rounds" (which standard fuzzy string matching fails to catch).

**Scope-Creep Catcher enforces a strict architectural boundary:**
> **The LLM reads, explains, and writes. Code finds, verifies, decides, and calculates.**

The model is never allowed to perform math, never has the final say on whether work is out-of-scope, and cannot cite a clause that has not been cryptographically verified against the original document text.

---

## 2. The Asymmetry of Errors: Why False Accusations Are Fatal

In freelance client management, errors are not symmetric:

| Error Type | What Happens | Real-World Impact |
|---|---|---|
| **False Negative (Miss)** | An out-of-scope request is classified as in-scope. | The freelancer does 2–4 hours of extra work without charging. Annoying, but relationship preserved. |
| **False Positive (False Accusation)** | An in-scope or reasonable revision is flagged as out-of-scope, prompting a confrontational change order. | The client feels nickel-and-dimed or insulted. Client relationship damaged, contract disputes, non-payment. |

Because **false accusations are far worse than misses**, the architecture prioritizes:
1. **Conservative classification**: If evidence is missing or ambiguous, default to `gray_area` instead of `out_of_scope`.
2. **Abstention over invention**: When the model has low confidence, rule R7 forces a `gray_area` verdict.
3. **Clarifying questions over pushback**: For gray areas, the drafter generates a polite clarifying question rather than a change order.

---

## 3. The 3-Tier Quote Verifier (The Trust Engine)

The verifier (`engine/verifier.py`) ensures that no claim can be made without verbatim textual evidence from the underlying documents.

### Tier 1: Normalized Exact Matching
Input text is normalized using Unicode NFKC normalization, converting typographic quotes (`“`, `”`, `‘`, `’`), em-dashes (`—`), non-breaking spaces (`\u00a0`), and collapsing redundant whitespace while maintaining a bidirectional character index map (`imap`). If the normalized quote exists as a substring of the source, it is accepted with 100% confidence, and exact original start/end character offsets are returned.

### Tier 2: Fuzzy Alignment via RapidFuzz
When OCR artifacts, minor punctuation differences, or client typos prevent an exact match, RapidFuzz `partial_ratio_alignment` is evaluated against a 95% similarity threshold.

### Tier 3: The Number Token Guard (Critical Defense)
Standard fuzzy matching fails catastrophically on numbers. For example:
- Source: `"Includes 2 rounds of revisions"`
- Hallucinated Quote: `"Includes 3 rounds of revisions"`
- Character similarity: **~94%**

Under a standard 90% or 95% fuzzy threshold, a small model hallucinating a different number would pass inspection.

To prevent this, `verifier.py` parses all number tokens from both the candidate quote and the matched window, mapping word numbers (`"two"` $\to$ `"2"`) to numeric digits. **If the numeric token sets differ in any way, the match is rejected immediately with method `number_mismatch` or `not_found`, forcing `ok = False`.**

### What the Verifier Does NOT Catch
The verifier proves **source text fidelity** (that the quoted words actually exist in the contract). It does not prove **semantic validity** (that the cited clause genuinely supports the conclusion). Semantic validity is governed by the deterministic rule engine (R0–R8), skills profiles, and explicit user override controls.

---

## 4. Deterministic Rule Hierarchy (R0–R8)

The rule engine (`engine/rules.py`) enforces contract law best practices deterministically:

1. **R0 (Integrity Guard):** If either the SOW quote or the client quote fails verification, the verdict is forced to `unverified`. No change order or pushback draft can be generated until the freelancer reviews or edits the text.
2. **R1 (Hard Exclusions):** If the request matches an explicitly excluded item in `sow.excluded`, it is unconditionally `out_of_scope`.
3. **R2 (Scope Boundary / Pages):** For `new_page` requests, if a page list exists in the SOW and the requested page is not on it, it is classified `out_of_scope`. If no page list exists, it is marked `gray_area`.
4. **R3 (Quota & Revision Limits):** If revisions are used up (`revisions_used >= revision_rounds`), revisions become `out_of_scope`. If revision rounds were never defined in the SOW, revisions become `gray_area`.
5. **R4 (Vague Revision Clause):** If a client requests a "substantial" revision and the SOW used vague terms like "minor revisions", it is marked `gray_area` and linked to the ambiguity card.
6. **R5 (Deliverables Boundary):** If a new feature or deliverable was requested that is not listed in deliverables, it is `out_of_scope`.
7. **R6 (Timeline Shift):** A deadline shift (`timeline_change`) is always a conversation, never an out-of-scope accusation $\to$ `gray_area`.
8. **R7 (Confidence Threshold):** If LLM confidence is `low` and no hard rule triggered, default to `gray_area`.
9. **R8 (Hard Rule Conflict Resolution):** If a hard rule (R1–R5) contradicts the LLM proposal, the rule wins and `overridden_by_rule = True`.

---

## 5. Drafting Guard & Change Order Math

In `engine/drafter.py`:
- All pricing and hours are computed via deterministic lookup tables (`config/hours.yaml` and client hourly rate).
- The LLM drafts the conversational wrapper using placeholder tokens (`{PRICE_1}`, `{HOURS_1}`).
- Placeholders are injected by code.
- A **Number Guard** regex scans the entire generated response. If any numeric token appears in the draft that was not explicitly authorized in the decision record, the draft is rejected and regenerated; if it fails twice, a safe fallback template is used.

---

## 6. Local Open-Weights & Privacy Rationale

Freelance contracts contain non-disclosure agreements, proprietary technical architecture, client identities, and pricing terms.
- Sending raw client contracts to third-party proprietary APIs often breaches client confidentiality agreements.
- Local inference via **Ollama (`gemma2:2b`, `qwen2.5:7b`)** ensures **100% data residency**: the SOW and client messages never touch the internet.
- Zero marginal token cost enables continuous real-time analysis for solo practitioners.
