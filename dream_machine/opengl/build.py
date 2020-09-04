
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


from ..build_common import *
from .solver import solve
from .validate import validate


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


def build(user_sources, dependencies, extensions, out_path=None, copy_dlls=True, debug=False):
    if not find_glad():
        download_glad(extensions, debug)
    else:
        found = extract_extensions_from_glad()
        if set(found) != set(extensions):
            download_glad(extensions, debug)

    sources = user_sources + [os.path.join("glad", "glad.c")]
    includes = ["glad"]
    libraries = ["opengl32"]
    defines = []

    clang(sources, dependencies, includes, libraries, defines, out_path, copy_dlls, debug)
