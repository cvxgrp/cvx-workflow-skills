#!/usr/bin/env python3
"""Record a bounded external command in a fresh workspace; do not grade it."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time


def _digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _snapshot_files(root: Path) -> dict:
    result = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            result[relative] = {"symlink": os.readlink(path)}
        elif path.is_file():
            result[relative] = {"sha256": _digest(path), "bytes": path.stat().st_size}
    return result


def _stop_group(process: subprocess.Popen) -> None:
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        time.sleep(0.1)
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    elif process.poll() is None:
        process.kill()
    process.wait()


def record_run(
    *, prompt: Path, output: Path, command: list[str], mode: str,
    harness: str, model: str, harness_version: str = "unspecified",
    settings: dict | None = None, skill: Path | None = None,
    timeout: float = 120, max_log_bytes: int = 16 * 1024 * 1024,
) -> dict:
    if mode not in ("baseline", "with-skill", "fixture"):
        raise ValueError("mode must be baseline, with-skill, or fixture")
    if not command or not math.isfinite(timeout) or timeout <= 0 or max_log_bytes <= 0:
        raise ValueError("command, finite positive timeout, and positive max_log_bytes are required")
    if mode == "baseline" and skill is not None:
        raise ValueError("baseline runs cannot snapshot a skill")
    if mode == "with-skill" and skill is None:
        raise ValueError("with-skill runs require --skill")
    prompt_bytes = prompt.read_bytes()
    prompt_bytes.decode("utf-8")
    if settings is not None and not isinstance(settings, dict):
        raise ValueError("settings must be a JSON object")
    if skill is not None:
        skill = skill.absolute()
        if not skill.is_dir() or not (skill / "SKILL.md").is_file():
            raise ValueError("skill must be an assembled directory containing SKILL.md")
        if any(p.is_symlink() for p in (skill, *skill.parents)) or any(p.is_symlink() for p in skill.rglob("*")):
            raise ValueError("skill snapshots and their parent paths must not contain symlinks")
        skill = skill.resolve()
    # Fresh outputs only: never merge with or overwrite a previous run.
    output = output.resolve()
    if skill is not None and (output.is_relative_to(skill) or skill.is_relative_to(output)):
        raise ValueError("run output and input skill must not overlap")
    output.mkdir(parents=True, exist_ok=False)
    workspace = output / "workspace"
    workspace.mkdir()
    (output / "prompt.md").write_bytes(prompt_bytes)
    skill_snapshot = None
    if skill is not None:
        skill_snapshot = output / "skill"
        shutil.copytree(skill, skill_snapshot)
    environment = os.environ.copy()
    environment.update({
        "CVX_EVAL_PROMPT_FILE": str(output / "prompt.md"),
        "CVX_EVAL_WORKSPACE": str(workspace),
        "CVX_EVAL_SKILL_DIR": str(skill_snapshot) if skill_snapshot else "",
    })
    report = {
        "schema_version": 1,
        "mode": mode,
        "harness": harness,
        "harness_version": harness_version,
        "model": model,
        "settings": settings or {},
        "command": command,
        "prompt_sha256": hashlib.sha256(prompt_bytes).hexdigest(),
        "skill_files": _snapshot_files(skill_snapshot) if skill_snapshot else None,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "timeout_seconds": timeout,
        "max_log_bytes": max_log_bytes,
        "assessment": "not_graded",
        "status": "launch_error",
        "exit_code": None,
    }
    start = time.monotonic()
    process = None
    try:
        with (output / "prompt.md").open("rb") as stdin, \
                (output / "stdout.log").open("wb") as stdout, \
                (output / "stderr.log").open("wb") as stderr:
            try:
                process = subprocess.Popen(
                    command, cwd=workspace, env=environment, stdin=stdin,
                    stdout=stdout, stderr=stderr, start_new_session=os.name == "posix",
                )
            except OSError as exc:
                report["error"] = str(exc)
            else:
                while process.poll() is None:
                    log_bytes = (output / "stdout.log").stat().st_size + (output / "stderr.log").stat().st_size
                    if log_bytes > max_log_bytes:
                        report["status"] = "output_limit"
                        break
                    if time.monotonic() - start > timeout:
                        report["status"] = "timeout"
                        break
                    time.sleep(0.02)
                else:
                    report["status"] = "completed" if process.returncode == 0 else "command_failed"
                # Also clean up same-group descendants when the main command exits.
                _stop_group(process)
                report["exit_code"] = process.returncode
                if report["status"] in ("completed", "command_failed"):
                    if (output / "stdout.log").stat().st_size + (output / "stderr.log").stat().st_size > max_log_bytes:
                        report["status"] = "output_limit"
    except BaseException:
        if process is not None:
            _stop_group(process)
        raise
    report["elapsed_seconds"] = time.monotonic() - start
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    report["artifacts"] = _snapshot_files(workspace)
    report["logs"] = {
        name: {"sha256": _digest(output / name), "bytes": (output / name).stat().st_size}
        for name in ("stdout.log", "stderr.log")
    }
    (output / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("baseline", "with-skill", "fixture"), required=True)
    parser.add_argument("--harness", required=True)
    parser.add_argument("--harness-version", default="unspecified")
    parser.add_argument("--model", default="unspecified")
    parser.add_argument("--settings", type=Path, help="JSON object; do not include credentials")
    parser.add_argument("--skill", type=Path)
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--max-log-bytes", type=int, default=16 * 1024 * 1024)
    parser.add_argument("command", nargs=argparse.REMAINDER, help="-- executable args ...; no shell")
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    try:
        settings = json.loads(args.settings.read_text(encoding="utf-8")) if args.settings else None
        report = record_run(
            prompt=args.prompt, output=args.output, command=command, mode=args.mode,
            harness=args.harness, harness_version=args.harness_version, model=args.model,
            settings=settings, skill=args.skill, timeout=args.timeout, max_log_bytes=args.max_log_bytes,
        )
    except (OSError, ValueError) as exc:
        print(f"evaluation setup error: {exc}", file=sys.stderr)
        return 2
    print(f"{report['status']}; assessment remains not_graded; report: {args.output / 'report.json'}")
    return 0 if report["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
