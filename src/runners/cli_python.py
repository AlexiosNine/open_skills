"""CLI Python Runner - executes Python scripts as skills."""

import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict

from ..config import config
from ..models import (
    ErrorCode,
    ErrorDetail,
    NormalizedSkillResult,
    SkillManifest,
    SkillMeta,
)
from .base import SkillRunner

logger = logging.getLogger(__name__)


class CLIPythonRunner(SkillRunner):
    """Runner for executing Python CLI scripts."""

    def invoke(
        self,
        skill_id: str,
        input_data: dict,
        trace_id: str,
        manifest: SkillManifest | None = None,
    ) -> NormalizedSkillResult:
        """
        Execute a Python CLI skill.

        Args:
            skill_id: The skill ID
            input_data: The input data dictionary
            trace_id: The trace ID
            manifest: Optional SkillManifest (used for timeout override)

        Returns:
            NormalizedSkillResult
        """
        start_time = time.time()

        # Determine script path
        if manifest and manifest.entry:
            script_path = Path(manifest.entry)
        else:
            script_path = config.get_skill_script_path(skill_id)

        # Check if script exists
        if not script_path.exists():
            latency_ms = int((time.time() - start_time) * 1000)
            return NormalizedSkillResult(
                success=False,
                skill_id=skill_id,
                trace_id=trace_id,
                data=None,
                error=ErrorDetail(
                    code=ErrorCode.NOT_FOUND,
                    message=f"Skill script not found: {script_path}",
                ),
                meta=SkillMeta(latency_ms=latency_ms),
            )

        # Determine timeout
        timeout_ms = (
            manifest.timeout_ms if manifest and manifest.timeout_ms else config.timeout_ms
        )
        timeout_seconds = timeout_ms / 1000.0

        # Prepare input JSON
        try:
            input_json = json.dumps({"input": input_data}, ensure_ascii=False)
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return NormalizedSkillResult(
                success=False,
                skill_id=skill_id,
                trace_id=trace_id,
                data=None,
                error=ErrorDetail(
                    code=ErrorCode.INVALID_ARGUMENT,
                    message="Failed to serialize input to JSON",
                    details={"exception": type(e).__name__, "reason": str(e)},
                ),
                meta=SkillMeta(latency_ms=latency_ms),
            )

        # Execute the script
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                input=input_json,
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                cwd=config.cli_dir.parent,  # Run from project root
            )
        except subprocess.TimeoutExpired:
            latency_ms = int((time.time() - start_time) * 1000)
            return NormalizedSkillResult(
                success=False,
                skill_id=skill_id,
                trace_id=trace_id,
                data=None,
                error=ErrorDetail(
                    code=ErrorCode.TIMEOUT,
                    message=f"Skill execution timed out after {timeout_ms}ms",
                ),
                meta=SkillMeta(latency_ms=latency_ms),
            )
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return NormalizedSkillResult(
                success=False,
                skill_id=skill_id,
                trace_id=trace_id,
                data=None,
                error=ErrorDetail(
                    code=ErrorCode.INTERNAL,
                    message="Failed to execute skill script",
                    details={"exception": type(e).__name__, "reason": str(e)},
                ),
                meta=SkillMeta(latency_ms=latency_ms),
            )

        latency_ms = int((time.time() - start_time) * 1000)

        # Parse output
        output_text = result.stdout.strip()
        if not output_text and result.stderr:
            # Try stderr if stdout is empty
            output_text = result.stderr.strip()

        if not output_text:
            return NormalizedSkillResult(
                success=False,
                skill_id=skill_id,
                trace_id=trace_id,
                data=None,
                error=ErrorDetail(
                    code=ErrorCode.INTERNAL,
                    message="Skill script produced no output",
                    details={
                        "exit_code": result.returncode,
                        "stdout": result.stdout[:200] if result.stdout else None,
                        "stderr": result.stderr[:200] if result.stderr else None,
                    },
                ),
                meta=SkillMeta(latency_ms=latency_ms),
            )

        # Try to parse JSON output
        try:
            output_data = json.loads(output_text)
        except json.JSONDecodeError as e:
            return NormalizedSkillResult(
                success=False,
                skill_id=skill_id,
                trace_id=trace_id,
                data=None,
                error=ErrorDetail(
                    code=ErrorCode.INTERNAL,
                    message="Failed to parse skill output as JSON",
                    details={
                        "exit_code": result.returncode,
                        "json_error": str(e),
                        "output_preview": output_text[:200],
                    },
                ),
                meta=SkillMeta(latency_ms=latency_ms),
            )

        # Validate and adapt the result
        if isinstance(output_data, dict):
            # If it's already a NormalizedSkillResult-like structure, use it
            # Otherwise, wrap it
            if "success" in output_data:
                # Ensure trace_id matches
                output_data["trace_id"] = trace_id
                # Ensure skill_id matches
                output_data["skill_id"] = skill_id
                try:
                    return NormalizedSkillResult(**output_data)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse skill output as NormalizedSkillResult: {e}"
                    )
                    # Fall through to wrap it

            # Wrap the output in a NormalizedSkillResult
            return NormalizedSkillResult(
                success=result.returncode == 0,
                skill_id=skill_id,
                trace_id=trace_id,
                data=output_data if result.returncode == 0 else None,
                error=ErrorDetail(
                    code=ErrorCode.INTERNAL,
                    message=f"Skill script exited with code {result.returncode}",
                    details={"exit_code": result.returncode},
                )
                if result.returncode != 0
                else None,
                meta=SkillMeta(latency_ms=latency_ms),
            )
        else:
            # Non-dict output - wrap it
            return NormalizedSkillResult(
                success=result.returncode == 0,
                skill_id=skill_id,
                trace_id=trace_id,
                data={"output": output_data} if result.returncode == 0 else None,
                error=ErrorDetail(
                    code=ErrorCode.INTERNAL,
                    message=f"Skill script exited with code {result.returncode}",
                    details={"exit_code": result.returncode},
                )
                if result.returncode != 0
                else None,
                meta=SkillMeta(latency_ms=latency_ms),
            )

