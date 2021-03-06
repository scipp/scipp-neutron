mkdir build
cd build

echo building in %cd%
cmake -G"Visual Studio 16 2019" -A x64 -DCMAKE_CXX_STANDARD=20 -DCMAKE_INSTALL_PREFIX=%CONDA_PREFIX% -DPYTHON_EXECUTABLE=%CONDA_PREFIX%\python -DWITH_CXX_TEST=OFF ..

:: Show cmake settings
cmake -B . -S .. -LA

:: Benchmarks
cmake --build . --target all-benchmarks --config Release || echo ERROR && exit /b

:: C++ tests
cmake --build . --target all-tests --config Release || echo ERROR && exit /b
bin\Release\scippneutron-test.exe || echo ERROR && exit /b

::  Build, install and move scipp Python library to site packages location
cmake --build . --target install --config Release || echo ERROR && exit /b
move %CONDA_PREFIX%\scippneutron %CONDA_PREFIX%\lib\
