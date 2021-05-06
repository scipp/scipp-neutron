#!/bin/bash

set -ex

mkdir -p 'build' && cd 'build'

if test -z "${OSX_VERSION}"
then
  IPO="ON"
else
  # Disable IPO for OSX due to unexplained linker failure.
  IPO="OFF"
fi

# Perform CMake configuration
cmake \
  -G Ninja \
  -DPYTHON_EXECUTABLE="${CONDA_PREFIX}/bin/python" \
  -DCMAKE_INSTALL_PREFIX="$INSTALL_PREFIX" \
  -DCMAKE_OSX_DEPLOYMENT_TARGET=$OSX_VERSION \
  -DCMAKE_OSX_SYSROOT="/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX$OSX_VERSION.sdk" \
  -DWITH_CTEST=OFF \
  -DCMAKE_INTERPROCEDURAL_OPTIMIZATION=$IPO \
  ..

# Show cmake settings
cmake -B . -S .. -LA

# Build benchmarks, C++ tests and install Python package
ninja -v all-benchmarks all-tests install

# Run C++ tests
./bin/scippneutron-test
