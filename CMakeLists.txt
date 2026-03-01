cmake_minimum_required(VERSION 3.14)

project(zsys_core
    VERSION 1.0.0
    DESCRIPTION "zsys pure C core library"
    LANGUAGES C
)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

# Build options
option(BUILD_SHARED_LIBS  "Build shared library"        ON)
option(ZSYS_BUILD_TESTS   "Build test suite"            OFF)
option(ZSYS_INSTALL       "Generate install targets"    ON)

# Compile flags
if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic -O3)
    if(NOT CMAKE_BUILD_TYPE STREQUAL "Debug")
        add_compile_options(-march=native)
    endif()
endif()

# Source files
set(ZSYS_SOURCES
    zsys/src/zsys_core.c
)
set(ZSYS_HEADERS
    zsys/include/zsys_core.h
)

# ── Shared library: libzsys_core.so ─────────────────────────────────────────
add_library(zsys_core SHARED ${ZSYS_SOURCES})
target_include_directories(zsys_core
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/zsys/include>
        $<INSTALL_INTERFACE:include>
)
set_target_properties(zsys_core PROPERTIES
    VERSION   ${PROJECT_VERSION}
    SOVERSION ${PROJECT_VERSION_MAJOR}
    PUBLIC_HEADER "${ZSYS_HEADERS}"
    OUTPUT_NAME "zsys_core"
)
target_compile_definitions(zsys_core PRIVATE ZSYS_BUILDING_DLL)

# ── Static library: libzsys_core.a ──────────────────────────────────────────
add_library(zsys_core_static STATIC ${ZSYS_SOURCES})
target_include_directories(zsys_core_static
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/zsys/include>
        $<INSTALL_INTERFACE:include>
)
set_target_properties(zsys_core_static PROPERTIES
    OUTPUT_NAME "zsys_core"
)

# ── pkg-config ───────────────────────────────────────────────────────────────
configure_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/cmake/zsys_core.pc.in"
    "${CMAKE_CURRENT_BINARY_DIR}/zsys_core.pc"
    @ONLY
)

# ── Tests ────────────────────────────────────────────────────────────────────
if(ZSYS_BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests/c)
endif()

# ── Install ──────────────────────────────────────────────────────────────────
if(ZSYS_INSTALL)
    include(GNUInstallDirs)

    install(TARGETS zsys_core zsys_core_static
        EXPORT zsys_coreTargets
        LIBRARY       DESTINATION ${CMAKE_INSTALL_LIBDIR}
        ARCHIVE       DESTINATION ${CMAKE_INSTALL_LIBDIR}
        PUBLIC_HEADER DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/zsys
    )
    install(FILES "${CMAKE_CURRENT_BINARY_DIR}/zsys_core.pc"
        DESTINATION ${CMAKE_INSTALL_LIBDIR}/pkgconfig
    )
    install(EXPORT zsys_coreTargets
        FILE         zsys_coreTargets.cmake
        NAMESPACE    zsys::
        DESTINATION  ${CMAKE_INSTALL_LIBDIR}/cmake/zsys_core
    )

    # CMake config file
    include(CMakePackageConfigHelpers)
    write_basic_package_version_file(
        "${CMAKE_CURRENT_BINARY_DIR}/zsys_coreConfigVersion.cmake"
        VERSION       ${PROJECT_VERSION}
        COMPATIBILITY SameMajorVersion
    )
    configure_package_config_file(
        "${CMAKE_CURRENT_SOURCE_DIR}/cmake/zsys_coreConfig.cmake.in"
        "${CMAKE_CURRENT_BINARY_DIR}/zsys_coreConfig.cmake"
        INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/zsys_core
    )
    install(FILES
        "${CMAKE_CURRENT_BINARY_DIR}/zsys_coreConfig.cmake"
        "${CMAKE_CURRENT_BINARY_DIR}/zsys_coreConfigVersion.cmake"
        DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/zsys_core
    )
endif()

# ── Summary ──────────────────────────────────────────────────────────────────
message(STATUS "zsys_core v${PROJECT_VERSION}")
message(STATUS "  Build type : ${CMAKE_BUILD_TYPE}")
message(STATUS "  Shared lib : $<TARGET_FILE:zsys_core>")
message(STATUS "  Headers    : ${CMAKE_INSTALL_INCLUDEDIR}/zsys/")
