cmake_minimum_required(VERSION 2.8.12)
project(PackageTest CXX)

include(${CMAKE_BINARY_DIR}/conan_paths.cmake)
find_package(Gperftools REQUIRED)

add_executable(example example.cpp)
target_link_libraries(example gperftools::tcmalloc)
