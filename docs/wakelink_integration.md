# zsys × WakeLink (ewsp-core) — Theoretical Integration

> **Status:** Theoretical / Future vision
> **Date:** 2026-03
> **Author:** deadboizxc

---

## 1. TL;DR — Главное открытие

**ewsp-core и zsys — это архитектурные близнецы, написанные одним автором.**

Оба:
- Чистый C, без внешних зависимостей
- CMake, opaque-pointer API, `_new()/_free()/_copy()`
- Doxygen + секционные заголовки (`/* ═══ */`)
- Python ctypes + pure Python fallback
- Kotlin/Android JNI биндинги
- Multi-platform: Linux, ESP32, Android, iOS

Текущее положение — **два параллельных C-ядра** от одного разработчика.
Интеграция = **слияние двух близнецов** в одну универсальную основу.

---

## 2. Что такое WakeLink / ewsp-core?

```
WakeLink — IoT проект для Wake-on-LAN и управления устройствами.

wakelink-repos/
├── firmware/     — ESP32/ESP8266 прошивка (C/C++ Arduino)
├── android/      — Android приложение (Kotlin, Jetpack Compose)
├── cli/          — Python CLI клиент
├── ewsp/         — Универсальная C библиотека (ewsp-core)
└── docs/         — Документация протокола
```

**ewsp-core** (Encrypted WakeLink Secure Protocol):
```
ewsp/
├── include/
│   ├── ewsp.h           — мастер-заголовок
│   ├── ewsp_crypto.h    — SHA256, HMAC, HKDF, XChaCha20 (БЕЗ libsodium!)
│   ├── ewsp_chain.h     — блокчейн-цепочка пакетов
│   ├── ewsp_packet.h    — сериализация/десериализация пакетов
│   ├── ewsp_models.h    — модели данных (Device, Command, Response)
│   ├── ewsp_session.h   — сессионный handshake + key ratcheting
│   ├── ewsp_json.h      — JSON парсер/билдер (без cJSON)
│   ├── ewsp_commands.h  — типы команд
│   └── ewsp_errors.h    — коды ошибок
├── src/             — реализации
└── bindings/
    ├── python/      — ctypes биндинги (= та же структура что zsys._ctypes!)
    └── kotlin/jni/  — JNI для Android
```

---

## 3. Анализ пересечений

### 3.1 Архитектура (ПОЛНОЕ совпадение)

| Аспект | ewsp-core | zsys | Вердикт |
|--------|-----------|------|---------|
| Язык ядра | C11 | C11 | ✅ Идентично |
| Build | CMake | CMake | ✅ Идентично |
| Память | `_new/_free`, strdup | `_new/_free`, strdup | ✅ Идентично |
| API | opaque pointer | opaque pointer | ✅ Идентично |
| Python | ctypes + fallback | ctypes + fallback | ✅ Идентично |
| Android | Kotlin JNI | Нет (пока) | zsys может взять у ewsp |
| ESP32 | Да (прошивка) | Нет | новый домен для zsys |

### 3.2 Модули (что есть в одном, нет в другом)

```
                    ewsp-core          zsys
                    ─────────          ────
Crypto (SHA256)     ✅ (custom C)      ❌ (нет)
HMAC-SHA256         ✅ (custom C)      ❌ (нет)
XChaCha20           ✅ (custom C)      ❌ (нет)
HKDF-SHA256         ✅ (custom C)      ❌ (нет)
Blockchain chain    ✅ ewsp_chain.c    ❌ (stub header только)
Session handshake   ✅ ewsp_session.c  ❌ (нет)
Packet protocol     ✅ ewsp_packet.c   ❌ (нет)
JSON (custom)       ✅ ewsp_json.c     ✅ zsys_core.c (flat JSON)
Device model        ✅ ewsp_models.h   ❌ (нет IoT моделей)
─────────────────────────────────────────────────────
i18n engine         ❌ (Kotlin вручную) ✅ zsys_i18n.c (C, быстрый)
KV storage          ❌ (нет)           ✅ zsys_storage.c (FNV-1a hash)
Module registry     ❌ (нет)           ✅ zsys_registry.c
Message router      ❌ (нет)           ✅ zsys_router.c
User/Chat models    ❌ (нет)           ✅ zsys_user.c, zsys_chat.c
Client config       ❌ (нет)           ✅ zsys_client.c
Text formatting     ❌ (нет)           ✅ zsys_core.c (bold/italic/etc.)
```

**Вывод:** ewsp-core силён в крипто и протоколе; zsys силён в данных и маршрутизации.
Вместе = полноценное универсальное C-ядро.

---

## 4. Стратегии интеграции

### Стратегия A — ewsp_crypto.c → zsys_crypto.c (HIGH IMPACT, LOW EFFORT)

**Самое ценное что можно сделать прямо сейчас.**

`ewsp_crypto.c` реализует SHA-256, HMAC-SHA256, HKDF-SHA256 и XChaCha20
**без libsodium, без OpenSSL** — только стандартный C11.

Это именно то что нужно `zsys_crypto.h` (сейчас stub).

```c
// Было бы: zsys/include/zsys_crypto.h
// SHA256 — из ewsp_crypto.c (переименование префикса ewsp_ → zsys_)

void zsys_sha256(const uint8_t *data, size_t len, uint8_t hash[32]);
void zsys_hmac_sha256(const uint8_t *key, size_t key_len,
                      const uint8_t *data, size_t data_len,
                      uint8_t mac[32]);
// HKDF-SHA256 key derivation
int  zsys_hkdf(const uint8_t *salt, size_t salt_len,
               const uint8_t *ikm,  size_t ikm_len,
               const uint8_t *info, size_t info_len,
               uint8_t *out,        size_t out_len);
// XChaCha20 stream cipher
int  zsys_xchacha20(const uint8_t key[32],
                    const uint8_t nonce[24],
                    uint32_t counter,
                    const uint8_t *in, uint8_t *out, size_t len);
// AEAD
int  zsys_aead_encrypt(const uint8_t key[32],
                       const uint8_t *plain, size_t plain_len,
                       uint8_t *cipher_out,  size_t *cipher_len);
int  zsys_aead_decrypt(const uint8_t key[32],
                       const uint8_t *cipher, size_t cipher_len,
                       uint8_t *plain_out,    size_t *plain_len);
```

Реализация = ewsp_crypto.c с заменой префикса `ewsp_` → `zsys_`.
Нет новых зависимостей. Работает на ESP32, Android, Linux, Windows.

**Выгода для zsys:** наконец есть полноценный криптослой без внешних зависимостей.  
**Выгода для WakeLink:** ewsp-core может использовать zsys как git submodule вместо копии.

---

### Стратегия B — ewsp_chain.c → zsys_blockchain.c (DIRECT REUSE)

`zsys/include/zsys_blockchain.h` — уже существует как stub-заголовок.
`ewsp_chain.c` — готовая реализация блокчейн-цепочки (prev_hash + seq + genesis).

Это **дословное воплощение** запланированного `zsys_blockchain.c`:

```c
// В zsys уже есть stub:
// zsys/include/zsys_blockchain.h → implement from ewsp_chain.c

// Концепции идентичны:
//   ewsp_chain_state_t   →   ZsysChain
//   ewsp_chain_init()    →   zsys_chain_new()
//   ewsp_chain_next_tx() →   zsys_chain_next_seq()
//   ewsp_chain_update()  →   zsys_chain_update()
//   ewsp_chain_verify()  →   zsys_chain_verify()
```

WakeLink уже доказал что эта реализация работает в production на ESP32.
zsys получает battle-tested блокчейн-цепочку.

---

### Стратегия C — ewsp_session.c → zsys_session.h (MEDIUM-TERM)

`ewsp_session.c` — mutual authentication handshake + HKDF key derivation
+ key ratcheting + replay protection через 64-bit counters.

Это **общая задача для любого зашифрованного протокола** — и для WakeLink,
и для IskraTeam, и для любого будущего zsys-based клиента.

```
Текущее положение:
  IskraTeam: PyNaCl → Python session (дублирование)
  WakeLink:  ewsp_session.c → C session
  zsys:      нет session вообще

Будущее:
  Все три → zsys_session.c (= ewsp_session.c переименованный)
```

---

### Стратегия D — zsys_i18n.c → WakeLink Android (QUICK WIN)

WakeLink Android делает i18n вручную через три Kotlin файла:
- `EnglishStrings.kt`
- `RussianStrings.kt`
- `UkrainianStrings.kt`

zsys уже имеет полноценный C i18n движок (`zsys_i18n.c`) — FNV-1a хеш,
JSON/CBOR загрузка, multi-lang.

**Через уже существующий JNI bridge** (ewsp уже умеет JNI) можно подключить
zsys i18n к Android за 1-2 часа:

```kotlin
// Вместо:
object Strings {
    fun get(key: String, lang: String): String = when(lang) {
        "ru" -> RussianStrings.map[key] ?: key
        ...
    }
}

// Станет:
// zsys i18n через JNI (уже есть ewsp JNI bridge как шаблон):
external fun zsysI18nGet(key: String): String
// Локали в assets/locales/ru.json — уже есть формат в zsys!
```

---

### Стратегия E — zsys_storage.c → ewsp session persistence (CLEAN DESIGN)

`ewsp_session.h` упоминает persistence состояния сессии.
Сейчас в WakeLink это Android EncryptedSharedPreferences (Kotlin-only).

`ZsysKV` — универсальный C KV-store, может использоваться для:
- Хранения состояния сессии в ewsp (on ESP32 через SPIFFS)
- Хранения chain state (`tx_seq`, `tx_hash`, `rx_seq`, `rx_hash`)
- Кэша device info

```c
// WakeLink firmware, вместо custom storage:
ZsysKV *session_store = zsys_kv_new(0);
zsys_kv_set(session_store, "tx_seq", "42");
zsys_kv_set(session_store, "tx_hash", "a1b2c3...");

// Сохранить в SPIFFS:
char *json = zsys_kv_to_json(session_store);
fs_write("session.json", json);
zsys_free(json);
```

**Работает на ESP32** — zsys_storage.c использует только stdlib.h, string.h, stdio.h.
ESP32 имеет полноценный C stdlib.

---

## 5. Мегастратегия — Слияние в единое C-ядро

Самый амбициозный сценарий: **ewsp-core и zsys сливаются в один проект.**

```
libzsys_core.so v2.0 (hypothetical)
════════════════════════════════════════════════════════

zsys/ (модули данных и утилит)     ewsp/ (крипто и протокол)
────────────────────────────────   ─────────────────────────────
zsys_core.c    — text utils        zsys_crypto.c  — SHA256/HMAC/XChaCha20
zsys_router.c  — message routing   zsys_chain.c   — blockchain
zsys_registry.c — module registry  zsys_packet.c  — packet encode/decode
zsys_i18n.c    — i18n              zsys_session.c — session handshake
zsys_user.c    — ZsysUser          zsys_device.c  — ZsysDevice (IoT)
zsys_chat.c    — ZsysChat          zsys_commands.c — command types
zsys_client.c  — ZsysClientConfig  zsys_json.c    — JSON parser
zsys_storage.c — ZsysKV            zsys_errors.c  — unified error codes

════════════════════════════════════════════════════════
Один .so, одни биндинги, один CMake

Потребители:
  zxc_userbot    → Python ctypes → libzsys_core.so
  IskraTeam API  → Go CGo       → libzsys_core.so
  WakeLink CLI   → Python ctypes → libzsys_core.so
  WakeLink Android → Kotlin JNI → libzsys_core.so
  WakeLink Firmware → #include  → libzsys_core.a (static, ESP32)
  Будущий Go клиент → CGo        → libzsys_core.so
```

**ESP32 совместимость:** zsys_core.c, zsys_storage.c, zsys_crypto.c (=ewsp_crypto.c)
используют только стандартный C — они компилируются с Arduino ESP32 SDK без изменений.

---

## 6. Текущие дубликаты — что устранит интеграция

| Компонент | Сейчас | После интеграции |
|-----------|--------|-----------------|
| SHA-256 | ewsp_crypto.c + Python hashlib + Android.security | zsys_crypto.c везде |
| HMAC-SHA256 | ewsp_crypto.c + Python hmac + Android | zsys_crypto.c везде |
| JSON builder | ewsp_json.c + zsys flat JSON + Kotlin kotlinx.serialization | zsys_json.c + Kotlin parser |
| KV storage | Android SharedPrefs + ESP32 custom + Python dict | zsys_kv везде |
| i18n | Kotlin ручной + zsys C engine | zsys_i18n везде через JNI |
| Python ctypes | ewsp/bindings/python/ewsp_core.py + zsys/_ctypes/ | один zsys/_ctypes/ |
| Error codes | ewsp_errors.h + zsys (нет unified) | zsys_errors.h везде |

---

## 7. IoT-специфичные расширения zsys (новые модули)

После слияния zsys получает новые C-модули которых сейчас нет:

```c
// zsys/include/zsys_device.h — IoT устройство (из ewsp_models.h)
typedef struct ZsysDevice ZsysDevice;

ZsysDevice *zsys_device_new(void);
void        zsys_device_free(ZsysDevice *d);
void        zsys_device_set_id(ZsysDevice *d, const char *id);
void        zsys_device_set_ip(ZsysDevice *d, const char *ip);
void        zsys_device_set_mac(ZsysDevice *d, const char *mac);
// ...

// zsys/include/zsys_crypto.h — крипто без внешних зависимостей (из ewsp_crypto.h)
void zsys_sha256(const uint8_t *data, size_t len, uint8_t out[32]);
void zsys_hmac_sha256(/* ... */);
int  zsys_xchacha20_aead_encrypt(/* ... */);
int  zsys_xchacha20_aead_decrypt(/* ... */);

// zsys/include/zsys_chain.h — blockchain цепочка (из ewsp_chain.h)
typedef struct ZsysChain ZsysChain;
ZsysChain *zsys_chain_new(void);
void       zsys_chain_free(ZsysChain *c);
int        zsys_chain_next(ZsysChain *c, uint8_t *prev_hash_out);
int        zsys_chain_update(ZsysChain *c, uint64_t seq, const char *packet_hash);
int        zsys_chain_verify(ZsysChain *c, uint64_t seq, const char *prev_hash);
```

---

## 8. Что это даёт каждому проекту

### WakeLink получает:
- `zsys_i18n.c` — убрать 3 ручных Kotlin файла с переводами
- `zsys_kv` — portable storage для session state (ESP32 + Android)
- `zsys_router.c` — command dispatcher для firmware
- `zsys_user.c` — модель пользователя для cloud backend

### zsys получает:
- `ewsp_crypto.c` → `zsys_crypto.c` — полноценный крипто без libsodium
- `ewsp_chain.c` → `zsys_chain.c` — реализует давно запланированный `zsys_blockchain.h`
- `ewsp_session.c` → `zsys_session.c` — handshake + key ratcheting
- `ewsp_device.h` → `zsys_device.h` — IoT domain модели
- JNI биндинги — шаблон для Android

### Оба проекта:
- Единый Python ctypes слой вместо двух параллельных
- Единые коды ошибок
- Единый JSON парсер
- **Работа на ESP32** — если zsys остаётся в рамках стандартного C

---

## 9. Практические первые шаги

```
Шаг 1 (1-2 часа): Скопировать ewsp_crypto.c → zsys/src/zsys_crypto.c
  - Заменить префикс ewsp_ → zsys_
  - Добавить zsys_crypto.h в include/
  - Добавить в CMakeLists.txt
  - Тест: zsys_sha256 / zsys_hmac_sha256 из Python ctypes

Шаг 2 (2-3 часа): Реализовать zsys_chain.c на базе ewsp_chain.c
  - Закрывает давно открытый stub zsys_blockchain.h
  - Тест: genesis → packet1 → packet2 цепочка

Шаг 3 (когда WakeLink стабилизируется):
  - Подключить WakeLink firmware к zsys как submodule
  - ewsp-core становится тонким wrapper над zsys

Шаг 4 (долгосрочно):
  - Единые ctypes биндинги для ewsp + zsys
  - WakeLink Android JNI → libzsys_core.so
```

---

## 10. Риски

| Риск | Митигация |
|------|-----------|
| Сложность ESP32 — stdlib ограничения | zsys_crypto.c уже работает на ESP32 как ewsp_crypto.c |
| Разные версии CMake | ESP32 использует свой CMake, не system — держать отдельный CMakeLists для embedded |
| ABI изменения сломают прошивки | Для embedded использовать static lib (.a), не .so |
| Over-engineering | Начать с Шага 1 (только крипто), доказать ценность до слияния |

---

*ewsp-core и zsys родились параллельно потому что решали разные задачи —
IoT vs мессенджеры. Но их C-архитектура идентична настолько, что слияние
не требует переписывания — только переименование и реорганизация.*
