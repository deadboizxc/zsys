# Contributing to zsys

Thank you for contributing! Please read this guide before submitting a PR.

---

## Development setup

```bash
git clone https://github.com/deadboizxc/zsys
cd zsys

# Python environment
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# C extension
make build-c build-py
```

---

## Dependency rule

> **Every module must depend only on `zsys.core`. Never import from sibling modules.**

```python
# ✅ Allowed
from zsys.core.exceptions import ZsysError
from zsys.core.logging import get_logger

# ❌ Forbidden in zsys.log
from zsys.i18n import t

# ❌ Forbidden in zsys.modules  
from zsys.storage import SQLiteStorage
```

The only exception is `zsys.services.*` which is an explicit orchestration layer.

---

## Adding a new module

1. Create `zsys/yourmodule/` directory
2. Add `__init__.py` with public API
3. Import only from `zsys.core.*` or stdlib
4. Add `bind_yourmodule.c` (Python C binding placeholder)
5. Optionally add `yourmodule.go` (Go binding)
6. Add tests to `tests/test_yourmodule.py`
7. Document in `docs/`

---

## Commit style

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(i18n): add CBOR locale serialization

Add binary CBOR format for faster locale loading. Falls back to JSON
if CBOR not available. Benchmark: 3x faster parse on 10k strings.

Closes #42
```

**Scopes**: `core`, `c`, `python`, `i18n`, `modules`, `log`, `utils`, `storage`,  
`telegram`, `go`, `rust`, `build`, `docs`, `ci`

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`

---

## C code guidelines

- C11 standard (`-std=c11`)
- No dynamic allocation without `zsys_free()` contract
- Functions returning `char*` must be freed with `zsys_free(result)`
- No `Python.h` in `zsys/src/zsys_core.c` — it's for all language bindings
- `Python.h` only in `zsys/src/_zsys_core.c`

---

## Testing

```bash
make test        # Python tests
make test-c      # C tests (requires ZSYS_BUILD_TESTS=ON)
```

New Python functions need a test in `tests/`. C functions need a test in `tests/c/`.

---

## Versioning

zsys follows [Semantic Versioning](https://semver.org/). When bumping version:

1. Update `zsys/__init__.py`
2. Update `pyproject.toml`
3. Update `zsys/include/zsys_core.h` version macros
4. Update `zsys/rust/Cargo.toml`
5. Add `CHANGELOG.md` entry
