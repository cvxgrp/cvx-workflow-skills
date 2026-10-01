#!/usr/bin/env python3
"""Read local bundled resources without consulting a source checkout."""

import json
from pathlib import Path

skill = Path(__file__).resolve().parents[1]
message = (skill / "assets/message.txt").read_text(encoding="utf-8").strip()
checklist = (skill / "references/shared-checklist.md").read_text(encoding="utf-8")
print(json.dumps({"message": message, "checklist_present": "Fixture checklist" in checklist}, sort_keys=True))
