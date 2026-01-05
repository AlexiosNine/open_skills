"""Skill Runners - execution strategies for different skill types."""

from .base import SkillRunner
from .cli_python import CLIPythonRunner

__all__ = ["SkillRunner", "CLIPythonRunner", "RunnerFactory"]


class RunnerFactory:
    """Factory for creating appropriate runners based on skill manifest."""

    def __init__(self):
        self._runners: dict[str, SkillRunner] = {}

    def get_runner(self, manifest) -> SkillRunner:
        """
        Get a runner for the given skill manifest.

        Args:
            manifest: SkillManifest object

        Returns:
            SkillRunner instance

        Raises:
            ValueError: If no runner is available for the manifest type/runtime
        """
        # Create a key from type and runtime
        key = f"{manifest.type}:{manifest.runtime}"

        # Return cached runner or create new one
        if key not in self._runners:
            runner = self._create_runner(manifest)
            self._runners[key] = runner

        return self._runners[key]

    def _create_runner(self, manifest) -> SkillRunner:
        """
        Create a runner instance based on manifest.

        Args:
            manifest: SkillManifest object

        Returns:
            SkillRunner instance

        Raises:
            ValueError: If runner type/runtime is not supported
        """
        if manifest.type == "cli" and manifest.runtime == "python":
            return CLIPythonRunner()

        # Future extensions:
        # elif manifest.type == "cli" and manifest.runtime == "exec":
        #     return CLIExecRunner()
        # elif manifest.type == "http":
        #     return HTTPRunner()
        # elif manifest.type == "docker":
        #     return DockerRunner()
        # elif manifest.type == "inproc":
        #     return InProcRunner()

        raise ValueError(
            f"Unsupported runner type: {manifest.type}:{manifest.runtime}"
        )


# Global factory instance
_factory: RunnerFactory | None = None


def get_factory() -> RunnerFactory:
    """Get the global runner factory instance."""
    global _factory
    if _factory is None:
        _factory = RunnerFactory()
    return _factory

