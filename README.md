### Dependencies
Python 3.8 or newer is required, and should be present in your system PATH
environment variable.

Generating and building D3D12 and OpenGL programs requires clang to be
installed and present in PATH as well.

To run tests, you will also need the python modules mypy and pytest, which can be
installed via pip.

The OpenGL backend additionally requires glad to be installed separately.  Glad
is available in pip.

### Installation
```
git clone git@github.com:Aeva/dream_machine.git
cd dream_machine
git submodule init
git submodule update
python setup.py develop --user
```

### Usage
Modify `example.data` to specify your program, and then run `build.bat`.  This will
generate `generated.cpp` and then it will compile your program to produce
`generated.exe`.

Shaders go in the `shaders` directory.  Additional behavioral hooks can be customized
via `user_code.cpp`.
