
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


class InitGL(SyntaxExpander):
    template = """
	SDL_GL_LoadLibrary(nullptr);
	SDL_GL_SetAttribute(SDL_GL_ACCELERATED_VISUAL, 1);
	SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 「hint_version_major」);
	SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 「hint_version_minor」);
	SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_CORE);
#if DEBUG_BUILD
	SDL_GL_SetAttribute(SDL_GL_CONTEXT_FLAGS, SDL_GL_CONTEXT_DEBUG_FLAG);
#endif // DEBUG_BUILD
""".strip()

    def __init__(self, major, minor):
        SyntaxExpander.__init__(self, hint_version_major = major, hint_version_minor = minor)


AFTER_SDL_CREATE_WINDOW = """
	GLContext = SDL_GL_CreateContext(Window);
	if(!GLContext)
	{
		std::cout << "Fatal Error: SDL failed to create an OpenGL context: " << SDL_GetError() << std::endl;
		SDL_DestroyWindow(Window);
		SDL_Quit();
		return 1;
	}

	if (!gladLoadGLLoader((GLADloadproc)SDL_GL_GetProcAddress))
	{
		std::cout << "Failed to initialize GLAD!" << std::endl;
		SDL_GL_DeleteContext(GLContext);
		SDL_DestroyWindow(Window);
		SDL_Quit();
		return 1;
	}
	else
	{
		std::cout << "Found OpenGL version " << GLVersion.major << "." << GLVersion.minor << std::endl << std::endl;
	}

#if DEBUG_BUILD
	if (GLAD_GL_ARB_debug_output)
	{
		GLint ContextFlags;
		glGetIntegerv(GL_CONTEXT_FLAGS, &ContextFlags);
		if (ContextFlags & GL_CONTEXT_FLAG_DEBUG_BIT)
		{
			glEnable(GL_DEBUG_OUTPUT);
			glEnable(GL_DEBUG_OUTPUT_SYNCHRONOUS);
			glDebugMessageCallbackARB(&DebugCallback, nullptr);
			glDebugMessageControlARB(GL_DONT_CARE, GL_DONT_CARE, GL_DONT_CARE, 0, nullptr, GL_TRUE);
		}
		else
		{
			std::cout << "Debug context not available!" << std::endl;
		}
	}
	else
	{
		std::cout << "Debug output extension not available!" << std::endl;
	}
#endif
""".strip()


class GeneratedMain(SyntaxExpander):
    template = external("cpp_templates/dream_machine.cpp")
    indent = ("initial_setup_hook", "resize_hook", "draw_frame_hook", "renderers", "upload_type_handlers", "uploader_definitions")

    def __init__(self, *args, **kargs):
        SyntaxExpander.__init__(self, *args, **kargs)
        self.structs_namespace = "Glsl"
        self.sdl_window_flags = " | SDL_WINDOW_OPENGL"
        self.after_sdl_window = AFTER_SDL_CREATE_WINDOW
        self.set_viewport = "glViewport(0, 0, ScreenWidth, ScreenHeight);"
        self.present = "SDL_GL_SwapWindow(Window);"


class GeneratedHeader(SyntaxExpander):
    template = external("cpp_templates/dream_machine.h")
    indent = ("struct_declarations", "user_var_declarations", "uploader_declarations")

    def __init__(self, dependencies, *args, **kargs):
        SyntaxExpander.__init__(self, *args, **kargs)
        self.structs_namespace = "Glsl"
        self.include_before_sdl = '#include "glad.h"'
        self.include_after_sdl = []
        for header in dependencies:
            self.include_after_sdl.append(f'#include "{header}.h"')
