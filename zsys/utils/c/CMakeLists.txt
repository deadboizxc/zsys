cmake_minimum_required(VERSION 3.14)
project(zsys_utils VERSION 1.0.0 LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -O3)
endif()

add_library(zsys_utils SHARED src/zsys_utils.c)
target_include_directories(zsys_utils PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>)
set_target_properties(zsys_utils PROPERTIES
    VERSION ${PROJECT_VERSION}
    SOVERSION 1
    PUBLIC_HEADER "include/zsys_utils.h")

add_library(zsys_utils_static STATIC src/zsys_utils.c)
target_include_directories(zsys_utils_static PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>)
set_target_properties(zsys_utils_static PROPERTIES OUTPUT_NAME "zsys_utils")

include(GNUInstallDirs)
install(TARGETS zsys_utils zsys_utils_static
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    PUBLIC_HEADER DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/zsys)
