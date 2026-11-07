# Original Study preservation

This directory references the original evidence in place. No original file is
moved or replaced. `manifest.json` pins all existing accession files, original
pilot configurations and dependency manifests by SHA-256 and size.

The Original Study entry revision is
`f51a8360aca39a428ca41bfc9afe10447d175d72`. Genuine final inference ran at
`e5dcc3c61cc6ded130a4f118825fc324e90a7e3a`, including its documented extra LF0.0
views. The corrected pre-manuscript revision has the historical 238-test suite.
See [claims](../../docs/RESEARCH_CLAIMS.md) for exact units and conditions.

Run `uv run python scripts/research/verify_legacy.py` to check preservation.
This checks saved bytes, not fresh model inference. Old code remains available
in immutable Git history; use a separate checkout/directory for legacy reproduction.
New results belong under a separately labeled Expanded Study directory.
