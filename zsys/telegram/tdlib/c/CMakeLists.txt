cmake_minimum_required(VERSION 3.14)

project(libtg
    VERSION 0.1.0
    DESCRIPTION "High-level Telegram C API built on TDLib"
    LANGUAGES C
)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -O2)
endif()

# ── TDLib ────────────────────────────────────────────────────────────────────
find_library(TDJSON_LIB NAMES tdjson tdjson_static
    HINTS /usr/local/lib /usr/lib $ENV{TDLIB_DIR}/lib)

if(NOT TDJSON_LIB)
    message(FATAL_ERROR
        "TDLib not found.\n"
        "Install TDLib or set: cmake -DTDLIB_DIR=/path/to/tdlib .")
endif()
message(STATUS "libtg: TDLib found at ${TDJSON_LIB}")

# ── sources ──────────────────────────────────────────────────────────────────
set(TG_SOURCES
    src/tg_client.c
    src/tg_auth.c
    src/tg_dispatch.c
    src/tg_message.c
)

# ── shared ───────────────────────────────────────────────────────────────────
add_library(tg SHARED ${TG_SOURCES})
target_include_directories(tg
    PUBLIC  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/src
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
