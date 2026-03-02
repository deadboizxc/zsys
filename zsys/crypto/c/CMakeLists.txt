cmake_minimum_required(VERSION 3.15)
project(zsys_crypto VERSION 1.0.0 LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -O2)
endif()

find_package(OpenSSL REQUIRED)

add_library(zsys_crypto SHARED src/zsys_crypto.c)
target_include_directories(zsys_crypto PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>)
target_link_libraries(zsys_crypto OpenSSL::SSL OpenSSL::Crypto)

add_library(zsys_crypto_static STATIC src/zsys_crypto.c)
target_include_directories(zsys_crypto_static PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>)
target_link_libraries(zsys_crypto_static OpenSSL::SSL OpenSSL::Crypto)
set_target_properties(zsys_crypto_static PROPERTIES OUTPUT_NAME "zsys_crypto")

include(GNUInstallDirs)
install(TARGETS zsys_crypto zsys_crypto_static
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR})
install(FILES include/zsys_crypto.h DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})
