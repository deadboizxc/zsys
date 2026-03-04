[🇬🇧 English](CONTRIBUTING.md) | [🇷🇺 Русский](CONTRIBUTING_RU.md)

# Участие в разработке zsys

Спасибо за ваш вклад! Пожалуйста, прочитайте это руководство перед отправкой PR.

---

## Настройка окружения разработки

```bash
git clone https://github.com/deadboizxc/zsys
cd zsys

# Окружение Python
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# C-расширение
make build-c build-py
```

---

## Правило зависимостей

> **Каждый модуль должен зависеть только от `zsys.core`. Никогда не импортируйте из соседних модулей.**

```python
# ✅ Разрешено
from zsys.core.exceptions import ZsysError
from zsys.core.logging import get_logger

# ❌ Запрещено в zsys.log
from zsys.i18n import t

# ❌ Запрещено в zsys.modules  
from zsys.storage import SQLiteStorage
```

Единственное исключение — `zsys.services.*`, который является явным слоем оркестрации.

---

## Добавление нового модуля

1. Создайте директорию `zsys/yourmodule/`
2. Добавьте `__init__.py` с публичным API
3. Импортируйте только из `zsys.core.*` или stdlib
4. Добавьте `bind_yourmodule.c` (заглушка Python C-привязки)
5. Опционально добавьте `yourmodule.go` (Go-привязка)
6. Добавьте тесты в `tests/test_yourmodule.py`
7. Задокументируйте в `docs/`

---

## Стиль коммитов

Используйте [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(i18n): add CBOR locale serialization

Add binary CBOR format for faster locale loading. Falls back to JSON
if CBOR not available. Benchmark: 3x faster parse on 10k strings.

Closes #42
```

**Области (Scopes)**: `core`, `c`, `python`, `i18n`, `modules`, `log`, `utils`, `storage`,  
`telegram`, `go`, `rust`, `build`, `docs`, `ci`

**Типы**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`

---

## Рекомендации по C-коду

- Стандарт C11 (`-std=c11`)
- Никакого динамического выделения памяти без контракта `zsys_free()`
- Функции, возвращающие `char*`, должны освобождаться через `zsys_free(result)`
- Никакого `Python.h` в `zsys/src/zsys_core.c` — это для всех языковых привязок
- `Python.h` только в `zsys/src/_zsys_core.c`

---

## Тестирование

```bash
make test        # Python-тесты
make test-c      # C-тесты (требует ZSYS_BUILD_TESTS=ON)
```

Новые Python-функции требуют теста в `tests/`. C-функции требуют теста в `tests/c/`.

---

## Версионирование

zsys следует [Semantic Versioning](https://semver.org/). При обновлении версии:

1. Обновите `zsys/__init__.py`
2. Обновите `pyproject.toml`
3. Обновите макросы версии в `zsys/include/zsys_core.h`
4. Обновите `zsys/rust/Cargo.toml`
5. Добавьте запись в `CHANGELOG.md`
