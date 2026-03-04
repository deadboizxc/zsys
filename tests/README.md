[🇬🇧 English](README.md) | [🇷🇺 Русский](README_RU.md)

# core/tests/ — Тесты ядра zsys

## Структура

```
core/tests/
├── conftest.py         # Общие fixtures
├── test_config.py      # Тесты config (BaseConfig, env)
├── test_db.py          # Тесты db (SQLite, LMDB, factory)
├── test_log.py         # Тесты logging (ColorLogger, Printer)
├── test_utils.py       # Тесты utils (shell_exec, paths)
├── test_http.py        # Тесты transport (HttpClient)
├── test_crypto.py      # Тесты domain (hash, tokens)
├── test_i18n.py        # Тесты i18n (I18N, translations)
└── test_modules.py     # Тесты modules (Router, Context)
```

## Запуск

```bash
# Все тесты
pytest -v

# Конкретный файл
pytest zsys/core/tests/test_config.py -v

# С покрытием
pytest --cov=zsys --cov-report=html

# Только async тесты
pytest -m asyncio
```

## Fixtures (conftest.py)

| Fixture         | Описание                         |
|-----------------|----------------------------------|
| `tmp_env_file`  | Временный `.env` файл            |
| `tmp_db_path`   | Путь для временной БД            |
| `tmp_log_file`  | Путь для временного лог-файла    |
| `clean_env`     | Очистка переменных окружения     |
| `mock_logger`   | Mock-логгер для тестов           |
| `sample_data`   | Типовые данные для тестов БД     |

## Установка зависимостей

```bash
# Минимальная (для тестов)
pip install -e ".[dev]"

# Полная (все драйверы БД)
pip install -e ".[dev,db-all]"
```

## Рекомендации

- Каждый тест должен быть изолированным
- Использовать `tmp_path` для временных файлов
- Async тесты помечать `@pytest.mark.asyncio`
- Для HTTP использовать `aioresponses`
