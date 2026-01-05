#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import time
import uuid
from typing import Any, Dict, Optional


SKILL_ID = "echo"
VERSION = "0.1.0"


def _now_ms() -> int:
    return int(time.time() * 1000)


def _make_result(
    *,
    success: bool,
    trace_id: str,
    data: Dict[str, Any] | None = None,
    error: Dict[str, Any] | None = None,
    latency_ms: int | None = None,
) -> Dict[str, Any]:
    return {
        "success": success,
        "skill_id": SKILL_ID,
        "trace_id": trace_id,
        "data": data if success else None,
        "error": None if success else (error or {"code": "INTERNAL", "message": "Unknown error"}),
        "meta": {
            "latency_ms": latency_ms if latency_ms is not None else 0,
            "version": VERSION,
        },
    }


def _read_stdin_text() -> str:
    return sys.stdin.read()


def _extract_trace_id_from_input(input_obj: Any) -> Optional[str]:
    if not isinstance(input_obj, dict):
        return None
    for k in ("trace_id", "_trace_id"):
        v = input_obj.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def _ensure_trace_id(maybe_trace_id: Optional[str]) -> str:
    return maybe_trace_id if (isinstance(maybe_trace_id, str) and maybe_trace_id.strip()) else str(uuid.uuid4())


def main() -> int:
    start = _now_ms()
    trace_id: Optional[str] = None

    try:
        raw = _read_stdin_text()
        if not raw.strip():
            trace_id = _ensure_trace_id(None)
            latency = _now_ms() - start
            result = _make_result(
                success=False,
                trace_id=trace_id,
                error={"code": "INVALID_ARGUMENT", "message": "Empty stdin"},
                latency_ms=latency,
            )
            sys.stdout.write(json.dumps(result, ensure_ascii=False))
            return 1

        try:
            req = json.loads(raw)
        except json.JSONDecodeError as e:
            trace_id = _ensure_trace_id(None)
            latency = _now_ms() - start
            result = _make_result(
                success=False,
                trace_id=trace_id,
                error={
                    "code": "INVALID_JSON",
                    "message": "Failed to parse stdin as JSON",
                    "details": {"pos": e.pos, "lineno": e.lineno, "colno": e.colno},
                },
                latency_ms=latency,
            )
            sys.stdout.write(json.dumps(result, ensure_ascii=False))
            return 2

        if not isinstance(req, dict):
            trace_id = _ensure_trace_id(None)
            latency = _now_ms() - start
            result = _make_result(
                success=False,
                trace_id=trace_id,
                error={"code": "INVALID_ARGUMENT", "message": "stdin JSON must be an object"},
                latency_ms=latency,
            )
            sys.stdout.write(json.dumps(result, ensure_ascii=False))
            return 1

        payload = req.get("input")
        trace_id = _ensure_trace_id(_extract_trace_id_from_input(payload))

        if not isinstance(payload, dict):
            latency = _now_ms() - start
            result = _make_result(
                success=False,
                trace_id=trace_id,
                error={"code": "INVALID_ARGUMENT", "message": 'Missing or invalid "input" object'},
                latency_ms=latency,
            )
            sys.stdout.write(json.dumps(result, ensure_ascii=False))
            return 1

        text = payload.get("text")
        if not isinstance(text, str) or not text.strip():
            latency = _now_ms() - start
            result = _make_result(
                success=False,
                trace_id=trace_id,
                error={
                    "code": "INVALID_ARGUMENT",
                    "message": 'Field "text" is required and must be a non-empty string',
                    "details": {"field": "text"},
                },
                latency_ms=latency,
            )
            sys.stdout.write(json.dumps(result, ensure_ascii=False))
            return 1

        latency = _now_ms() - start
        result = _make_result(
            success=True,
            trace_id=trace_id,
            data={"echoed": text},
            latency_ms=latency,
        )
        sys.stdout.write(json.dumps(result, ensure_ascii=False))
        return 0

    except Exception as e:
        # 兜底：确保 trace_id 始终存在
        trace_id = _ensure_trace_id(trace_id)
        latency = _now_ms() - start
        result = _make_result(
            success=False,
            trace_id=trace_id,
            error={
                "code": "INTERNAL",
                "message": "Unhandled error in echo skill",
                "details": {"exception": type(e).__name__, "reason": str(e)},
            },
            latency_ms=latency,
        )
        sys.stdout.write(json.dumps(result, ensure_ascii=False))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
