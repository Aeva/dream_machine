
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
from base64 import b64encode
from hashlib import md5
from ..handy import *
from ..opengl.glsl_types import *
from ..expanders import SyntaxExpander, external


class ShaderSource(SyntaxExpander):
    template = '"「name」" : atob("「encoded」"),'

    def __init__(self, name, source):
        SyntaxExpander.__init__(self)
        self.name = name
        self.encoded = b64encode(source.encode()).decode().strip()
