
# Copyright 2020 Aeva Palecek
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
import re
import sys
import shutil
import subprocess
from glob import glob


def find_exe(name):
    splitter = ":"
    if sys.platform == "win32":
        name += ".exe"
        splitter=";"
    for env_path in os.environ["PATH"].split(splitter):
        path = os.path.join(env_path, name)
        if os.path.isfile(path):
            return path
    raise RuntimeError(f"Can't find {name}.  Is it in your PATH env var?")


def clang(user_sources, extra_sources, extra_include_paths, libraries, defines, out_path=None, copy_dlls=True, debug=False):
    cc = find_exe("clang++")
    dependencies_dir = os.path.join(os.path.dirname(__file__), "dependencies")

    libraries = ["SDL2", "SDL2main"] + libraries
    defines = ["WIN32_LEAN_AND_MEAN"] + defines

    library_paths = [os.path.join(dependencies_dir, "SDL2-2.0.12", "lib", "x64")]
    include_paths = glob(os.path.join(dependencies_dir, "**", "include"))
    include_paths += [os.path.dirname(__file__)]
    include_paths += extra_include_paths

    sources = list(user_sources)
    sources += glob(os.path.join(dependencies_dir, "**", "src", "*.cpp"))
    sources += glob(os.path.join(dependencies_dir, "**", "src", "*.c"))
    for named in extra_sources:
        sources.append(os.path.join(os.path.dirname(__file__), f"{named}.cpp"))

    dlls = ["SDL2.dll"]

    args = [cc]
    if debug:
        args += ["-O0", "-g", "-gcodeview", "-DDEBUG_BUILD"]
    args += [f"-D{p}" for p in defines]
    args += [f"-I{p}" for p in include_paths]
    args += [f"-L{p}" for p in library_paths]
    args += [f"-l{p}" for p in libraries]
    args += sources
    if out_path:
        args += [f"-o{out_path}"]

    print(" ".join(args))
    print(subprocess.run(args, check=True))

    if copy_dlls:
        for path in library_paths:
            for dll in dlls:
                src = os.path.join(path, dll)
                if os.path.isfile(src):
                    dst = os.path.join(os.getcwd(), dll)
                    if not os.path.isfile(dst):
                        shutil.copyfile(src, dst)

