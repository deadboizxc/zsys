[🇬🇧 English](c_api.md) | [🇷🇺 Русский](c_api_RU.md)

# Справочник C API

Все функции объявлены в `zsys/include/zsys_core.h`.

## Модель памяти

Функции, возвращающие `char*`, выделяют память в куче.  
**Всегда освобождайте через `zsys_free(ptr)`.**

```c
char *result = zsys_escape_html("<b>test</b>", 10);
printf("%s\n", result);
zsys_free(result);
```

## Функции для работы с текстом

### `zsys_escape_html`
```c
char *zsys_escape_html(const char *text, size_t len);
```
Экранирует `&`, `<`, `>`, `"` в HTML-сущности.

### `zsys_strip_html`
```c
char *zsys_strip_html(const char *text, size_t len);
```
Удаляет все HTML-теги и деэкранирует сущности.

### `zsys_truncate_text`
```c
char *zsys_truncate_text(const char *text, size_t len, size_t max_chars, const char *suffix);
```
Обрезка с учётом UTF-8. Добавляет `suffix` (например, `"…"`), если текст был обрезан.

### `zsys_split_text`
```c
char **zsys_split_text(const char *text, size_t len, size_t max_chars, size_t *out_count);
```
Разбивает текст на фрагменты максимум по `max_chars` символов.  
Возвращает массив строк. Освобождать через `zsys_free_array()`.

### `zsys_format_bytes`
```c
char *zsys_format_bytes(uint64_t size);
```
Форматирует количество байт: `1536 → "1.5 KB"`, `1073741824 → "1.0 GB"`.

## HTML-форматирование

```c
char *zsys_format_bold(const char *text, size_t len);     // <b>text</b>
char *zsys_format_italic(const char *text, size_t len);   // <i>text</i>
char *zsys_format_code(const char *text, size_t len);     // <code>text</code>
char *zsys_format_pre(const char *text, size_t len, const char *lang);  // <pre lang>
char *zsys_format_link(const char *text, size_t len, const char *url);  // <a href>
char *zsys_format_mention(const char *name, size_t nlen, int64_t user_id);
char *zsys_format_spoiler(const char *text, size_t len);
char *zsys_format_quote(const char *text, size_t len);
```

## Функции времени

### `zsys_format_duration`
```c
char *zsys_format_duration(double seconds);
```
`3661.0 → "1h 1m 1s"`

### `zsys_human_time`
```c
char *zsys_human_time(double seconds, int short_form);
```
Человекочитаемое время по-русски. `short_form=1`: `"1 ч. 1 мин."`, `short_form=0`: `"1 час 1 минута"`.

### `zsys_parse_duration`
```c
double zsys_parse_duration(const char *text);
```
`"1h30m" → 5400.0`, `"2d" → 172800.0`

## Маршрутизация

### `zsys_match_prefix`
```c
int zsys_match_prefix(const char *text, const char **prefixes, const char **triggers,
                      size_t prefix_count, size_t trigger_count,
                      char **out_cmd, char **out_args);
```
Возвращает 1 при совпадении. Устанавливает `out_cmd` и `out_args` (оба нужно освободить).

## Мета-данные модуля

### `zsys_parse_meta_comments`
```c
ZsysMeta *zsys_parse_meta_comments(const char *source, size_t len);
void zsys_free_meta(ZsysMeta *meta);
```

### `zsys_build_help_text`
```c
char *zsys_build_help_text(const char *name, const char *commands, const char *prefix);
```

## Терминал

### `zsys_ansi_color`
```c
char *zsys_ansi_color(const char *text, int color_code);
```
Оборачивает текст в ANSI escape-коды. `color_code` = стандартный номер ANSI-цвета.

## Логирование

### `zsys_format_json_log`
```c
char *zsys_format_json_log(const char *level, const char *message, const char *timestamp);
```
Возвращает JSON-строку: `{"level":"INFO","msg":"...","ts":"..."}`.
