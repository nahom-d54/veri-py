# Contributors

Thank you for your interest in **veri-py**.

## How to contribute

1. Open an issue to discuss larger changes, or send a focused pull request for bug fixes and small improvements.
2. Keep changes scoped to the problem you are solving.
3. Before opening a PR, run the checks used in CI (from the repo root):

   ```bash
   pip install -e ".[dev]"
   ruff check src tests
   mypy src
   pytest -q
   ```

4. Match existing style: types, naming, and patterns in `src/veri_py`.

## Contributors

Contributors are listed below in alphabetical order. Add yourself in the same PR as your first merged contribution (or ask a maintainer to add you).

<!-- Add names as: - Your Name -->

- Nahom D (original author; see [`pyproject.toml`](pyproject.toml))
