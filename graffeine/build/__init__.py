
import os
import sys
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


def build(source_path, out_path="a.out"):
    cc = find_exe("clang++")
    includes = glob(os.path.join(os.path.dirname(__file__), "**", "include"))
    libs = glob(os.path.join(os.path.dirname(__file__), "**", "lib"))
    sources = [source_path]
    sources += glob(os.path.join(os.path.dirname(__file__), "**", "src", "*.cpp"))
    sources += glob(os.path.join(os.path.dirname(__file__), "**", "src", "*.c"))

    args = [cc]
    args += [f"-I{p}" for p in includes]
    args += [f"-L{p}" for p in libs]
    args += ["-lglfw3", "-lopengl32"]
    args += sources

    print(" ".join(args))
    print(subprocess.run(args, check=True))
