cmake_minimum_required(VERSION 3.15)
project(glide_native LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# A shared library that Python loads via ctypes -- no engine headers required.
add_library(glide_native SHARED glide_solver.cpp)

if(MSVC)
  target_compile_options(glide_native PRIVATE /O2 /W4)
else()
  target_compile_options(glide_native PRIVATE -O3 -Wall -Wextra)
endif()

# Drop the platform "lib" prefix so the file is glide_native.(dll|so|dylib),
# which is what glide/native_solver.py looks for.
set_target_properties(glide_native PROPERTIES PREFIX "")

# Copy the built library next to the Python package (works for every
# generator/config, unlike output-dir juggling with MSVC's Release/ subfolder).
add_custom_command(TARGET glide_native POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E copy
          $<TARGET_FILE:glide_native>
          "${CMAKE_SOURCE_DIR}/../glide/")
