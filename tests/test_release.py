"""M0 infrastructure tests. All skill content is disposable, not product scope."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.build_release import ReleaseError, build, read_json, validate_release

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/release"


def tree_bytes(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / "source"
        shutil.copytree(FIXTURE, self.source)
        self.output = self.base / "release"
        self.config_path = self.source / "release.json"
        self.config = read_json(self.config_path)
        self.skill = self.source / "skills/m0-fixture"

    def configure(self):
        self.config_path.write_text(json.dumps(self.config), encoding="utf-8")

    def assemble(self):
        return build(self.source, self.config_path, self.output)

    def test_assembled_adapters_and_inventory(self):
        self.assertEqual(self.assemble(), ["m0-fixture"])
        inventory = validate_release(self.output)
        package = read_json(self.output / "package.json")
        plugin = read_json(self.output / ".claude-plugin/plugin.json")
        self.assertEqual(package["pi"], {"skills": ["./skills"]})
        self.assertEqual(plugin["skills"], "./skills/")
        self.assertEqual(package["version"], plugin["version"])
        self.assertEqual(inventory["skills"], ["m0-fixture"])
        self.assertNotIn("scripts", package)
        self.assertNotIn("dependencies", package)
        self.assertFalse((self.output / "shared").exists())
        self.assertFalse((self.output / "registry").exists())
        self.assertFalse((self.output / "tests").exists())

    def test_reference_validator_cli(self):
        self.assemble()
        result = subprocess.run(
            [sys.executable, "-m", "agentskills.cli", "validate", str(self.output / "skills/m0-fixture")],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("valid", result.stdout.lower())

    def test_individual_skill_isolated_without_source_and_unrelated_cwd(self):
        self.assemble()
        isolated = self.base / "installed/m0-fixture"
        isolated.parent.mkdir()
        shutil.copytree(self.output / "skills/m0-fixture", isolated)
        shutil.rmtree(self.source)
        shutil.rmtree(self.output)
        cwd = self.base / "unrelated"
        cwd.mkdir()
        result = subprocess.run(
            [sys.executable, "-I", str(isolated / "scripts/check_resources.py")],
            cwd=cwd, capture_output=True, text=True, check=True,
        )
        self.assertEqual(json.loads(result.stdout), {
            "message": "isolated-m0-fixture", "checklist_present": True,
        })

    def test_deterministic_rebuild_and_stale_resources_removed(self):
        extra = self.skill / "assets/old.txt"
        extra.write_text("old", encoding="utf-8")
        self.config["skills"]["m0-fixture"]["files"].append({
            "source": "skills/m0-fixture/assets/old.txt", "target": "assets/old.txt",
        })
        self.configure()
        self.assemble()
        before = tree_bytes(self.output)
        self.assemble()
        self.assertEqual(before, tree_bytes(self.output))
        self.config["skills"]["m0-fixture"]["files"].pop()
        self.configure()
        self.assemble()
        self.assertFalse((self.output / "skills/m0-fixture/assets/old.txt").exists())

    def test_invalid_rebuild_keeps_prior_release(self):
        self.assemble()
        before = tree_bytes(self.output)
        (self.skill / "assets/message.txt").unlink()
        with self.assertRaisesRegex(ReleaseError, "Missing source"):
            self.assemble()
        self.assertEqual(before, tree_bytes(self.output))

    def test_rename_failure_rolls_back_prior_release(self):
        self.assemble()
        before = tree_bytes(self.output)
        from tools import build_release
        original = build_release.os.replace

        def fail_stage(source, target):
            if "-stage-" in Path(source).name:
                raise OSError("simulated rename failure")
            return original(source, target)

        with patch.object(build_release.os, "replace", side_effect=fail_stage):
            with self.assertRaisesRegex(OSError, "simulated"):
                self.assemble()
        self.assertEqual(before, tree_bytes(self.output))

    def test_unowned_output_not_discarded(self):
        self.output.mkdir()
        (self.output / "user.txt").write_text("preserve me")
        with self.assertRaisesRegex(ReleaseError, "unowned"):
            self.assemble()
        self.assertEqual((self.output / "user.txt").read_text(), "preserve me")

    def test_modified_or_extra_output_not_discarded(self):
        self.assemble()
        (self.output / "user.txt").write_text("preserve me")
        with self.assertRaisesRegex(ReleaseError, "modified or added"):
            self.assemble()
        (self.output / "user.txt").unlink()
        helper = self.output / "skills/m0-fixture/scripts/check_resources.py"
        helper.write_text("# user edit\n")
        with self.assertRaisesRegex(ReleaseError, "modified or added"):
            self.assemble()
        self.assertEqual(helper.read_text(), "# user edit\n")

    def test_empty_user_directory_not_discarded(self):
        self.assemble()
        (self.output / "user-directory").mkdir()
        with self.assertRaisesRegex(ReleaseError, "directories were added"):
            self.assemble()
        self.assertTrue((self.output / "user-directory").is_dir())

    def test_missing_declared_resource(self):
        (self.skill / "SKILL.md").write_text((self.skill / "SKILL.md").read_text() + "\nRead `assets/missing.json`.\n")
        with self.assertRaisesRegex(ReleaseError, "Missing resource"):
            self.assemble()

    def test_nested_markdown_resource_link(self):
        (self.source / "shared/checklist.md").write_text("Read the [asset](../assets/message.txt).\n")
        self.assemble()

    def test_escaping_markdown_links(self):
        for link in ("../outside.md", "/tmp/outside.md", "file:///tmp/outside.md", "%2e%2e/outside.md"):
            with self.subTest(link=link):
                (self.skill / "SKILL.md").write_text(
                    "---\nname: m0-fixture\ndescription: Fixture.\n---\n\n" + f"[bad]({link})\n"
                )
                with self.assertRaises(ReleaseError):
                    self.assemble()

    def test_escaping_literal_resource_path(self):
        (self.skill / "SKILL.md").write_text((self.skill / "SKILL.md").read_text() + "\nRead `../references/outside.md`.\n")
        with self.assertRaisesRegex(ReleaseError, "escapes skill"):
            self.assemble()

    def test_external_links_and_anchor_allowed(self):
        (self.skill / "SKILL.md").write_text((self.skill / "SKILL.md").read_text() + "\n[external](https://example.org) [anchor](#heading)\n")
        self.assemble()

    def test_path_traversal_and_windows_paths_rejected(self):
        original = copy.deepcopy(self.config)
        for target in ("../escape.txt", "/absolute.txt", "C:/windows.txt", "assets\\bad.txt", "assets/./bad.txt"):
            with self.subTest(target=target):
                self.config = copy.deepcopy(original)
                self.config["skills"]["m0-fixture"]["files"][1]["target"] = target
                self.configure()
                with self.assertRaises(ReleaseError):
                    self.assemble()
        self.assertFalse((self.base / "escape.txt").exists())

    def test_collision_and_file_directory_collision(self):
        files = self.config["skills"]["m0-fixture"]["files"]
        for target in ("SKILL.md", "assets", "scripts/check_resources.py/nested.txt"):
            with self.subTest(target=target):
                addition = {"source": "shared/checklist.md", "target": target}
                files.append(addition)
                self.configure()
                with self.assertRaisesRegex(ReleaseError, "collision"):
                    self.assemble()
                files.pop()

    def test_symlink_source_and_output_rejected(self):
        asset = self.skill / "assets/message.txt"
        external = self.base / "external.txt"
        external.write_text("not bundled")
        asset.unlink()
        asset.symlink_to(external)
        with self.assertRaisesRegex(ReleaseError, "Symlink source"):
            self.assemble()
        asset.unlink()
        asset.write_text("isolated-m0-fixture\n")
        external_dir = self.base / "external-dir"
        external_dir.mkdir()
        self.output.symlink_to(external_dir, target_is_directory=True)
        with self.assertRaisesRegex(ReleaseError, "Symlink output"):
            self.assemble()
        self.assertEqual(list(external_dir.iterdir()), [])

    def test_symlink_parent_source_and_output_rejected(self):
        resources = self.source / "shared"
        renamed = self.base / "shared-outside"
        resources.rename(renamed)
        resources.symlink_to(renamed, target_is_directory=True)
        with self.assertRaisesRegex(ReleaseError, "Symlink source"):
            self.assemble()
        resources.unlink()
        renamed.rename(resources)
        link = self.base / "linked"
        real = self.base / "real"
        real.mkdir()
        link.symlink_to(real, target_is_directory=True)
        with self.assertRaisesRegex(ReleaseError, "Symlink output"):
            build(self.source, self.config_path, link / "release")

    def test_empty_map_unknown_skill_and_no_empty_product(self):
        for names in (["cvx-model"], [], ["m0-fixture", "m0-fixture"]):
            with self.subTest(names=names):
                with self.assertRaises(ReleaseError):
                    build(self.source, self.config_path, self.output, names)
        with self.assertRaisesRegex(ReleaseError, "No implemented skills"):
            build(ROOT, ROOT / "release.json", self.output)
        self.assertFalse(self.output.exists())

    def test_invalid_metadata_and_oversize_or_empty_entry(self):
        cases = [
            "# No frontmatter\n",
            "---\nname: different-name\ndescription: Fixture.\n---\nBody\n",
            "---\nname: m0-fixture\ndescription: Fixture.\nunknown: value\n---\nBody\n",
            "---\nname: m0-fixture\ndescription: Fixture.\n---\n",
            "---\nname: m0-fixture\ndescription: Fixture.\n---\n" + "Body\n" * 501,
            "---\nname: m0-fixture\ndescription: " + "x" * 1025 + "\n---\nBody\n",
        ]
        for content in cases:
            with self.subTest(content=content[:80]):
                (self.skill / "SKILL.md").write_text(content)
                with self.assertRaises(ReleaseError):
                    self.assemble()

    def test_duplicate_json_keys_unknown_map_keys_and_source_roots(self):
        self.config_path.write_text('{"skills": {}, "skills": {}}')
        with self.assertRaisesRegex(ReleaseError, "Duplicate JSON key"):
            self.assemble()
        self.config["typo"] = True
        self.configure()
        with self.assertRaisesRegex(ReleaseError, "unknown keys"):
            self.assemble()
        del self.config["typo"]
        self.config["skills"]["m0-fixture"]["files"][0]["source"] = "release.json"
        self.configure()
        with self.assertRaisesRegex(ReleaseError, "outside skill/shared/registry"):
            self.assemble()

    def test_source_root_and_in_repo_output_protected(self):
        for output in (self.source, self.base, self.source / "skills"):
            with self.subTest(output=output):
                with self.assertRaises(ReleaseError):
                    build(self.source, self.config_path, output)
        build(self.source, self.config_path, self.source / "dist")

    def test_unselected_source_and_helper_not_executed(self):
        (self.skill / "assets/secret.txt").write_text("not selected")
        helper = self.skill / "scripts/check_resources.py"
        helper.write_text("raise RuntimeError('build must not run me')\n")
        self.assemble()
        self.assertFalse((self.output / "skills/m0-fixture/assets/secret.txt").exists())
        self.assertIn("RuntimeError", (self.output / "skills/m0-fixture/scripts/check_resources.py").read_text())

    def add_registry(self):
        registry = self.source / "registry"
        registry.mkdir()
        card = {
            "id": "fixture-method", "evidence_level": "card_specific",
            "implementation_status": "verified_reference", "source_keys": ["fixture-source"],
            "verification_tests": ["synthetic infrastructure fixture; not a scientific test"],
        }
        (registry / "algorithms.jsonl").write_text(json.dumps(card) + "\n" + json.dumps({"id": "not-selected"}) + "\n")
        (registry / "sources.json").write_text(json.dumps({
            "fixture-source": {"title": "Synthetic infrastructure record"}, "unselected": {},
        }))
        self.config["skills"]["m0-fixture"]["registry"] = {
            "algorithms": "registry/algorithms.jsonl", "sources": "registry/sources.json",
            "ids": ["fixture-method"],
        }
        self.configure()
        return card

    def test_registry_curated_and_missing_ids_rejected(self):
        self.add_registry()
        self.assemble()
        bundled = self.output / "skills/m0-fixture/assets/registry"
        cards = [json.loads(line) for line in (bundled / "algorithms.jsonl").read_text().splitlines()]
        self.assertEqual([c["id"] for c in cards], ["fixture-method"])
        self.assertEqual(set(read_json(bundled / "sources.json")), {"fixture-source"})
        self.config["skills"]["m0-fixture"]["registry"]["ids"] = ["unknown"]
        self.configure()
        with self.assertRaisesRegex(ReleaseError, "Missing registry id"):
            self.assemble()

    def test_registry_template_unverified_and_missing_evidence_rejected(self):
        card = self.add_registry()
        for field, value in (("evidence_level", "family_template"), ("implementation_status", "catalog_only"), ("verification_tests", []), ("source_keys", []), ("source_keys", ["missing-source"])):
            with self.subTest(field=field, value=value):
                changed = dict(card, **{field: value})
                (self.source / "registry/algorithms.jsonl").write_text(json.dumps(changed) + "\n")
                with self.assertRaises(ReleaseError):
                    self.assemble()

    def test_generated_root_files_cannot_be_shadowed(self):
        for target in ("package.json", "release-manifest.json", "skills/hidden.txt"):
            with self.subTest(target=target):
                self.config["root_files"] = [{"source": "shared/checklist.md", "target": target}]
                self.configure()
                with self.assertRaises(ReleaseError):
                    self.assemble()


if __name__ == "__main__":
    unittest.main()
