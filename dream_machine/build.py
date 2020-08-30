
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


def find_glad() -> bool:
    if os.path.isdir("glad"):
        exists = True
        for file in "glad.c", "glad.h", "khrplatform.h":
            if not os.path.isfile(os.path.join("glad", file)):
                exists = False
                break
        return exists
    else:
        return False


def extract_extensions_from_glad():
    with open(os.path.join("glad", "glad.c"), "r") as glad:
        match = re.search(r'--extensions="(?P<extensions>[A-Za-z0-9_, ]+)"', glad.read())
        if match:
            return sorted([e.strip() for e in match["extensions"].split(',')])


def download_glad(extensions, debug):
    params = {
        "out-path" : "glad",
        "profile" : "core",
        "api" : "gl=4.2",
        "generator" : "c-debug" if debug else "c",
        "spec" : "gl",
        "extensions" : f"{','.join(extensions)}",
    }
    glad = ["python", "-m glad", "--local-files", "--no-loader"] + [f" --{n}={v}" for (n,v) in params.items()]
    subprocess.call(" ".join(glad), shell=True)
    if not find_glad():
        raise FileNotFoundError("Can't find glad.")


def build(user_sources, extra_sources, backend, out_path=None, copy_dlls=True, debug=False):
    cc = find_exe("clang++")
    dependencies_dir = os.path.join(os.path.dirname(__file__), "dependencies")
    defines = ["GLFW_DLL", "WIN32_LEAN_AND_MEAN", "DEBUG_BUILD"]
    includes = glob(os.path.join(dependencies_dir, "**", "include"))
    includes += [os.path.dirname(__file__)]
    libs = [os.path.join(dependencies_dir, "SDL2-2.0.12", "lib", "x64")]
    sources = list(user_sources)
    sources += glob(os.path.join(dependencies_dir, "**", "src", "*.cpp"))
    sources += glob(os.path.join(dependencies_dir, "**", "src", "*.c"))
    for named in extra_sources:
        sources.append(os.path.join(os.path.dirname(__file__), f"{named}.cpp"))
    dlls = ["SDL2.dll"]

    if backend == "OpenGL":
        extensions = \
        sorted([
            "GL_ARB_buffer_storage",
            "GL_ARB_clear_texture",
            "GL_ARB_clip_control",
            "GL_ARB_compute_shader",
            "GL_ARB_debug_output",
            "GL_ARB_direct_state_access",
            "GL_ARB_gpu_shader5",
            "GL_ARB_program_interface_query",
            "GL_ARB_shader_image_load_store",
            "GL_ARB_shader_storage_buffer_object",
            "GL_KHR_debug",
            "GL_NV_mesh_shader",
        ])
        if not find_glad():
            download_glad(extensions, debug)
        else:
            found = extract_extensions_from_glad()
            if set(found) != set(extensions):
                download_glad(extensions, debug)

        includes.append("glad")
        sources.append(os.path.join("glad", "glad.c"))

    args = [cc]
    if debug:
        args += ["-O0", "-g", "-gcodeview", "-DDEBUG_BUILD"]
    args += [f"-D{p}" for p in defines]
    args += [f"-I{p}" for p in includes]
    args += [f"-L{p}" for p in libs]
    args += ["-lSDL2", "-lSDL2main", "-lopengl32"]
    args += sources
    if out_path:
        args += [f"-o{out_path}"]

    print(" ".join(args))
    print(subprocess.run(args, check=True))

    if copy_dlls:
        for path in libs:
            for dll in dlls:
                src = os.path.join(path, dll)
                if os.path.isfile(src):
                    dst = os.path.join(os.getcwd(), dll)
                    if not os.path.isfile(dst):
                        shutil.copyfile(src, dst)
