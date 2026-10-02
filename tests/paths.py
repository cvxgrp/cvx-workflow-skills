"""Output location for optional release assembly."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"


def artifact_output(path):
    path = Path(path).absolute()
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise ValueError("Artifact paths must not contain symlinks")
    path = path.resolve()
    if not path.is_relative_to(ARTIFACTS) or path == ARTIFACTS:
        raise ValueError(f"Generated output must be inside {ARTIFACTS}")
    return path
