"""Validate skill-file format without executing skill code."""

import argparse
from pathlib import Path

from agentskills import validate
from agentskills.parser import parse_frontmatter


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-dir", type=Path,
                        default=Path(__file__).resolve().parents[1] / "skills")
    args = parser.parse_args()
    if not args.skills_dir.is_dir():
        parser.error(f"Missing skills directory: {args.skills_dir}")
    skills = sorted(path for path in args.skills_dir.iterdir() if path.is_dir())
    if not skills:
        parser.error("No skill directories found")
    failed = False
    for skill in skills:
        entry = skill / "SKILL.md"
        try:
            errors = validate(skill) if entry.is_file() else ["Missing SKILL.md"]
            if not errors and not parse_frontmatter(entry.read_text(encoding="utf-8"))[1].strip():
                errors = ["Missing instruction body"]
        except (OSError, UnicodeError) as exc:
            errors = [str(exc)]
        if errors:
            failed = True
            for error in errors:
                print(f"{skill.name}: {error}")
        else:
            print(f"{skill.name}: valid")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
