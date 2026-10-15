"""
engine/tracing.py
Optional Sentry tracing for latency and token metrics.
Off by default (ENABLE_SENTRY=0). When on: send_default_pii=False,
only metadata (model, step, seconds, token counts) goes out — never
prompt or response text, and only synthetic data is used.

This keeps the "nothing leaves your laptop" claim true by default.
"""
from __future__ import annotations

import os

ENABLE_SENTRY = os.environ.get("ENABLE_SENTRY", "0") == "1"

if ENABLE_SENTRY:
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=os.environ.get("SENTRY_DSN", ""),
            send_default_pii=False,
            traces_sample_rate=1.0,
        )
        _sentry_available = True
    except ImportError:
        _sentry_available = False
else:
    _sentry_available = False


def start_span(op: str, description: str) -> object | None:
    """Start a Sentry span if tracing is enabled."""
    if not _sentry_available:
        return None
    try:
        import sentry_sdk
        return sentry_sdk.start_span(op=op, name=description)
    except Exception:
        return None


def record_ai_metadata(span: object | None, model: str, step: str,
                        seconds: float, input_tokens: int | None,
                        output_tokens: int | None) -> None:
    """Record AI metadata on a span. No prompt/response text."""
    if span is None:
        return
    try:
        span.set_attribute("ai.model", model)
        span.set_attribute("ai.step", step)
        span.set_attribute("ai.latency_seconds", seconds)
        if input_tokens is not None:
            span.set_attribute("ai.input_tokens", input_tokens)
        if output_tokens is not None:
            span.set_attribute("ai.output_tokens", output_tokens)
    except Exception:
        pass
