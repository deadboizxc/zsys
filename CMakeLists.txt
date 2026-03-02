cmake_minimum_required(VERSION 3.14)

project(zsys
    VERSION 1.0.0
    DESCRIPTION "zsys C modules"
    LANGUAGES C
)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

option(ZSYS_BUILD_TESTS  "Build test suite"  OFF)
option(ZSYS_BUILD_ALL    "Build all modules" ON)

if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic -O3)
    if(NOT CMAKE_BUILD_TYPE STREQUAL "Debug")
        add_compile_options(-march=native)
    endif()
endif()

# ── modules (each is independent, builds its own .so) ───────────────────────
# Shared include path used by modules that depend on zsys_core headers
set(ZSYS_CORE_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/zsys/core/c/include")

add_subdirectory(zsys/core/c)
add_subdirectory(zsys/modules/c)
add_subdirectory(zsys/i18n/c)
add_subdirectory(zsys/storage/c)

# ── libtg (Telegram / TDLib) — only if TDLib is available ───────────────────
find_library(TDJSON_LIB NAMES tdjson tdjson_static
    HINTS /usr/local/lib /usr/lib $ENV{TDLIB_DIR}/lib)
if(TDJSON_LIB)
    add_subdirectory(zsys/telegram/tdlib/c)
else()
    message(STATUS "TDLib not found — skipping libtg. "
                   "(set TDLIB_DIR to enable)")
endif()

# ── tests ────────────────────────────────────────────────────────────────────
if(ZSYS_BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests/c)
endif()

# ── summary ──────────────────────────────────────────────────────────────────
message(STATUS "zsys v${PROJECT_VERSION} — modules:")
message(STATUS "  core     → zsys/core/c/")
message(STATUS "  modules  → zsys/modules/c/")
message(STATUS "  i18n     → zsys/i18n/c/")
message(STATUS "  storage  → zsys/storage/c/")
if(TDJSON_LIB)
message(STATUS "  telegram → zsys/telegram/tdlib/c/")
endif()
