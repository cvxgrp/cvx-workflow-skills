#!/usr/bin/env python3
"""Check a built release's inventory, metadata, local resources, and adapters."""

import argparse
from pathlib import Path
import sys

try:
    from .build_release import ReleaseError, validate_release
except ImportError:
    from build_release import ReleaseError, validate_release


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("release", type=Path)
    args = parser.parse_args()
    try:
        manifest = validate_release(args.release)
    except (ReleaseError, OSError, ValueError) as exc:
        print(f"validation error: {exc}", file=sys.stderr)
        return 1
    print(f"Valid assembled release: {', '.join(manifest['skills'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
