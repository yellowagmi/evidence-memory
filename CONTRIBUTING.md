# Contributing

Evidence Memory is an early library extracted from an existing application.
Useful contributions improve the public component and preserve its evidence,
chronology, revision, and transaction contracts.

Open an issue describing a concrete user need or reproducible defect. For public
API, identity, or storage changes, discuss the proposed compatibility behavior
before writing a large change. Small fixes can go directly to a pull request.

Install the package and run its tests:

```sh
python -m pip install .
python -m unittest discover -s tests -v
```

Add a focused regression check for changed behavior. Tests must run without model
credentials, private journals, network services, or application datasets. Use
small self-contained fixtures; do not include real transcripts, account records,
or copyrighted source collections in an issue or patch. `TMPDIR` controls test
scratch placement when needed.

Explain the problem, resulting behavior, compatibility implications, and validation
in the pull request. Performance claims need a reproducible workload and baseline.
Memory usefulness claims need an outcome comparison; retrieval alone is insufficient.

The project uses the MIT license. By contributing, you agree to license your
contribution under that license. Identify any third-party code and its license.
