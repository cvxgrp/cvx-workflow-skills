"""Exercise recording, not optimization/model-selection grading."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from evals.run import record_run
from tools.build_release import build

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/release"


class EvalRecorderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.prompt = self.base / "prompt.md"
        self.prompt.write_text("Fixture prompt.\n", encoding="utf-8")
        self.output = self.base / "run"

    def run_command(self, command, **options):
        return record_run(
            prompt=self.prompt, output=self.output, command=command,
            mode=options.pop("mode", "fixture"), harness="stdlib-fixture", model="none",
            **options,
        )

    def test_success_records_prompt_configuration_logs_and_artifacts(self):
        command = [sys.executable, "-c", (
            "import os, pathlib, sys; "
            "assert pathlib.Path.cwd() == pathlib.Path(os.environ['CVX_EVAL_WORKSPACE']); "
            "text = sys.stdin.read(); "
            "pathlib.Path('answer.txt').write_text(text); "
            "print('fixture completed'); print('fixture stderr', file=sys.stderr)"
        )]
        report = self.run_command(command, settings={"seed": 7}, harness_version="fixture-v1")
        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["assessment"], "not_graded")
        self.assertEqual(report["exit_code"], 0)
        self.assertEqual(report["settings"], {"seed": 7})
        self.assertEqual(report["command"], command)
        self.assertEqual(report["harness_version"], "fixture-v1")
        self.assertEqual((self.output / "workspace/answer.txt").read_text(), "Fixture prompt.\n")
        self.assertIn("answer.txt", report["artifacts"])
        self.assertEqual(json.loads((self.output / "report.json").read_text()), report)
        self.assertIn("fixture completed", (self.output / "stdout.log").read_text())
        self.assertIn("fixture stderr", (self.output / "stderr.log").read_text())

    def test_with_skill_snapshot_runs_after_source_removed(self):
        source = self.base / "source"
        shutil.copytree(FIXTURE, source)
        release = self.base / "release"
        build(source, source / "release.json", release)
        shutil.rmtree(source)
        skill = release / "skills/m0-fixture"
        command = [sys.executable, "-c", (
            "import os, pathlib, subprocess, sys; "
            "script = pathlib.Path(os.environ['CVX_EVAL_SKILL_DIR']) / 'scripts/check_resources.py'; "
            "result = subprocess.check_output([sys.executable, '-I', str(script)]); "
            "pathlib.Path('result.json').write_bytes(result)"
        )]
        report = self.run_command(command, mode="with-skill", skill=skill)
        shutil.rmtree(release)
        self.assertEqual(report["status"], "completed")
        self.assertIn("SKILL.md", report["skill_files"])
        self.assertEqual(json.loads((self.output / "workspace/result.json").read_text())["message"], "isolated-m0-fixture")

    def test_command_failure_and_launch_failure_recorded(self):
        report = self.run_command([sys.executable, "-c", "raise SystemExit(7)"])
        self.assertEqual(report["status"], "command_failed")
        self.assertEqual(report["exit_code"], 7)
        self.output = self.base / "launch-failure"
        report = self.run_command([str(self.base / "does-not-exist")])
        self.assertEqual(report["status"], "launch_error")
        self.assertIsNone(report["exit_code"])
        self.assertIn("error", report)
        self.assertTrue((self.output / "report.json").is_file())

    def test_timeout_and_output_limit(self):
        report = self.run_command([sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.05)
        self.assertEqual(report["status"], "timeout")
        self.assertLess(report["elapsed_seconds"], 3)
        self.output = self.base / "too-much-output"
        report = self.run_command([sys.executable, "-c", "print('x' * 8192)"], max_log_bytes=1024)
        self.assertEqual(report["status"], "output_limit")

    def test_existing_run_not_overwritten(self):
        self.run_command([sys.executable, "-c", "print('first')"])
        before = (self.output / "report.json").read_bytes()
        with self.assertRaises(FileExistsError):
            self.run_command([sys.executable, "-c", "print('second')"])
        self.assertEqual((self.output / "report.json").read_bytes(), before)

    def test_modes_and_required_inputs_checked_before_creating_output(self):
        for options in ({"mode": "with-skill"}, {"mode": "unknown"}, {"timeout": 0}, {"timeout": float("nan")}, {"timeout": float("inf")}, {"max_log_bytes": 0}, {"settings": []}):
            with self.subTest(options=options):
                with self.assertRaises(ValueError):
                    self.run_command([sys.executable, "-c", "pass"], **options)
                self.assertFalse(self.output.exists())
        with self.assertRaises(ValueError):
            self.run_command([])

    def test_baseline_cannot_receive_skill(self):
        with self.assertRaises(ValueError):
            self.run_command([sys.executable, "-c", "pass"], mode="baseline", skill=FIXTURE / "skills/m0-fixture")
        self.assertFalse(self.output.exists())

    def test_symlink_and_overlapping_skill_snapshots_rejected(self):
        skill = self.base / "skill"
        shutil.copytree(FIXTURE / "skills/m0-fixture", skill)
        link = skill / "outside"
        link.symlink_to(self.prompt)
        with self.assertRaisesRegex(ValueError, "symlinks"):
            self.run_command([sys.executable, "-c", "pass"], mode="with-skill", skill=skill)
        link.unlink()
        self.output = skill / "run"
        with self.assertRaisesRegex(ValueError, "overlap"):
            self.run_command([sys.executable, "-c", "pass"], mode="with-skill", skill=skill)

    def test_cli_from_unrelated_cwd(self):
        cwd = self.base / "unrelated"
        cwd.mkdir()
        result = subprocess.run([
            sys.executable, str(ROOT / "evals/run.py"), "--prompt", str(self.prompt),
            "--output", str(self.output), "--mode", "fixture", "--harness", "stdlib-fixture",
            "--model", "none", "--", sys.executable, "-c", "print('ok')",
        ], cwd=cwd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("not_graded", result.stdout)

    @unittest.skipUnless(os.name == "posix", "process-group cleanup is POSIX-only")
    def test_timeout_kills_same_group_descendant(self):
        command = [sys.executable, "-c", (
            "import subprocess, sys, time; "
            "subprocess.Popen([sys.executable, '-c', "
            "\"import pathlib, time; time.sleep(0.5); pathlib.Path('leaked.txt').write_text('leak')\"]); "
            "time.sleep(5)"
        )]
        report = self.run_command(command, timeout=0.1)
        self.assertEqual(report["status"], "timeout")
        import time
        time.sleep(0.6)
        self.assertFalse((self.output / "workspace/leaked.txt").exists())


if __name__ == "__main__":
    unittest.main()
