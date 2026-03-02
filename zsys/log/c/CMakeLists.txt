cmake_minimum_required(VERSION 3.14)
project(zsys_log VERSION 1.0.0 LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -O3)
endif()

add_library(zsys_log SHARED src/zsys_log.c)
target_include_directories(zsys_log PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>)

add_library(zsys_log_static STATIC src/zsys_log.c)
target_include_directories(zsys_log_static PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>)
set_target_properties(zsys_log_static PROPERTIES OUTPUT_NAME "zsys_log")

include(GNUInstallDirs)
install(TARGETS zsys_log zsys_log_static
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR})
install(FILES include/zsys_log.h
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})
