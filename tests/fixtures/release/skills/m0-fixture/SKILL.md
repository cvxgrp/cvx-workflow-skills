---
name: m0-fixture
description: Exercise disposable M0 packaging tests. Not an optimization skill and never included in a product release.
license: Apache-2.0
---

# Disposable release fixture

Read the [bundled checklist](references/shared-checklist.md).
Run `scripts/check_resources.py` using the absolute installed skill path, from
any working directory. It reads `assets/message.txt` relative to its own file
and prints a small JSON result. It uses only the Python standard library.
Do not interpret this fixture as product functionality or model evaluation.
