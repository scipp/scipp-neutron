# ~~~
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2021 Scipp contributors (https://github.com/scipp)
# ~~~
cmake_minimum_required(VERSION 3.16)
execute_process(
  COMMAND git describe --tag --abbrev=0
  WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
  OUTPUT_VARIABLE SCIPPNEUTRON_VERSION
  OUTPUT_STRIP_TRAILING_WHITESPACE
)
project(scippneutron VERSION ${SCIPPNEUTRON_VERSION})

if(NOT DEFINED CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif(NOT DEFINED CMAKE_CXX_STANDARD)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_program(CCACHE_FOUND ccache)
if(CCACHE_FOUND)
  set_property(GLOBAL PROPERTY RULE_LAUNCH_COMPILE ccache)
  set_property(GLOBAL PROPERTY RULE_LAUNCH_LINK ccache)
endif(CCACHE_FOUND)
if(MSVC)
  set(CLCACHE_PATH
      ""
      CACHE PATH "Path to installed clcache executable directory"
  )
  if(EXISTS ${CLCACHE_PATH})
    set(CMAKE_VS_GLOBALS "CLToolExe=clcache.exe" "CLToolPath=${CLCACHE_PATH}"
                         "TrackFileAccess=false"
    )
    message(STATUS "Will attempt to use clcache")
  else(EXISTS ${CLCACHE_PATH})
    message(STATUS "CLCACHE_PATH not specified. Not enabled.")
    unset(CMAKE_VS_GLOBALS) # Clear all vs globals
  endif(EXISTS ${CLCACHE_PATH})
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /constexpr:steps2000000")
endif(MSVC)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE
      "Release"
      CACHE
        STRING
        "Choose the type of build, options are: Debug Release RelWithDebInfo MinSizeRel."
        FORCE
  )
endif(NOT CMAKE_BUILD_TYPE)

set(CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake")

set(CMAKE_CXX_VISIBILITY_PRESET hidden)
set(CMAKE_VISIBILITY_INLINES_HIDDEN TRUE)

# MP : Parallel compile, add before any targets so all use it
add_compile_options($<$<CXX_COMPILER_ID:MSVC>:-MP>)

include(GTest)
include(GoogleBenchmark)
include(GenerateExportHeader)
include(IPO)
include(pybind11)
include(scipp-install)

find_package(scipp 0.6 REQUIRED)

if("${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}" VERSION_LESS "3.7")
  message(
    FATAL_ERROR
      "Python v3 interpreter must be greater than or equal to 3.7. Found ${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}"
  )
endif()

option(WITH_CTEST "Enable ctest integration of tests" ON)
option(DYNAMIC_LIB "Build shared libraries" ON)
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)

# Optimization flags
if(${CMAKE_CXX_COMPILER_ID} MATCHES "GNU")
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} --param inline-unit-growth=50")
endif()

# Get version from git-describe
execute_process(
  COMMAND git describe --tag
  WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
  RESULT_VARIABLE HAVE_GIT_VERSION_INFO
  OUTPUT_VARIABLE GIT_VERSION_INFO OUTPUT_STRIP_TRAILING_WHITESPACE
)
if(${HAVE_GIT_VERSION_INFO} EQUAL 0)
  message(STATUS "Got version from Git: ${GIT_VERSION_INFO}")
  add_definitions(-DSCIPPNEUTRON_VERSION="${GIT_VERSION_INFO}")
endif()

if(NOT WIN32)
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fno-omit-frame-pointer")
  add_compile_options(
    -Wall
    -Wextra
    -Wpedantic
    -Wunused
    -Wshadow
    -Winit-self
    -Wpointer-arith
    -Woverloaded-virtual
    -Wold-style-cast
    -Wcast-qual
    -Wcast-align
  )
  add_compile_options(
    $<$<COMPILE_LANGUAGE:CXX>:-Woverloaded-virtual>
    $<$<COMPILE_LANGUAGE:CXX>:-fno-operator-names>
  )
endif(NOT WIN32)
# This is currently causing to many warnings, reenable when appropriate.
# add_compile_options ( -Wconversion )

# permissive- : Std compliant parsing, warnings (W3) set by CMake defaults
add_compile_options($<$<CXX_COMPILER_ID:MSVC>:-permissive->)

enable_testing()

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${PROJECT_BINARY_DIR}/bin)

# Custom target for building tests. all excludes tests by default
add_custom_target(all-tests)

# Custom target for building documentation
if(NOT WIN32)
  add_custom_target(docs COMMAND ./docs_build.sh)
else()
  add_custom_target(docs COMMAND docs_build.bat)
endif()

configure_file(cmake/docs_build.bat.in docs_build.bat)
configure_file(cmake/docs_build.sh.in docs_build.sh)

include(GNUInstallDirs)
set(PYTHONDIR scippneutron)
set(INCLUDEDIR ${CMAKE_INSTALL_INCLUDEDIR})

set(EXPORT_NAME ${PROJECT_NAME}-targets)

if(NOT APPLE)
  set(CMAKE_INSTALL_RPATH $ORIGIN)
else()
  set(CMAKE_INSTALL_RPATH @loader_path)
endif()

add_subdirectory(benchmark)
add_subdirectory(neutron)
add_subdirectory(python)

if(DYNAMIC_LIB)
  install(
    EXPORT ${EXPORT_NAME}
    DESTINATION "lib/cmake/${PROJECT_NAME}"
    NAMESPACE ${PROJECT_NAME}::
  )
  include(CMakePackageConfigHelpers)
  configure_package_config_file(
    ${CMAKE_CURRENT_SOURCE_DIR}/cmake/${PROJECT_NAME}-config.cmake.in
    "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}-config.cmake"
    INSTALL_DESTINATION lib/cmake/${PROJECT_NAME}
  )
  write_basic_package_version_file(
    "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}-config-version.cmake"
    VERSION "${CMAKE_PROJECT_VERSION}"
    COMPATIBILITY SameMinorVersion # switch to SameMajorVersion after 1.0
                                   # release
  )
  install(
    FILES "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}-config.cmake"
          "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}-config-version.cmake"
    DESTINATION lib/cmake/${PROJECT_NAME}
  )
endif(DYNAMIC_LIB)
