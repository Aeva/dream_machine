
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


from ..expanders import SyntaxExpander, external


class GeneratedMain(SyntaxExpander):
    template = external("cpp_templates/dream_machine.cpp")
    indent = ("initial_setup_hook", "resize_hook", "draw_frame_hook", "renderers", "struct_definitions", "uploader_definitions")

    def __init__(self, *args, **kargs):
        SyntaxExpander.__init__(self, *args, **kargs)
        self.structs_namespace = "GNDN"
        self.sdl_window_flags = ""
        self.after_sdl_window = ""
        self.set_viewport = ""
        self.present = ""


class GeneratedHeader(SyntaxExpander):
    template = external("cpp_templates/dream_machine.h")
    indent = ("struct_declarations", "user_var_declarations", "uploader_declarations")

    def __init__(self, dependencies, *args, **kargs):
        SyntaxExpander.__init__(self, *args, **kargs)
        self.structs_namespace = "GNDN"
        self.include_before_sdl = ''
        self.include_after_sdl = []
        for header in dependencies:
            self.include_after_sdl.append(f'#include "{header}.h"')
