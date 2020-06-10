
import os
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


def build(source_path, out_path=None, copy_dlls=True):
    cc = find_exe("clang++")
    defines = ["GLFW_DLL", "WIN32_LEAN_AND_MEAN", "DEBUG_BUILD"]
    includes = glob(os.path.join(os.path.dirname(__file__), "**", "include"))
    libs = glob(os.path.join(os.path.dirname(__file__), "**", "lib"))
    sources = [source_path]
    sources += glob(os.path.join(os.path.dirname(__file__), "**", "src", "*.cpp"))
    sources += glob(os.path.join(os.path.dirname(__file__), "**", "src", "*.c"))
    dlls = ["glfw3.dll"]

    args = [cc]
    args += [f"-D{p}" for p in defines]
    args += [f"-I{p}" for p in includes]
    args += [f"-L{p}" for p in libs]
    args += ["-lglfw3dll", "-lopengl32"]
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
