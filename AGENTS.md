# Repository working agreement

This directory is both a Claude Code skill installation and a Git repository. Keep public code and ignored local preferences separate.

Before changes, inspect the current branch, worktree and fetched upstream. Pull only with `--ff-only` when clean; do not reset, force-push, discard user edits or silently resolve divergent histories.

Work on a feature branch before committing. Run the test script(s) and `scripts/check_release.py`. Commit or push only when the user asks; after an authorized push fetch and verify local HEAD equals its upstream and the public worktree is clean.

`.local/` is intentionally ignored. It may contain user defaults or private reference pointers; do not stage it, print its identifiers, or include it in examples, releases or packages. Local preferences cannot override data, permission or publication boundaries.

Do not publish original private materials, access tokens, signed resource URLs, user-document locators or machine-specific paths. Examples must be synthetic or independently authorized; brand names do not imply a license to third-party media or fonts.

The pre-push gate runs deterministic local tests and public-package checks. It does not invoke model APIs or external publishing. CI outcomes and semantic/visual review are distinct; do not claim model or platform evaluations were run when only unit checks passed.
