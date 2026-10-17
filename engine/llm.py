"""
engine/llm.py
Single wrapper for every Ollama model call.
- JSON-schema constrained output via Pydantic
- One automatic retry on validation failure
- Latency and token metrics recorded to results/raw/metrics.jsonl
"""
from __future__ import annotations

import time
from typing import Type, TypeVar

import ollama
from pydantic import BaseModel, ValidationError

from .config import MODEL, NUM_CTX, SEED, METRICS, MAX_TOKENS_DEFAULT

T = TypeVar("T", bound=BaseModel)


def call_json(
    schema: Type[T],
    system: str,
    user: str,
    step: str,
    model: str | None = None,
    max_tokens: int = MAX_TOKENS_DEFAULT,
) -> T:
    """
    Call Ollama with JSON-schema constrained output.

    Args:
        schema:     Pydantic model class; its JSON schema is passed to Ollama.
        system:     System-role prompt text.
        user:       User-role prompt text.
        step:       Human-readable step name for metrics (e.g. "S1_extract").
        model:      Override the default model (useful for eval comparisons).
        max_tokens: Cap on output tokens.

    Returns:
        Validated instance of `schema`.

    Raises:
        RuntimeError: If both the initial call and the retry fail validation.
    """
    resolved_model = model or MODEL
    msgs: list[dict] = [
        {"role": "system", "content": system},
        {"role": "user",   "content": user},
    ]
    last_err: Exception | None = None

    for attempt in range(2):           # original + one retry
        print(f"[LLM] {step} | attempt {attempt + 1}/2 | model={resolved_model} | max_tokens={max_tokens}", flush=True)
        t0 = time.perf_counter()
        try:
            print(f"[LLM] Sending request to Ollama...", flush=True)
            response = ollama.chat(
                model=resolved_model,
                messages=msgs,
                format=schema.model_json_schema(),
                options={
                    "temperature": 0,
                    "repeat_penalty": 1.1,
                    "seed": SEED,
                    "num_ctx": NUM_CTX,
                    "num_predict": max_tokens,
                },
            )
        except Exception as exc:
            print(f"[LLM] ERROR on attempt {attempt + 1}: {exc}", flush=True)
            raise RuntimeError(
                f"{step}: Ollama call failed (attempt {attempt + 1}): {exc}"
            ) from exc

        elapsed = time.perf_counter() - t0
        print(f"[LLM] {step} done in {elapsed:.2f}s | prompt_tokens={response.prompt_eval_count} | output_tokens={response.eval_count}", flush=True)
        METRICS.record(
            step=step,
            model=resolved_model,
            seconds=elapsed,
            prompt_tokens=response.prompt_eval_count,
            output_tokens=response.eval_count,
        )

        raw_content: str = response.message.content
        print(f"[LLM] Raw response ({len(raw_content)} chars): {raw_content[:200]}...", flush=True)
        try:
            parsed = schema.model_validate_json(raw_content)
            print(f"[LLM] Schema validation OK", flush=True)
            return parsed
        except ValidationError as exc:
            last_err = exc
            print(f"[LLM] Schema validation FAILED (attempt {attempt + 1}): {exc.errors()[:3]}", flush=True)
            # On first failure: append error context and retry
            if attempt == 0:
                print(f"[LLM] Retrying with error context...", flush=True)
                msgs += [
                    {"role": "assistant", "content": raw_content},
                    {
                        "role": "user",
                        "content": (
                            f"Your output failed schema validation: "
                            f"{exc.errors()[:3]}. "
                            "Return ONLY valid JSON matching the schema, nothing else."
                        ),
                    },
                ]

    raise RuntimeError(
        f"{step}: LLM output failed schema validation twice. Last error: {last_err}"
    )
