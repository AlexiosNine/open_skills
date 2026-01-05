"""Base runner interface."""

from abc import ABC, abstractmethod

from ..models import NormalizedSkillResult


class SkillRunner(ABC):
    """Abstract base class for skill runners."""

    @abstractmethod
    def invoke(
        self,
        skill_id: str,
        input_data: dict,
        trace_id: str,
        manifest=None,
    ) -> NormalizedSkillResult:
        """
        Invoke a skill.

        Args:
            skill_id: The skill ID
            input_data: The input data dictionary
            trace_id: The trace ID for this invocation
            manifest: Optional SkillManifest for the skill

        Returns:
            NormalizedSkillResult
        """
        pass

