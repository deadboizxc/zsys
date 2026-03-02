cmake_minimum_required(VERSION 3.14)
project(zsys_core VERSION 1.0.0 LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -O3)
endif()

set(SOURCES
    src/zsys_core.c
    src/zsys_user.c
    src/zsys_chat.c
    src/zsys_client.c
)
set(HEADERS
    include/zsys_core.h
    include/zsys_user.h
    include/zsys_chat.h
    include/zsys_client.h
)

add_library(zsys_core SHARED ${SOURCES})
target_include_directories(zsys_core PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>)
set_target_properties(zsys_core PROPERTIES
    VERSION ${PROJECT_VERSION} SOVERSION 1 PUBLIC_HEADER "${HEADERS}")

add_library(zsys_core_static STATIC ${SOURCES})
target_include_directories(zsys_core_static PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>)
set_target_properties(zsys_core_static PROPERTIES OUTPUT_NAME "zsys_core")

include(GNUInstallDirs)
install(TARGETS zsys_core zsys_core_static
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    PUBLIC_HEADER DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/zsys)
