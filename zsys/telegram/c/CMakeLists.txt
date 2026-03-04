cmake_minimum_required(VERSION 3.14)

project(libtg
    VERSION 0.1.0
    DESCRIPTION "High-level Telegram C API built on TDLib"
    LANGUAGES C CXX
)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -O2)
endif()

# ── TDLib: system first, FetchContent fallback ───────────────────────────────
option(TDLIB_FETCH "Download and build TDLib via FetchContent if not found" ON)

find_library(TDJSON_LIB NAMES tdjson tdjson_static
    HINTS
        /usr/local/lib
        /usr/lib
        $ENV{TDLIB_DIR}/lib
        ${CMAKE_CURRENT_SOURCE_DIR}/tdlib/lib
)
find_path(TDJSON_INCLUDE td/telegram/td_json_client.h
    HINTS
        /usr/local/include
        /usr/include
        $ENV{TDLIB_DIR}/include
        ${CMAKE_CURRENT_SOURCE_DIR}/tdlib/include
)

if(TDJSON_LIB AND TDJSON_INCLUDE)
    message(STATUS "libtg: TDLib found at ${TDJSON_LIB}")
elseif(TDLIB_FETCH)
    message(STATUS "libtg: TDLib not found — fetching from GitHub (this will take a while)...")
    include(FetchContent)
    FetchContent_Declare(td
        GIT_REPOSITORY https://github.com/tdlib/td.git
        GIT_TAG        v1.8.29
        GIT_SHALLOW    TRUE
    )
    # Build only tdjson target, disable tests/docs
    set(TD_ENABLE_JNI          OFF CACHE BOOL "" FORCE)
    set(BUILD_SHARED_LIBS_SAVE ${BUILD_SHARED_LIBS})
    set(BUILD_SHARED_LIBS      OFF CACHE BOOL "" FORCE)
    FetchContent_MakeAvailable(td)
    set(BUILD_SHARED_LIBS ${BUILD_SHARED_LIBS_SAVE})

    set(TDJSON_LIB     tdjson_static)
    set(TDJSON_INCLUDE ${td_SOURCE_DIR})
    message(STATUS "libtg: TDLib built via FetchContent")
else()
    message(FATAL_ERROR
        "TDLib not found.\n"
        "Options:\n"
        "  1. Run:  make build-tdlib   (builds TDLib from source into ./tdlib/)\n"
        "  2. Set:  cmake -DTDLIB_DIR=/path/to/tdlib .\n"
        "  3. Set:  cmake -DTDLIB_FETCH=ON .  (downloads automatically)\n"
    )
endif()
message(STATUS "libtg: TDLib include: ${TDJSON_INCLUDE}")

# ── sources ──────────────────────────────────────────────────────────────────
set(TG_SOURCES
    src/tg_client.c
    src/tg_auth.c
    src/tg_dispatch.c
    src/tg_message.c
    src/tg_chat.c
    src/tg_user.c
    src/tg_admin.c
    src/tg_media.c
    src/tg_account.c
    src/tg_bot.c
)

# ── shared ───────────────────────────────────────────────────────────────────
add_library(tg SHARED ${TG_SOURCES})
target_include_directories(tg
    PUBLIC  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/src
            ${TDJSON_INCLUDE}
)
target_link_libraries(tg PRIVATE ${TDJSON_LIB} pthread)
set_target_properties(tg PROPERTIES
    VERSION   ${PROJECT_VERSION}
    SOVERSION 0
    OUTPUT_NAME "tg"
)

# ── static ───────────────────────────────────────────────────────────────────
add_library(tg_static STATIC ${TG_SOURCES})
target_include_directories(tg_static
    PUBLIC  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/src
            ${TDJSON_INCLUDE}
)
target_link_libraries(tg_static PRIVATE ${TDJSON_LIB} pthread)
set_target_properties(tg_static PROPERTIES OUTPUT_NAME "tg")

# ── install ───────────────────────────────────────────────────────────────────
include(GNUInstallDirs)
install(TARGETS tg tg_static
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
)
install(FILES include/tg.h
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
)

message(STATUS "libtg v${PROJECT_VERSION} configured")
message(STATUS "  Build:  cmake --build . --target tg")
message(STATUS "  Output: libtg.so + libtg.a")
