
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


class D3D12Setup(SyntaxExpander):
    template = external("d3d12/bootstrap.cpp")

    def __init__(self, *args, **kargs):
        SyntaxExpander.__init__(self, *args, **kargs)
        self.rtv_heap_size = 2


class GeneratedMain(SyntaxExpander):
    template = external("cpp_templates/dream_machine.cpp")
    indent = ("initial_setup_hook", "resize_hook", "draw_frame_hook", "renderers", "struct_definitions", "uploader_definitions")

    def __init__(self, *args, **kargs):
        SyntaxExpander.__init__(self, *args, **kargs)
        self.structs_namespace = "HLSL"
        self.sdl_window_flags = ""
        self.after_sdl_window = D3D12Setup()
        self.set_viewport = ""
        self.present = 'RETURN_ON_FAIL("Present", SwapChain->Present(1, 0))'


class GeneratedHeader(SyntaxExpander):
    template = external("cpp_templates/dream_machine.h")
    indent = ("struct_declarations", "user_var_declarations", "uploader_declarations")

    def __init__(self, dependencies, *args, **kargs):
        SyntaxExpander.__init__(self, *args, **kargs)
        self.structs_namespace = "HLSL"
        self.include_before_sdl = \
        [
            '#include <windows.h>',
            '#include <winuser.h>',
            '#include <wrl.h>',
            '#include <d3d12.h>',
            '#include <dxgi1_4.h>',
            '#include <stdexcept>',
        ]
        self.include_after_sdl = \
        [
            "using Microsoft::WRL::ComPtr;",
        ]
        for header in dependencies:
            self.include_after_sdl.append(f'#include "{header}.h"')
