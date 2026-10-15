# Scope-Creep Catcher — Evaluation Results

> **Note:** Gold set is self-written (synthetic). n is small (~23 requests).
> Accuracy has roughly ±13 percentage points of uncertainty.
> Do not overinterpret small differences between models or modes.

## Summary Table

| Model | Mode | Split | N | Accuracy | False Accusation Rate |
|-------|------|-------|---|----------|----------------------|
| gemma2:2b | baseline | dev | 8 | 75.0% | 0.0% |
| gemma2:2b | baseline | test | 15 | 60.0% | 14.3% |
| gemma2:2b | pipeline | dev | 8 | 50.0% | 0.0% |
| gemma2:2b | pipeline | test | 15 | 33.3% | 14.3% |


## gemma2:2b | baseline | dev

- **Accuracy:** 75.0%
- **False accusation rate:** 0.0%
- **Per difficulty:** {'obvious': 0.6667, 'subtle': 1.0}

### Confusion Matrix

| Actual \ Predicted | in_scope | out_of_scope | gray_area | unverified |
|---|---|---|---|---|
| in_scope | 1 | 0 | 1 | 0 |
| out_of_scope | 0 | 3 | 1 | 0 |
| gray_area | 0 | 0 | 2 | 0 |
| unverified | 0 | 0 | 0 | 0 |

## gemma2:2b | baseline | test

- **Accuracy:** 60.0%
- **False accusation rate:** 14.3%
- **Per difficulty:** {'obvious': 0.6667, 'subtle': 0.3333}

### Confusion Matrix

| Actual \ Predicted | in_scope | out_of_scope | gray_area | unverified |
|---|---|---|---|---|
| in_scope | 1 | 0 | 3 | 0 |
| out_of_scope | 0 | 6 | 2 | 0 |
| gray_area | 0 | 1 | 2 | 0 |
| unverified | 0 | 0 | 0 | 0 |

## gemma2:2b | pipeline | dev

- **Accuracy:** 50.0%
- **False accusation rate:** 0.0%
- **Per difficulty:** {'obvious': 0.3333, 'subtle': 1.0}

### Confusion Matrix

| Actual \ Predicted | in_scope | out_of_scope | gray_area | unverified |
|---|---|---|---|---|
| in_scope | 0 | 0 | 2 | 0 |
| out_of_scope | 0 | 2 | 2 | 0 |
| gray_area | 0 | 0 | 2 | 0 |
| unverified | 0 | 0 | 0 | 0 |

## gemma2:2b | pipeline | test

- **Accuracy:** 33.3%
- **False accusation rate:** 14.3%
- **Per difficulty:** {'obvious': 0.3333, 'subtle': 0.3333}

### Confusion Matrix

| Actual \ Predicted | in_scope | out_of_scope | gray_area | unverified |
|---|---|---|---|---|
| in_scope | 0 | 1 | 1 | 2 |
| out_of_scope | 0 | 2 | 5 | 1 |
| gray_area | 0 | 0 | 3 | 0 |
| unverified | 0 | 0 | 0 | 0 |

---

## Limitations

- Gold set is self-written, not independently labelled.
- n ≈ 23 requests total (dev + test combined).
- Hour estimates are illustrative — not real project quotes.
- The quote verifier catches fabricated citations but not wrong reasoning.
- This is not legal advice.
