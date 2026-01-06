"""Skill Registry and Manifest Loader."""

import logging
from pathlib import Path
from typing import Dict, Optional

import yaml

from .config import config
from .models import SkillManifest

logger = logging.getLogger(__name__)


class SkillRegistry:
    """Registry for managing skill manifests."""

    def __init__(self, skills_dir: Optional[Path] = None):
        """
        Initialize the registry.

        Args:
            skills_dir: Directory containing skill manifest YAML files
        """
        if skills_dir is None:
            # Default to ./skills relative to project root
            project_root = Path(__file__).parent.parent
            skills_dir = project_root / "skills"

        self.skills_dir = Path(skills_dir)
        self._manifests: Dict[str, SkillManifest] = {}
        self._load_all()

    def _load_all(self) -> None:
        """Load all skill manifests from the skills directory."""
        if not self.skills_dir.exists():
            logger.warning(
                f"Skills directory does not exist: {self.skills_dir}"
            )
            return

        if not self.skills_dir.is_dir():
            logger.warning(
                f"Skills path is not a directory: {self.skills_dir}"
            )
            return

        for yaml_file in self.skills_dir.glob("*.yaml"):
            try:
                manifest = self._load_manifest(yaml_file)
                if manifest:
                    self._manifests[manifest.id] = manifest
                    logger.info(f"Loaded skill manifest: {manifest.id}")
            except Exception as e:
                logger.error(
                    f"Failed to load manifest from {yaml_file}: {e}",
                    exc_info=True,
                )

    def _load_manifest(self, yaml_path: Path) -> Optional[SkillManifest]:
        """
        Load a skill manifest from a YAML file.

        Args:
            yaml_path: Path to the YAML file

        Returns:
            SkillManifest object or None if file is empty/invalid
        """
        if not yaml_path.exists():
            return None

        with open(yaml_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        # Skip empty files
        if not content:
            return None

        try:
            data = yaml.safe_load(content)
            if not data:
                return None

            # Ensure 'id' is set (default to filename without extension)
            if "id" not in data:
                data["id"] = yaml_path.stem
            
            # Validate id format
            import re
            if not re.match(r"^[a-z0-9-]+$", data["id"]):
                raise ValueError(f"Invalid skill id format: {data['id']}. Only lowercase letters, numbers, and hyphens are allowed.")

            # Set default entry path if not specified
            if "entry" not in data or not data["entry"]:
                data["entry"] = str(
                    config.cli_dir / f"{data['id']}.py"
                )

            return SkillManifest(**data)
        except Exception as e:
            logger.error(
                f"Failed to parse manifest {yaml_path}: {e}",
                exc_info=True,
            )
            raise

    def get_skill(self, skill_id: str) -> Optional[SkillManifest]:
        """
        Get a skill manifest by ID.

        Args:
            skill_id: The skill ID

        Returns:
            SkillManifest or None if not found
        """
        return self._manifests.get(skill_id)

    def list_skills(self) -> list[str]:
        """
        List all registered skill IDs.

        Returns:
            List of skill IDs
        """
        return list(self._manifests.keys())

    def reload(self) -> None:
        """Reload all manifests from disk."""
        self._manifests.clear()
        self._load_all()


# Global registry instance
_registry: Optional[SkillRegistry] = None


def get_registry() -> SkillRegistry:
    """Get the global skill registry instance."""
    global _registry
    if _registry is None:
        _registry = SkillRegistry()
    return _registry

