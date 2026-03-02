# zsys × IskraTeam — Theoretical Integration Plan

> **Status:** Theoretical / Future vision  
> **Date:** 2026-03  
> **Author:** deadboizxc  

---

## 1. Overview

Both `zsys` and `IskraTeam` are sibling projects under the same author.
Currently they are completely independent. This document describes how they
could share code, leverage each other's strengths, and eventually converge
toward a unified system foundation.

### What is IskraTeam?

```
IskraTeam/
├── api/          — FastAPI backend (Python, SQLAlchemy, PostgreSQL, Redis)
├── sdk/          — Python client SDK (iskra package)
├── userbot/      — Python userbot running on Iskra platform
├── AyuGram4A/    — Android Telegram client fork (Kotlin/Java)
└── proto/        — JSON-RPC 2.0 schema definitions
```

Iskra is a **custom E2E-encrypted messenger** with:
- JSON-RPC 2.0 over WebSocket (primary) + HTTP (debug)
- Client-side encryption: X25519 + ChaCha20-Poly1305 + Ed25519 (via PyNaCl)
- Public keys stored on server; **private keys never leave the device**
- Module-based userbot running on top of IskraClient

### What is zsys?

```
zsys/
├── zsys/src/      — C core (models, router, registry, i18n, storage)
├── zsys/_ctypes/  — portable Python bindings (ctypes)
├── zsys/_core/    — CPython extension (fast hot paths)
├── zsys/telegram/ — Telegram framework wrappers (Pyrogram, aiogram, etc.)
├── zsys/storage/  — Multi-backend storage (SQLite, Redis, MongoDB, ...)
├── zsys/i18n/     — C-backed internationalisation engine
└── zsys/modules/  — Universal module loading & routing system
```

zsys is a **framework foundation / universal C-backed core library** for
bots, messengers, and system tools.

---

## 2. Overlap Analysis

### 2.1 Data Models (HIGH overlap)

Both projects define nearly identical domain objects:

| Concept     | zsys C type         | IskraTeam                     |
|-------------|---------------------|-------------------------------|
| User        | `ZsysUser`          | `iskra.types.User` (Pydantic) |
| Chat        | `ZsysChat`          | `iskra.types.Chat`            |
| Message     | _(no C type yet)_   | `iskra.types.Message`         |
| Client conf | `ZsysClientConfig`  | `IskraClient` fields          |
| KV store    | `ZsysKV`            | _session state in Redis_      |
| User (DB)   | _(ORM layer)_       | `iskra_api.models.User` (SQLAlchemy) |

**Conclusion:** zsys C models could become the **shared canonical representation**
that both projects map to/from. IskraTeam converts: `DB row → ZsysUser → RPC JSON`.
zsys converts: `Pyrogram User → ZsysUser → zsys logic`.

### 2.2 Module System (HIGH overlap)

| Feature          | zsys                          | IskraTeam Userbot              |
|------------------|-------------------------------|--------------------------------|
| Module base      | `zsys.modules.Module`         | `iskra_userbot.Module`         |
| Command routing  | `zsys_router.c` + Python wrap | `iskra_userbot.Dispatcher`     |
| Module loader    | `zsys.modules.ModuleLoader`   | `iskra_userbot.ModuleLoader`   |
| Module registry  | `zsys_registry.c`             | dict inside `Dispatcher`       |
| Decorator-based  | `@zsys.on(filters=...)`       | `@command("ping")`             |

Both implement the **exact same pattern** independently. This is prime
code-reuse territory.

### 2.3 i18n (MEDIUM overlap)

| Feature       | zsys                            | IskraTeam                        |
|---------------|---------------------------------|----------------------------------|
| Engine        | C (`zsys_i18n.c`) + Python bind | None (raw Python strings)        |
| Format        | Flat JSON + CBOR binary         | Hardcoded strings                |
| Multi-lang    | Yes (hash-table per language)   | No                               |
| Performance   | C-speed (FNV-1a hash lookup)    | N/A                              |

IskraTeam has no i18n at all currently. zsys `i18n` module could be dropped
directly into `iskra_api` for error messages, `iskra_userbot` for responses.

### 2.4 Storage (MEDIUM overlap)

| Feature         | zsys                              | IskraTeam                        |
|-----------------|-----------------------------------|----------------------------------|
| In-memory KV    | `ZsysKV` (C, FNV-1a hash table)   | None (Python dict)               |
| Persistent      | `zsys.storage.sqlite`, `.redis`   | `iskra_api` uses Postgres+Redis  |
| Session state   | `ZsysKV` or `zsys.storage`        | Stored in Redis                  |
| Multi-backend   | Factory pattern (SQLite/Redis/...) | Hardwired Postgres+Redis         |

### 2.5 Transport (LOW-MEDIUM overlap)

| Feature       | zsys                               | IskraTeam                      |
|---------------|------------------------------------|--------------------------------|
| HTTP client   | `zsys.transport.http`              | `iskra.transport.http`         |
| WebSocket     | `zsys.transport.wss`               | `iskra.transport.wss`          |
| RPC protocol  | Custom routing (not JSON-RPC)      | JSON-RPC 2.0 over WSS          |
| Serialization | cbor2 + custom flat JSON           | JSON only                      |

These are close enough to unify under a shared base, but different enough
that convergence requires deliberate redesign.

### 2.6 Crypto (LOW overlap — philosophically same goal)

| Feature     | zsys                              | IskraTeam Crypto              |
|-------------|-----------------------------------|-------------------------------|
| Library     | Python `cryptography`, `pycryptodome` | PyNaCl (NaCl/libsodium)    |
| Algorithms  | AES, RSA, ECC (Python wrappers)   | X25519, ChaCha20-Poly1305, Ed25519 |
| C backend   | None yet                          | libsodium (via PyNaCl)        |
| E2E focus   | No (utility crypto)               | Yes (core feature)            |

**Opportunity:** zsys C core could wrap `libsodium` directly (via a new
`zsys/src/zsys_crypto.c`), exposing the same X25519/Ed25519 primitives that
IskraTeam uses — but from C, available to any language.

---

## 3. Integration Strategies

### Strategy A — zsys as shared utility library (Near-term, LOW effort)

IskraTeam adds zsys as a dependency. It uses:
- `zsys.i18n` for localising API error messages and userbot responses
- `zsys.utils.text` for text formatting in Iskra userbot responses
- `zsys.log.printer` for consistent styled terminal output
- `zsys.storage.sqlite` as a local key store for the SDK (session tokens)

```python
# iskra_api/main.py — near-term usage
from zsys.i18n import I18n

i18n = I18n()
i18n.load_json("locales/en.json")
i18n.set_lang("ru")

# In RPC error handler:
raise RpcError(404, i18n.get("errors.user_not_found"))
```

**Effort:** Low. zsys is already a pip-installable package.  
**Risk:** zsys becomes a dependency of IskraTeam — coupling.  
**Benefit:** IskraTeam gains i18n, text utils, and storage backends for free.

---

### Strategy B — zsys C models as canonical data layer (Medium-term)

Both projects map their domain objects TO/FROM `ZsysUser`, `ZsysChat`, etc.
The C struct becomes the "lingua franca" in memory — no conversion overhead
between Python, Go, or any future language.

```
IskraTeam flow:
  PostgreSQL row
      │
      ▼ (SQLAlchemy ORM → Pydantic)
  iskra_api.models.User         ← current dead end
      │
      ▼ (new: to_zsys())
  ZsysUser (C struct in memory)  ← universal
      │
      ├──→ zsys_user_to_json()  → RPC response JSON
      ├──→ Go binding           → future Go backend
      └──→ Rust binding         → future Rust client
```

```python
# New method in iskra_api/models/user.py
from zsys._ctypes import User as ZsysUser

class User(Base):
    ...
    def to_zsys(self) -> ZsysUser:
        u = ZsysUser()
        u.id         = self.id
        u.username   = self.username
        u.first_name = self.display_name or ""
        u.created_at = int(self.created_at.timestamp())
        return u

    @classmethod
    def from_zsys(cls, zu: ZsysUser) -> "User":
        return cls(id=zu.id, username=zu.username, ...)
```

**Effort:** Medium. Requires adding conversion methods everywhere.  
**Benefit:** Any future language (Go, Rust, Kotlin) gets Iskra data for free
via the C layer — no need to redefine User/Chat in each language.

---

### Strategy C — zsys Module System in Iskra Userbot (Medium-term)

Replace `iskra_userbot.Dispatcher` + `iskra_userbot.ModuleLoader` with
the zsys module system, adapted for the Iskra platform:

```python
# Current iskra_userbot approach:
class MyModule(Module):
    @command("ping")
    async def ping(self, ctx):
        await ctx.reply("pong")

# Future with zsys module system:
from zsys.modules import Module
from zsys.modules.context import BaseContext

class IskraContext(BaseContext):
    """Adapter: wraps IskraClient message into zsys context."""
    ...

class MyModule(Module):
    @zsys.command("ping")
    async def ping(self, ctx: IskraContext):
        await ctx.reply("pong")
```

The zsys module loader handles: hot-reload, dependency ordering, registry,
command routing — things currently duplicated in `iskra_userbot`.

**Effort:** Medium-High. Requires writing an `IskraContext` adapter.  
**Benefit:** Userbot features (hot-reload, module management) immediately
available for IskraTeam without re-implementing.

---

### Strategy D — zsys as universal C crypto layer (Long-term)

Currently IskraTeam uses PyNaCl (Python bindings to libsodium) for E2E.
A future `zsys/src/zsys_crypto.c` could wrap libsodium directly:

```c
// zsys/include/zsys_crypto.h (proposed)
typedef struct ZsysKeyPair ZsysKeyPair;

ZsysKeyPair  *zsys_keypair_generate(void);
void          zsys_keypair_free(ZsysKeyPair *kp);

// X25519 shared secret derivation
int  zsys_x25519_dh(
    const uint8_t *my_private,   // 32 bytes
    const uint8_t *their_public, // 32 bytes
    uint8_t *shared_out          // 32 bytes output
);

// ChaCha20-Poly1305 AEAD
int  zsys_chacha20poly1305_encrypt(
    const uint8_t *key,     size_t key_len,
    const uint8_t *nonce,   size_t nonce_len,
    const uint8_t *plain,   size_t plain_len,
    uint8_t *cipher_out,    size_t *cipher_len_out
);

// Ed25519 sign / verify
int  zsys_ed25519_sign(
    const uint8_t *signing_key, // 64 bytes
    const uint8_t *msg,         size_t msg_len,
    uint8_t *sig_out            // 64 bytes
);
int  zsys_ed25519_verify(
    const uint8_t *verify_key,  // 32 bytes
    const uint8_t *msg,         size_t msg_len,
    const uint8_t *sig          // 64 bytes
);
```

Benefits:
- IskraTeam Android client (AyuGram4A / Kotlin/JNI) can use the same crypto
  as the Python server — via JNI bridge to `libzsys_core.so`
- Future Rust client uses zsys Rust bindings instead of duplicating crypto
- Performance-critical key derivation (HKDF) runs in C, not Python

**Effort:** High. Requires linking libsodium (`target_link_libraries(zsys_core sodium)`).  
**Benefit:** Single crypto implementation, verified, in C, usable from every language.

---

### Strategy E — JSON-RPC router in C (Long-term, HIGH impact)

IskraTeam uses JSON-RPC 2.0. `zsys_router.c` is a message routing engine.
A future `zsys_rpc.c` could implement JSON-RPC 2.0 dispatch in C:

```c
// zsys/include/zsys_rpc.h (proposed)
typedef int (*ZsysRpcHandler)(
    const char *params_json,
    char       *result_json_out,
    size_t      result_max_len
);

typedef struct ZsysRpcRouter ZsysRpcRouter;

ZsysRpcRouter *zsys_rpc_new(void);
void           zsys_rpc_free(ZsysRpcRouter *r);
int            zsys_rpc_register(ZsysRpcRouter *r,
                                 const char *method,
                                 ZsysRpcHandler handler);
int            zsys_rpc_dispatch(ZsysRpcRouter *r,
                                 const char *request_json,
                                 char       *response_json_out,
                                 size_t      out_len);
```

This router could be:
- Embedded in `iskra_api` (Python calls it via ctypes)
- Used by a future Go `iskra_api` rewrite
- Used in a future Rust `iskra_api` rewrite
- Used in Android (JNI) for the native Iskra client

**Effort:** Very High. But would be the most powerful unification.

---

## 4. Code IskraTeam → zsys (What IskraTeam can contribute to zsys)

IskraTeam has things zsys is missing:

| Component                       | What it brings to zsys            |
|---------------------------------|-----------------------------------|
| `iskra.crypto` (X25519/Ed25519) | Real E2E crypto models for zsys   |
| `iskra.transport.wss`           | Robust WebSocket transport        |
| `iskra_api` RPC routing         | JSON-RPC 2.0 patterns             |
| `iskra_userbot.Context`         | Clean context abstraction         |
| `proto/*.schema.json`           | Schema validation patterns        |

Concretely, these could be **upstreamed** into zsys:
1. `iskra.transport.wss` → `zsys.transport.wss` (currently stub)
2. `iskra.crypto.CryptoManager` → `zsys.security.e2e` (currently generic crypto)
3. `iskra_userbot.Context` pattern → `zsys.modules.context` (already partially done)

---

## 5. Proposed Unified Architecture (Theoretical End-State)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        libzsys_core.so                                  │
│  ┌───────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┐  │
│  │ zsys_user │ │zsys_chat │ │zsys_kv   │ │zsys_i18n │ │zsys_crypto  │  │
│  │ zsys_msg  │ │zsys_reg. │ │zsys_rtr. │ │zsys_rpc  │ │(libsodium)  │  │
│  └───────────┘ └──────────┘ └──────────┘ └──────────┘ └─────────────┘  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
         ┌───────────────────────┼────────────────────────┐
         │                       │                        │
         ▼                       ▼                        ▼
┌─────────────────┐   ┌──────────────────┐   ┌────────────────────────┐
│  Python layer   │   │   Go layer       │   │   Rust layer           │
│  zsys._ctypes   │   │  bindings/go/    │   │  bindings/rust/        │
│  zsys._core     │   │  cgo bindings    │   │  bindgen + safe wrap   │
└────────┬────────┘   └────────┬─────────┘   └───────────┬────────────┘
         │                     │                         │
    ┌────┴─────┐           ┌───┴────┐              ┌─────┴──────┐
    │ zxc_     │           │ iskra_ │              │ future     │
    │ userbot  │           │ api v3 │              │ rust client│
    │ (Pyrogram│           │ (Go    │              │            │
    │  based)  │           │  based)│              │            │
    └──────────┘           └────────┘              └────────────┘
         │                     │
    ┌────┴─────┐          ┌────┴────────┐
    │Telegram  │          │ IskraTeam   │
    │  API     │          │ Platform    │
    └──────────┘          └─────────────┘
```

In this end-state:
- `libzsys_core.so` is the **single universal foundation**
- `zxc_userbot` uses it for Telegram automation (Python layer)
- `iskra_api` uses it for backend logic (Go or Rust layer)
- `AyuGram4A` Android client uses it via JNI (Java/Kotlin layer)
- **No logic is duplicated** across languages — C is the source of truth

---

## 6. Migration Roadmap

### Phase 0 — Now (Done)
- [x] C models: ZsysUser, ZsysChat, ZsysClientConfig, ZsysKV
- [x] Python ctypes bindings
- [x] zsys i18n C engine
- [x] zsys module system (Python)

### Phase 1 — Near-term (~weeks)
- [ ] IskraTeam adds `zsys` as optional dependency
- [ ] `iskra_userbot` uses `zsys.i18n` for responses
- [ ] Add `to_zsys()` / `from_zsys()` on Iskra ORM models
- [ ] `zsys_wallet.h` stub (for IskraTeam wallet concepts)

### Phase 2 — Medium-term (~months)
- [ ] Unified module context API in zsys (works for Telegram AND Iskra)
- [ ] `zsys.transport.wss` production-ready (port from Iskra SDK)
- [ ] `ZsysMessage` C struct (currently missing from zsys)
- [ ] zsys_rpc.h — JSON-RPC 2.0 routing in C

### Phase 3 — Long-term (~quarters)
- [ ] `zsys_crypto.c` — libsodium-backed E2E crypto in C
- [ ] `iskra_api` backend ported to Go using zsys CGo bindings
- [ ] AyuGram4A JNI bridge to `libzsys_core.so`
- [ ] `zxc_userbot` partially ported to Go (keepng Python for modules)

### Phase 4 — Theoretical end-state
- [ ] All platform logic in Go or Rust, using C core
- [ ] Python becomes: scripting / module authoring / prototyping layer
- [ ] Single `libzsys_core.so` ships with: Telegram bot, Iskra server, Android client

---

## 7. Practical First Steps (What to do right now)

If you want to start the integration today, minimal effort maximum value:

```python
# 1. In IskraTeam — install zsys
#    pip install -e /path/to/zsys

# 2. In iskra_api/main.py — replace hardcoded strings with zsys i18n
from zsys.i18n import I18n
i18n = I18n()
i18n.load_json("locales/ru.json")

# 3. In iskra_userbot — use zsys text formatting
from zsys.utils.text import escape_html
from zsys._core import zsys_format_bold

# 4. In iskra SDK — add to_zsys() on User type
from zsys._ctypes import User as ZsysUser
class User(BaseModel):
    def to_zsys(self) -> ZsysUser:
        u = ZsysUser()
        u.id = self.id
        u.username = self.username
        return u
```

Total time to step 4: ~2 hours. Zero architectural changes required.

---

## 8. Risks & Considerations

| Risk | Mitigation |
|------|-----------|
| zsys becomes a hard dep of IskraTeam | Keep as optional dep; pure Python fallback always available |
| C ABI breaks between versions | Semantic versioning on `zsys_core.h`; never remove symbols, only add |
| Performance overhead of ctypes | Use CPython extension for hot paths; ctypes only for data model layer |
| AyuGram4A JNI complexity | That's a separate project; use JNA instead of JNI for simplicity |
| Over-engineering | Do Phase 1 first; don't build Phase 3 until Phase 1 proves its value |

---

*This document is a theoretical future vision — nothing here is implemented
unless explicitly marked as Done. The goal is to avoid duplicated work and
move toward a unified system core over time.*
