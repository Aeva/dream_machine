# Dependencies
You will need python 3.6 or newer and clang installed on your system.  These should
alos be added to the PATH environment variable.

To run tests, you will also need the python modules mypy and pytest, which can be
installed via pip.

# Usage
Modify `example.data` to specify your program, and then run `build.bat`.  This will
generate `generated.cpp` and then it will compile your program to produce
`generated.exe`.

Shaders go in the `shaders` directory.  Additional behavioral hooks can be customized
via `user_code.cpp`.
