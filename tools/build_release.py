#!/usr/bin/env python3
"""Assemble explicitly selected skill resources. Never install or execute them."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile
from urllib.parse import unquote, urlsplit

try:
    from agentskills import validate as reference_validate
    from agentskills.parser import parse_frontmatter
except ImportError as exc:
    raise SystemExit("Missing development validator; run uv sync --locked separately before building.") from exc


class ReleaseError(ValueError):
    """Invalid input or an unsafe/unverifiable release tree."""


NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
VERSION = re.compile(r"\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?\Z")
OWNER = ".cvx-opt-release"
OWNER_CONTENT = b"cvx-opt-skill release builder v1\n"
INVENTORY = "release-manifest.json"
RESOURCE_PATH = re.compile(
    r"(?<![\w/])(?:\.\./)*(?:references|scripts|assets|languages|backends)/"
    r"[^\s`\"'<>()[\]{}]+"
)
LINK = re.compile(r"!?\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+[^)]*)?\)")
REFERENCE_LINK = re.compile(r"^\s*\[[^\]\n]+\]:\s*(<[^>]+>|\S+)", re.M)


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ReleaseError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except (OSError, ValueError) as exc:
        raise ReleaseError(f"Cannot read JSON {path}: {exc}") from exc


def _object(value: object, required: set[str], optional: set[str], context: str) -> dict:
    if not isinstance(value, dict):
        raise ReleaseError(f"{context} must be an object")
    missing, extra = required - value.keys(), value.keys() - required - optional
    if missing or extra:
        raise ReleaseError(f"{context}: missing keys {sorted(missing)}, unknown keys {sorted(extra)}")
    return value


def _list(value: object, context: str) -> list:
    if not isinstance(value, list):
        raise ReleaseError(f"{context} must be an array")
    return value


def relative_path(value: object) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ReleaseError(f"Expected a nonempty forward-slash relative path: {value!r}")
    path = PurePosixPath(value)
    # Disallow traversal, drive syntax, and non-canonical spellings in the map.
    if path.is_absolute() or any(p in ("", ".", "..") or ":" in p for p in value.split("/")):
        raise ReleaseError(f"Unsafe relative path: {value!r}")
    return path


def source_file(root: Path, value: object) -> Path:
    relative = relative_path(value)
    path = root.joinpath(*relative.parts)
    for parent in (path, *path.parents):
        if parent == root:
            break
        if parent.is_symlink():
            raise ReleaseError(f"Symlink source is not allowed: {path}")
    if not path.is_file():
        raise ReleaseError(f"Missing source file: {path}")
    return path


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _put(stage: Path, target: str, data: bytes, executable: bool = False) -> None:
    relative = relative_path(target)
    path = stage.joinpath(*relative.parts)
    if path.exists() or any(parent.is_file() for parent in path.parents if parent != stage):
        raise ReleaseError(f"Destination collision: {target}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    path.chmod(0o755 if executable else 0o644)


def _copy_files(root: Path, stage: Path, entries: object, prefix: str = "") -> None:
    for entry in _list(entries, "files"):
        item = _object(entry, {"source", "target"}, set(), "file entry")
        target = str(relative_path(item["target"]))
        source = source_file(root, item["source"])
        _put(stage, prefix + target, source.read_bytes(), bool(source.stat().st_mode & 0o111))


def _bundle_registry(root: Path, stage: Path, prefix: str, value: object) -> None:
    config = _object(value, {"algorithms", "sources", "ids"}, set(), "registry selection")
    for field in ("algorithms", "sources"):
        if not str(relative_path(config[field])).startswith("registry/"):
            raise ReleaseError(f"Registry {field} source must be inside registry/")
    ids = _list(config["ids"], "registry.ids")
    if not ids or any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        raise ReleaseError("registry.ids must be nonempty, unique strings")
    algorithms = {}
    source = source_file(root, config["algorithms"])
    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            card = json.loads(line, object_pairs_hook=_unique_object)
        except ValueError as exc:
            raise ReleaseError(f"Invalid registry JSON at {source}:{number}: {exc}") from exc
        if not isinstance(card, dict) or not isinstance(card.get("id"), str):
            raise ReleaseError(f"Registry card has no string id at {source}:{number}")
        if card["id"] in algorithms:
            raise ReleaseError(f"Duplicate registry id: {card['id']}")
        algorithms[card["id"]] = card
    selected, keys = [], set()
    for identifier in sorted(ids):
        if identifier not in algorithms:
            raise ReleaseError(f"Missing registry id: {identifier}")
        card = algorithms[identifier]
        if card.get("evidence_level") != "card_specific":
            raise ReleaseError(f"Registry card is not card_specific: {identifier}")
        if card.get("implementation_status") not in ("verified_reference", "verified_accelerated"):
            raise ReleaseError(f"Registry card is not labeled verified: {identifier}")
        sources = card.get("source_keys")
        if not isinstance(sources, list) or not sources or any(not isinstance(k, str) for k in sources):
            raise ReleaseError(f"Registry card has no valid primary-source keys: {identifier}")
        if not isinstance(card.get("verification_tests"), list) or not card["verification_tests"]:
            raise ReleaseError(f"Registry card has no verification tests: {identifier}")
        selected.append(card)
        keys.update(sources)
    sources = read_json(source_file(root, config["sources"]))
    if not isinstance(sources, dict) or keys - sources.keys():
        raise ReleaseError(f"Missing registry source records: {sorted(keys - sources.keys()) if isinstance(sources, dict) else 'invalid sources object'}")
    # Labels gate curation but are not proof: card auditing remains a release obligation.
    data = "".join(json.dumps(c, sort_keys=True, ensure_ascii=False) + "\n" for c in selected).encode()
    _put(stage, prefix + "assets/registry/algorithms.jsonl", data)
    _put(stage, prefix + "assets/registry/sources.json", _json_bytes({k: sources[k] for k in sorted(keys)}))


def _check_link(skill: Path, document: Path, target: str, *, from_skill_root: bool = False) -> None:
    target = target.strip("<>")
    parsed = urlsplit(target)
    if parsed.scheme in ("http", "https", "mailto"):
        return
    if parsed.scheme or parsed.netloc or "\\" in target:
        raise ReleaseError(f"Unsupported/nonportable resource link in {document}: {target}")
    path = unquote(parsed.path)
    if not path:
        return
    if PurePosixPath(path).is_absolute():
        raise ReleaseError(f"Absolute resource link in {document}: {target}")
    resolved = ((skill if from_skill_root else document.parent) / path).resolve()
    if not resolved.is_relative_to(skill):
        raise ReleaseError(f"Resource link escapes skill in {document}: {target}")
    if not resolved.exists():
        raise ReleaseError(f"Missing resource in {document}: {target}")


def validate_skill(skill: Path) -> None:
    entry = skill / "SKILL.md"
    if not entry.is_file():
        raise ReleaseError(f"Missing SKILL.md: {skill}")
    try:
        errors = reference_validate(skill)
        text = entry.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(text)
    except Exception as exc:
        raise ReleaseError(f"Invalid skill {skill.name}: {exc}") from exc
    if errors:
        raise ReleaseError(f"Invalid skill {skill.name}: {'; '.join(errors)}")
    if not NAME.fullmatch(metadata["name"]) or len(metadata["name"]) > 64:
        raise ReleaseError(f"Skill name must use ASCII lowercase single-hyphen form: {skill.name}")
    if len(text.splitlines()) > 500:
        raise ReleaseError(f"SKILL.md exceeds 500 lines: {skill.name}")
    if not body.strip():
        raise ReleaseError(f"Empty skill body: {skill.name}")
    for field in ("license", "compatibility", "allowed-tools"):
        if field in metadata and not isinstance(metadata[field], str):
            raise ReleaseError(f"{field} must be a string: {skill.name}")
    if "metadata" in metadata and (
        not isinstance(metadata["metadata"], dict)
        or any(not isinstance(v, str) for v in metadata["metadata"].values())
    ):
        raise ReleaseError(f"metadata must be a string-to-string map: {skill.name}")
    for path in skill.rglob("*.md"):
        content = path.read_text(encoding="utf-8")
        for match in LINK.finditer(content):
            _check_link(skill, path, match.group(1))
        for match in REFERENCE_LINK.finditer(content):
            _check_link(skill, path, match.group(1))
        # Backticked resource paths/commands are skill-root-relative. Markdown
        # links use standard document-relative semantics, checked above.
        for literal in re.findall(r"`([^`\n]+)`", content):
            for match in RESOURCE_PATH.finditer(literal):
                _check_link(skill, path, match.group().rstrip(".,;"), from_skill_root=True)


def _files(root: Path) -> dict[str, dict]:
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ReleaseError(f"Symlinks are not allowed in releases: {path}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ReleaseError(f"Non-regular release resource: {path}")
        relative = path.relative_to(root).as_posix()
        if relative != INVENTORY:
            result[relative] = {
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "executable": bool(path.stat().st_mode & 0o111),
            }
    return result


def verify_inventory(root: Path) -> dict:
    if not root.is_dir() or root.is_symlink() or not (root / OWNER).is_file():
        raise ReleaseError(f"Refusing unowned output directory: {root}")
    if (root / OWNER).read_bytes() != OWNER_CONTENT:
        raise ReleaseError(f"Unrecognized release ownership marker: {root}")
    inventory = read_json(root / INVENTORY)
    if not isinstance(inventory, dict) or type(inventory.get("schema_version")) is not int or inventory.get("schema_version") != 1:
        raise ReleaseError(f"Invalid release inventory: {root}")
    if inventory.get("files") != _files(root):
        raise ReleaseError(f"Release files were modified or added; refusing replacement: {root}")
    expected_dirs = set()
    for name in inventory["files"]:
        expected_dirs.update(str(p) for p in PurePosixPath(name).parents if str(p) != ".")
    actual_dirs = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_dir()}
    if actual_dirs != expected_dirs:
        raise ReleaseError(f"Release directories were added or removed; refusing replacement: {root}")
    return inventory


def validate_release(root: Path) -> dict:
    root = root.absolute()
    for parent in (root, *root.parents):
        if parent.is_symlink():
            raise ReleaseError(f"Symlink output path is not allowed: {parent}")
    root = root.resolve()
    inventory = verify_inventory(root)
    skills = inventory.get("skills")
    if not isinstance(skills, list) or not skills or any(not isinstance(n, str) for n in skills) or len(skills) != len(set(skills)):
        raise ReleaseError("Release must contain a nonempty, unique skill list")
    actual = {p.name for p in (root / "skills").iterdir()}
    if actual != set(skills):
        raise ReleaseError("Skill directory list differs from release inventory")
    for name in skills:
        if not isinstance(name, str) or not NAME.fullmatch(name):
            raise ReleaseError(f"Invalid release skill name: {name!r}")
        validate_skill(root / "skills" / name)
    package = _object(read_json(root / "package.json"),
                      {"name", "version", "description", "license", "pi", "files", "keywords"},
                      set(), "assembled package")
    plugin = _object(read_json(root / ".claude-plugin/plugin.json"),
                     {"name", "version", "description", "license", "skills"},
                     set(), "assembled plugin")
    if any(not isinstance(package[k], str) or not package[k].strip() for k in ("name", "version", "description", "license")):
        raise ReleaseError("Invalid assembled package metadata")
    if not NAME.fullmatch(package["name"]) or not VERSION.fullmatch(package["version"]):
        raise ReleaseError("Invalid assembled package name/version")
    if package.get("pi") != {"skills": ["./skills"]} or plugin.get("skills") != "./skills/":
        raise ReleaseError("Adapters must discover the same ./skills tree")
    if any(package.get(field) != plugin.get(field) for field in ("name", "version", "description", "license")):
        raise ReleaseError("Package and plugin metadata differ")
    if "scripts" in package or "dependencies" in package:
        raise ReleaseError("Portable skill package must not install executable hooks/dependencies")
    return inventory


def build(root: Path, config_path: Path, output: Path, names: list[str] | None = None) -> list[str]:
    root = root.resolve()
    output = output.absolute()
    for path in (output, *output.parents):
        if path.is_symlink():
            raise ReleaseError(f"Symlink output path is not allowed: {path}")
    output = output.resolve()
    if root == output or root.is_relative_to(output):
        raise ReleaseError("Output must not be the source root or one of its ancestors")
    if output.is_relative_to(root) and output.relative_to(root).parts[0] != "dist":
        raise ReleaseError("In-repository output must be under dist/")
    config_path = config_path.resolve()
    if config_path.is_relative_to(output):
        raise ReleaseError("Release configuration must not live inside the output")
    config = _object(read_json(config_path), {"schema_version", "package", "skills", "root_files"}, set(), "release map")
    if type(config["schema_version"]) is not int or config["schema_version"] != 1:
        raise ReleaseError("Unsupported release-map schema_version")
    package = _object(config["package"], {"name", "version", "description", "license"}, set(), "package")
    if any(not isinstance(v, str) or not v.strip() for v in package.values()):
        raise ReleaseError("Package metadata values must be nonempty strings")
    if not NAME.fullmatch(package["name"]) or not VERSION.fullmatch(package["version"]):
        raise ReleaseError("Invalid package name or version")
    skills = config["skills"]
    if not isinstance(skills, dict):
        raise ReleaseError("skills must map names to explicit resource selections")
    selected = sorted(skills if names is None else names)
    if not selected:
        raise ReleaseError("No implemented skills registered; refusing an empty product release")
    if len(set(selected)) != len(selected):
        raise ReleaseError("Duplicate requested skill")
    for name in selected:
        if not isinstance(name, str) or not NAME.fullmatch(name) or len(name) > 64:
            raise ReleaseError(f"Invalid skill name: {name!r}")
        if name not in skills:
            raise ReleaseError(f"Skill is not registered: {name}")
    if output.exists():
        verify_inventory(output)  # Never discard unrelated files or user edits.
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}-stage-", dir=output.parent))
    try:
        _put(stage, OWNER, OWNER_CONTENT)
        # Reserve generated files; root resources cannot shadow them.
        _put(stage, "package.json", _json_bytes({
            **package, "keywords": ["pi-package", "agent-skills", "convex-optimization"],
            "pi": {"skills": ["./skills"]},
            "files": ["skills/", ".claude-plugin/", "README.md", "LICENSE", OWNER, INVENTORY],
        }))
        _put(stage, ".claude-plugin/plugin.json", _json_bytes({**package, "skills": "./skills/"}))
        readme = (
            f"# {package['name']} {package['version']}\n\n{package['description']}\n\n"
            "Assembled skills: " + ", ".join(f"`{n}`" for n in selected) + ".\n\n"
            "Use this directory as a Claude Code plugin or a pi package. For Codex\n"
            "and OpenCode, copy individual directories from `skills/` into\n"
            "`.agents/skills/` in the target project (or `~/.agents/skills/`).\n"
            "Claude Code also supports `.claude/skills/`. No automatic installs or\n"
            "hooks are included. Each skill documents its own runtime requirements.\n"
        )
        _put(stage, "README.md", readme.encode())
        for entry in _list(config["root_files"], "root_files"):
            item = _object(entry, {"source", "target"}, set(), "root file")
            target = str(relative_path(item["target"]))
            if target == INVENTORY or target.startswith("skills/"):
                raise ReleaseError(f"Reserved root-file destination: {target}")
            _copy_files(root, stage, [entry])
        for name in selected:
            selection = _object(skills[name], {"files"}, {"registry"}, f"skill {name}")
            prefix = f"skills/{name}/"
            # Selected files may come from skills/, shared/, or registry/. No globbing.
            for entry in _list(selection["files"], f"{name}.files"):
                source = str(relative_path(entry.get("source") if isinstance(entry, dict) else None))
                allowed = (f"skills/{name}/", "shared/", "registry/")
                if not source.startswith(allowed):
                    raise ReleaseError(f"Source outside skill/shared/registry roots: {source}")
                if source_file(root, source).is_relative_to(output):
                    raise ReleaseError(f"Source overlaps output: {source}")
            _copy_files(root, stage, selection["files"], prefix)
            if "registry" in selection:
                _bundle_registry(root, stage, prefix, selection["registry"])
            validate_skill(stage / "skills" / name)
        _put(stage, INVENTORY, _json_bytes({
            "schema_version": 1, "skills": selected, "files": _files(stage),
        }))
        validate_release(stage)
        # Validate everything before replacement; roll back if the rename fails.
        backup = None
        if output.exists():
            verify_inventory(output)
            backup = Path(tempfile.mkdtemp(prefix=f".{output.name}-old-", dir=output.parent))
            backup.rmdir()
            os.replace(output, backup)
        try:
            os.replace(stage, output)
        except OSError:
            if backup is not None:
                os.replace(backup, output)
            raise
        if backup is not None:
            shutil.rmtree(backup)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return selected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--config", type=Path, default=Path("release.json"), help="relative to --root")
    parser.add_argument("--output", type=Path, help="default: ROOT/dist/release; otherwise relative to cwd")
    parser.add_argument("--skills", nargs="+", help="subset of registered skills; default: all")
    args = parser.parse_args()
    root = args.root.resolve()
    config = args.config if args.config.is_absolute() else root / args.config
    try:
        names = build(root, config, args.output or root / "dist/release", args.skills)
    except (ReleaseError, OSError) as exc:
        print(f"release error: {exc}", file=sys.stderr)
        return 1
    print(f"Assembled {', '.join(names)} into {args.output or root / 'dist/release'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
