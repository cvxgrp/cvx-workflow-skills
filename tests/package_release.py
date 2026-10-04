"""Assemble and ZIP the distribution; never publish or install it."""

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import tomllib
import zipfile

from .build_release import NAME, VERSION, ReleaseError, build, read_json
from .paths import ARTIFACTS, ROOT, artifact_output


def check_version(tag=None):
    package = read_json(ROOT / "release.json")["package"]
    name, version = package["name"], package["version"]
    if not NAME.fullmatch(name) or not VERSION.fullmatch(version):
        raise ReleaseError("Invalid distribution name/version")
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    locked = tomllib.loads((ROOT / "uv.lock").read_text())["package"]
    entries = [p for p in locked if p["name"] == name and p.get("source") == {"virtual": "."}]
    if project["name"] != name or project["version"] != version or len(entries) != 1 or entries[0]["version"] != version:
        raise ReleaseError("release.json, pyproject.toml, and uv.lock must agree on the package version")
    if tag is not None and tag != f"v{version}":
        raise ReleaseError(f"Tag {tag!r} does not match v{version}")
    return name, version


def write_zip(source, archive, prefix):
    # Stable ordering, dates, and permissions make repeated builds identical.
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(source.rglob("*")):
            if path.is_dir():
                continue
            info = zipfile.ZipInfo(f"{prefix}/{path.relative_to(source).as_posix()}")
            info.create_system = 3
            mode = 0o755 if path.stat().st_mode & 0o111 else 0o644
            info.external_attr = (stat.S_IFREG | mode) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(info, path.read_bytes())


def package_release(tag, output=None):
    name, version = check_version(tag)
    output = artifact_output(output or ARTIFACTS / "packages" / tag)
    release = ARTIFACTS / "release"
    if output.is_relative_to(release) or release.is_relative_to(output):
        raise ReleaseError("Archive output must not overlap the assembled distribution")
    if output.exists():
        raise ReleaseError(f"Output already exists; use a new --output directory: {output}")
    skills = build(ROOT, ROOT / "release.json", release)
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".packages-", dir=output.parent))
    try:
        write_zip(release, stage / f"{name}-{version}.zip", f"{name}-{version}")
        for skill in skills:
            write_zip(release / "skills" / skill, stage / f"{skill}-{version}.zip", skill)
        checksums = "".join(
            f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n"
            for path in sorted(stage.glob("*.zip"))
        )
        (stage / "SHA256SUMS").write_text(checksums, encoding="utf-8")
        os.rename(stage, output)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", help="release tag, e.g. v0.1.0")
    parser.add_argument("--check-version", action="store_true", help="only check version consistency")
    parser.add_argument("--output", type=Path, help="new directory inside ignored artifacts/")
    args = parser.parse_args()
    if not args.check_version and args.tag is None:
        parser.error("--tag is required for packaging")
    try:
        if args.check_version:
            name, version = check_version(args.tag)
            print(f"Consistent version: {name} {version}")
        else:
            print(f"Release bundles: {package_release(args.tag, args.output)}")
    except (ReleaseError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"packaging error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
