# Scope-Creep Catcher — Evaluation Results

> **Note:** Gold set is self-written (synthetic). n is small (~23 requests).
> Accuracy has roughly ±13 percentage points of uncertainty.
> Do not overinterpret small differences between models or modes.

## Summary Table

| Model | Mode | Split | N | Accuracy | False Accusation Rate |
|-------|------|-------|---|----------|----------------------|
| gemma2:2b | pipeline | dev | 8 | 12.5% | 0.0% |


## gemma2:2b | pipeline | dev

- **Accuracy:** 12.5%
- **False accusation rate:** 0.0%
- **Per difficulty:** {'obvious': 0.1667, 'subtle': 0.0}

### Confusion Matrix

| Actual \ Predicted | in_scope | out_of_scope | gray_area | unverified |
|---|---|---|---|---|
| in_scope | 0 | 0 | 1 | 1 |
| out_of_scope | 0 | 1 | 2 | 1 |
| gray_area | 0 | 0 | 0 | 2 |
| unverified | 0 | 0 | 0 | 0 |

---

## Limitations

- Gold set is self-written, not independently labelled.
- n ≈ 23 requests total (dev + test combined).
- Hour estimates are illustrative — not real project quotes.
- The quote verifier catches fabricated citations but not wrong reasoning.
- This is not legal advice.
