#!/usr/bin/env python3
from __future__ import annotations

import json
import statistics
import sys
import time
import uuid
from typing import Any, Dict, Optional


SKILL_ID = "calculator"
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


def _calculate_mean(numbers: list[float]) -> float:
    """Calculate mean (average)."""
    return statistics.mean(numbers)


def _calculate_median(numbers: list[float]) -> float:
    """Calculate median."""
    return statistics.median(numbers)


def _calculate_min(numbers: list[float]) -> float:
    """Calculate minimum."""
    return min(numbers)


def _calculate_max(numbers: list[float]) -> float:
    """Calculate maximum."""
    return max(numbers)


def _calculate_sum(numbers: list[float]) -> float:
    """Calculate sum."""
    return sum(numbers)


def _compare_values(compare: Dict[str, float]) -> Dict[str, Any]:
    """Compare values and return comparison result."""
    if not compare or len(compare) < 2:
        return {}
    
    values = list(compare.values())
    keys = list(compare.keys())
    
    max_key = keys[values.index(max(values))]
    min_key = keys[values.index(min(values))]
    
    return {
        "max": {"key": max_key, "value": max(values)},
        "min": {"key": min_key, "value": min(values)},
        "difference": max(values) - min(values),
    }


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

        # Validate numbers
        numbers = payload.get("numbers")
        if not isinstance(numbers, list) or len(numbers) == 0:
            latency = _now_ms() - start
            result = _make_result(
                success=False,
                trace_id=trace_id,
                error={
                    "code": "INVALID_ARGUMENT",
                    "message": 'Field "numbers" is required and must be a non-empty array',
                    "details": {"field": "numbers"},
                },
                latency_ms=latency,
            )
            sys.stdout.write(json.dumps(result, ensure_ascii=False))
            return 1

        # Convert to float and validate
        try:
            numbers_float = [float(n) for n in numbers]
        except (ValueError, TypeError) as e:
            latency = _now_ms() - start
            result = _make_result(
                success=False,
                trace_id=trace_id,
                error={
                    "code": "INVALID_ARGUMENT",
                    "message": 'Field "numbers" must contain only numeric values',
                    "details": {"field": "numbers", "error": str(e)},
                },
                latency_ms=latency,
            )
            sys.stdout.write(json.dumps(result, ensure_ascii=False))
            return 1

        # Validate ops
        ops = payload.get("ops")
        if not isinstance(ops, list) or len(ops) == 0:
            latency = _now_ms() - start
            result = _make_result(
                success=False,
                trace_id=trace_id,
                error={
                    "code": "INVALID_ARGUMENT",
                    "message": 'Field "ops" is required and must be a non-empty array',
                    "details": {"field": "ops"},
                },
                latency_ms=latency,
            )
            sys.stdout.write(json.dumps(result, ensure_ascii=False))
            return 1

        # Supported operations
        supported_ops = {"mean", "median", "min", "max", "sum"}
        invalid_ops = [op for op in ops if op not in supported_ops]
        if invalid_ops:
            latency = _now_ms() - start
            result = _make_result(
                success=False,
                trace_id=trace_id,
                error={
                    "code": "INVALID_ARGUMENT",
                    "message": f'Unsupported operations: {invalid_ops}. Supported: {sorted(supported_ops)}',
                    "details": {"field": "ops", "invalid_ops": invalid_ops},
                },
                latency_ms=latency,
            )
            sys.stdout.write(json.dumps(result, ensure_ascii=False))
            return 1

        # Perform calculations
        results = {}
        for op in ops:
            if op == "mean":
                results["mean"] = _calculate_mean(numbers_float)
            elif op == "median":
                results["median"] = _calculate_median(numbers_float)
            elif op == "min":
                results["min"] = _calculate_min(numbers_float)
            elif op == "max":
                results["max"] = _calculate_max(numbers_float)
            elif op == "sum":
                results["sum"] = _calculate_sum(numbers_float)

        # Handle comparison if provided
        comparison = None
        compare = payload.get("compare")
        if compare is not None:
            if isinstance(compare, dict):
                try:
                    compare_float = {k: float(v) for k, v in compare.items()}
                    comparison = _compare_values(compare_float)
                except (ValueError, TypeError):
                    # Invalid comparison values, skip
                    pass

        # Build response data
        data: Dict[str, Any] = {"results": results}
        if comparison:
            data["comparison"] = comparison

        latency = _now_ms() - start
        result = _make_result(
            success=True,
            trace_id=trace_id,
            data=data,
            latency_ms=latency,
        )
        sys.stdout.write(json.dumps(result, ensure_ascii=False))
        return 0

    except Exception as e:
        trace_id = _ensure_trace_id(trace_id)
        latency = _now_ms() - start
        result = _make_result(
            success=False,
            trace_id=trace_id,
            error={
                "code": "INTERNAL",
                "message": "Unhandled error in calculator skill",
                "details": {"exception": type(e).__name__, "reason": str(e)},
            },
            latency_ms=latency,
        )
        sys.stdout.write(json.dumps(result, ensure_ascii=False))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

