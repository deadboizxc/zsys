cmake_minimum_required(VERSION 3.14)
project(zsys_modules VERSION 1.0.0 LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -O3)
endif()

# zsys_router + zsys_registry depend on zsys_core headers
find_package(zsys_core QUIET)
if(NOT zsys_core_FOUND)
    # fallback: expect ZSYS_CORE_INCLUDE_DIR to be set
    if(NOT ZSYS_CORE_INCLUDE_DIR)
        set(ZSYS_CORE_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../core/c/include")
    endif()
endif()

set(SOURCES
    src/zsys_router.c
    src/zsys_registry.c
)

add_library(zsys_modules SHARED ${SOURCES})
target_include_directories(zsys_modules PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/src>
    ${ZSYS_CORE_INCLUDE_DIR})

add_library(zsys_modules_static STATIC ${SOURCES})
target_include_directories(zsys_modules_static PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/src>
    ${ZSYS_CORE_INCLUDE_DIR})
set_target_properties(zsys_modules_static PROPERTIES OUTPUT_NAME "zsys_modules")

include(GNUInstallDirs)
install(TARGETS zsys_modules zsys_modules_static
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR})
