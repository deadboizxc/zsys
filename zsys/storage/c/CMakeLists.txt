cmake_minimum_required(VERSION 3.14)
project(zsys_storage VERSION 1.0.0 LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -O3)
endif()

add_library(zsys_storage SHARED src/zsys_storage.c)
target_include_directories(zsys_storage PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>)
set_target_properties(zsys_storage PROPERTIES
    VERSION 1.0.0 SOVERSION 1)

add_library(zsys_storage_static STATIC src/zsys_storage.c)
target_include_directories(zsys_storage_static PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>)
set_target_properties(zsys_storage_static PROPERTIES OUTPUT_NAME "zsys_storage")

include(GNUInstallDirs)
install(TARGETS zsys_storage zsys_storage_static
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR})
install(FILES include/zsys_storage.h
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/zsys)
