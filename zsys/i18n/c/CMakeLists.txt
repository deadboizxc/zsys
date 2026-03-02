cmake_minimum_required(VERSION 3.14)
project(zsys_i18n VERSION 1.0.0 LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -O3)
endif()

if(NOT ZSYS_CORE_INCLUDE_DIR)
    set(ZSYS_CORE_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../core/c/include")
endif()

add_library(zsys_i18n SHARED src/zsys_i18n.c)
target_include_directories(zsys_i18n PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/src>
    ${ZSYS_CORE_INCLUDE_DIR})

add_library(zsys_i18n_static STATIC src/zsys_i18n.c)
target_include_directories(zsys_i18n_static PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/src>
    ${ZSYS_CORE_INCLUDE_DIR})
set_target_properties(zsys_i18n_static PROPERTIES OUTPUT_NAME "zsys_i18n")

include(GNUInstallDirs)
install(TARGETS zsys_i18n zsys_i18n_static
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR})
