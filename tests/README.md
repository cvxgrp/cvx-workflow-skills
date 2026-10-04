# Skill format checks

```bash
uv sync --locked
uv run --no-sync python -B -m tests
```

The checker requires `SKILL.md`, valid Agent Skills frontmatter and metadata,
a skill name matching its folder, and a nonempty instruction body. It uses the
reference validator and does not run helpers, solve models, or call a model.
Only `skills-ref` and its small dependency set are required.

Optional release assembly is separate:

```bash
uv run --no-sync python -B -m tests.build_release
uv run --no-sync python -B -m tests.validate_release artifacts/release
```

Assembly follows `release.json`. Generated releases belong under ignored
`artifacts/`. The previous numerical tests, graders, fixtures, live adapters,
and disabled CI template are retained locally in `artifacts/history/development-suite/`.
They are not part of the shared validation package.

CI uses the same offline format, assembly, and release-validation commands in
[.github/workflows/ci.yml](../.github/workflows/ci.yml), plus a package-version
consistency check. It makes no live model calls and does not run numerical solver
checks or publish releases.

## Versioning and releases

Use one version for the collection. `release.json` is authoritative; keep
`pyproject.toml` aligned and regenerate `uv.lock` with `uv lock` after changing
the project version. The builder generates the adapter versions. During `0.x`,
use patch increments for corrections within existing scope and minor increments
for new capabilities or changes to user-facing contracts. Routine PRs do not
need a version bump; prepare one when you choose to release.

1. Open a release-preparation PR with any version and support-status updates.
   For the first release, the existing version is `0.1.0`.
2. Merge after the `validate` CI check passes. Wait for CI on the merged commit
   to pass too, then tag that exact commit:

   ```bash
   git fetch origin main
   git tag -a v0.1.0 <passing-main-commit> -m "Release 0.1.0"
   git push origin v0.1.0
   ```

3. The [release workflow](../.github/workflows/release.yml) runs only on `v*`
   tag pushes. It requires the commit to be in `main` history, checks skill
   format and version consistency, assembles and validates the distribution,
   and creates four ZIP bundles plus `SHA256SUMS` in a **draft** GitHub Release.
4. Review the draft notes, including changes, source commit, and support coverage.
   Download a bundle and check its layout/checksum, then publish the draft.
   The bundles are the downloadable installation artifacts; GitHub's automatic
   source archives contain the authoring repository.

Merging a PR never creates a release. Pushing a tag creates a draft, not a public
release. Published tags/assets are fixed; corrections get a new version. The
workflow refuses to replace an existing release. If an upload fails partway,
delete only the incomplete draft before rerunning the failed workflow; keep its
tag. No extra publishing service or account token is needed: the tag workflow
uses GitHub's repository token with `contents: write`.

To preview the exact packaging step locally after setup:

```bash
uv run --no-sync python -B -m tests.package_release --tag v0.1.0
```

This rebuilds and validates `artifacts/release/`, then writes the full collection
and individual skill ZIPs plus checksums under `artifacts/packages/v0.1.0/`.
Individual ZIPs have a top-level folder named for the skill, with its complete
resources and license. The full ZIP has a `cvx-workflow-skills-0.1.0/` root with
both adapter manifests. Packaging refuses existing output; use a new ignored
directory with `--output` for another preview. It never publishes or installs.

## Main branch protection

Protect `main` with required PRs, the GitHub Actions `validate` status check,
branches up to date before merging, and resolved review conversations. Keep
force pushes and deletion disabled. Use squash merges for routine PRs. Require
an approving review when another maintainer is available; otherwise allow PRs
with passing CI without a required approval so the sole maintainer can merge.
Apply the rules to administrators too if all changes should follow this path.
Branch protection does not prevent you from pushing a separate release tag.
