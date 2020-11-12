#include <string>
#include <iostream>
#include "generated.h"


const char* WindowTitle = "Hello World!";
int ScreenWidth = 512;
int ScreenHeight = 512;
float ScreenScaleX = 1.0;
float ScreenScaleY = 1.0;
bool WindowIsDirty = true;
SDL_Window* Window;


WindowParams GetWindowInfo()
{
	WindowParams ScreenInfo = { ScreenWidth, ScreenHeight, 1.0, 1.0 };
	return ScreenInfo;
}


extern int CurrentRenderer = 0;
extern void UserSetupCallback(SDL_Window* Window);
extern void UserFrameCallback(unsigned int FrameIndex, double StartTime, double DeltaTime);


SDL_GLContext GLContext;
GLuint Shaders[3] = { 0 };
GLuint ShaderPrograms[2] = { 0 };
GLuint SamplerHandles[1] = { 0 };
GLuint TextureHandles[1] = { 0 };
GLuint FrameBufferHandles[2] = { 0 };
GLuint BufferHandles[1] = { 0 };


namespace UploadAction
{
	void WindowParamsType (GLuint Handle, Glsl::WindowParamsType& Data)
	{
		std::int32_t* Mapped = (std::int32_t*)glMapNamedBufferRange(Handle, 0, 48, GL_MAP_WRITE_BIT | GL_MAP_INVALIDATE_BUFFER_BIT);
		if (Mapped == nullptr)
		{
			std::cout << "Fatal error in function \"Upload::WindowParamsType\": glMapNamedBufferRange returned nullptr.\n";
			HaltAndCatchFire();
		}
		Reflow< vec4>(Mapped, 0, Data.WindowSize);
		Reflow< vec4>(Mapped, 4, Data.WindowScale);
		Reflow<float>(Mapped, 8, Data.ElapsedTime);
		glUnmapNamedBuffer(Handle);
	}
}


namespace Upload
{
	void WindowParams(Glsl::WindowParamsType& Data)
	{
		UploadAction::WindowParamsType(BufferHandles[0], Data);
	}
}


void UpdateWindowSize()
{
	int Width;
	int Height;
	SDL_GetWindowSize(Window, &Width, &Height);
	if (ScreenWidth != Width || ScreenHeight != Height)
	{
		std::cout << Height << "\n";
		ScreenWidth = Width;
		ScreenHeight = Height;
		WindowIsDirty = true;
	}
}


void InitialSetup()
{
	{
		GLuint vao;
		glGenVertexArrays(1, &vao);
		glBindVertexArray(vao);
	}
	{
		std::string ShaderSource = DecodeBase64("I3ZlcnNpb24gNDIwCiNleHRlbnNpb24gR0xfQVJCX2NvbXB1dGVfc2hhZGVyIDogcmVxdWlyZQojZXh0ZW5zaW9uIEdMX0FSQl9zaGFkZXJfaW1hZ2VfbG9hZF9zdG9yZSA6IHJlcXVpcmUKCi8qCglDb3B5cmlnaHQgMjAyMCBBZXZhIFBhbGVjZWsKCglMaWNlbnNlZCB1bmRlciB0aGUgQXBhY2hlIExpY2Vuc2UsIFZlcnNpb24gMi4wICh0aGUgIkxpY2Vuc2UiKTsKCXlvdSBtYXkgbm90IHVzZSB0aGlzIGZpbGUgZXhjZXB0IGluIGNvbXBsaWFuY2Ugd2l0aCB0aGUgTGljZW5zZS4KCVlvdSBtYXkgb2J0YWluIGEgY29weSBvZiB0aGUgTGljZW5zZSBhdAoKCQlodHRwOi8vd3d3LmFwYWNoZS5vcmcvbGljZW5zZXMvTElDRU5TRS0yLjAKCglVbmxlc3MgcmVxdWlyZWQgYnkgYXBwbGljYWJsZSBsYXcgb3IgYWdyZWVkIHRvIGluIHdyaXRpbmcsIHNvZnR3YXJlCglkaXN0cmlidXRlZCB1bmRlciB0aGUgTGljZW5zZSBpcyBkaXN0cmlidXRlZCBvbiBhbiAiQVMgSVMiIEJBU0lTLAoJV0lUSE9VVCBXQVJSQU5USUVTIE9SIENPTkRJVElPTlMgT0YgQU5ZIEtJTkQsIGVpdGhlciBleHByZXNzIG9yIGltcGxpZWQuCglTZWUgdGhlIExpY2Vuc2UgZm9yIHRoZSBzcGVjaWZpYyBsYW5ndWFnZSBnb3Zlcm5pbmcgcGVybWlzc2lvbnMgYW5kCglsaW1pdGF0aW9ucyB1bmRlciB0aGUgTGljZW5zZS4KKi8KCmxheW91dChzdGQxNDAsIGJpbmRpbmcgPSAwKQp1bmlmb3JtIFdpbmRvd1BhcmFtcwp7Cgl2ZWM0IFdpbmRvd1NpemU7Cgl2ZWM0IFdpbmRvd1NjYWxlOwoJZmxvYXQgRWxhcHNlZFRpbWU7Cn07CmxheW91dChyZ2JhMzJmLCBiaW5kaW5nID0gMCkKdW5pZm9ybSBpbWFnZTJEIFNvbWVSZXNvdXJjZTsKCmxheW91dChsb2NhbF9zaXplX3ggPSA4LCBsb2NhbF9zaXplX3kgPSA4LCBsb2NhbF9zaXplX3ogPSAxKSBpbjsKdm9pZCBtYWluKCkKewoJZmxvYXQgV2F2ZSA9IGZsb2F0KGdsX1dvcmtHcm91cElELnkgKiAxMjggKyBnbF9Xb3JrR3JvdXBJRC54KSAvIDE2Mzg0LjA7Cgl2ZWM0IEJvcmluZ0RhdGEgPSB2ZWM0KFdhdmUsIHZlYzIoZ2xfTG9jYWxJbnZvY2F0aW9uSUQueHkpIC8gOC4wLCAxLjApOwoJaW1hZ2VTdG9yZShTb21lUmVzb3VyY2UsIGl2ZWMyKGdsX0dsb2JhbEludm9jYXRpb25JRC54eSksIEJvcmluZ0RhdGEpOwp9Cg==");
		Shaders[0] = CompileShader(ShaderSource, GL_COMPUTE_SHADER);
	}
	{
		std::string ShaderSource = DecodeBase64("I3ZlcnNpb24gNDIwCgovKgoJQ29weXJpZ2h0IDIwMjAgQWV2YSBQYWxlY2VrCgoJTGljZW5zZWQgdW5kZXIgdGhlIEFwYWNoZSBMaWNlbnNlLCBWZXJzaW9uIDIuMCAodGhlICJMaWNlbnNlIik7Cgl5b3UgbWF5IG5vdCB1c2UgdGhpcyBmaWxlIGV4Y2VwdCBpbiBjb21wbGlhbmNlIHdpdGggdGhlIExpY2Vuc2UuCglZb3UgbWF5IG9idGFpbiBhIGNvcHkgb2YgdGhlIExpY2Vuc2UgYXQKCgkJaHR0cDovL3d3dy5hcGFjaGUub3JnL2xpY2Vuc2VzL0xJQ0VOU0UtMi4wCgoJVW5sZXNzIHJlcXVpcmVkIGJ5IGFwcGxpY2FibGUgbGF3IG9yIGFncmVlZCB0byBpbiB3cml0aW5nLCBzb2Z0d2FyZQoJZGlzdHJpYnV0ZWQgdW5kZXIgdGhlIExpY2Vuc2UgaXMgZGlzdHJpYnV0ZWQgb24gYW4gIkFTIElTIiBCQVNJUywKCVdJVEhPVVQgV0FSUkFOVElFUyBPUiBDT05ESVRJT05TIE9GIEFOWSBLSU5ELCBlaXRoZXIgZXhwcmVzcyBvciBpbXBsaWVkLgoJU2VlIHRoZSBMaWNlbnNlIGZvciB0aGUgc3BlY2lmaWMgbGFuZ3VhZ2UgZ292ZXJuaW5nIHBlcm1pc3Npb25zIGFuZAoJbGltaXRhdGlvbnMgdW5kZXIgdGhlIExpY2Vuc2UuCiovCgpsYXlvdXQoc3RkMTQwLCBiaW5kaW5nID0gMCkKdW5pZm9ybSBXaW5kb3dQYXJhbXMKewoJdmVjNCBXaW5kb3dTaXplOwoJdmVjNCBXaW5kb3dTY2FsZTsKCWZsb2F0IEVsYXBzZWRUaW1lOwp9OwpsYXlvdXQocmdiYTMyZiwgYmluZGluZyA9IDApCnVuaWZvcm0gaW1hZ2UyRCBTb21lUmVzb3VyY2U7CgoKdm9pZCBtYWluKCkKewoJZ2xfUG9zaXRpb24gPSB2ZWM0KC0xLjAgKyBmbG9hdCgoZ2xfVmVydGV4SUQgJiAxKSA8PCAyKSwgLTEuMCArIGZsb2F0KChnbF9WZXJ0ZXhJRCAmIDIpIDw8IDEpLCAwLCAxKTsKfQo=");
		Shaders[1] = CompileShader(ShaderSource, GL_VERTEX_SHADER);
	}
	{
		std::string ShaderSource = DecodeBase64("I3ZlcnNpb24gNDIwCiNleHRlbnNpb24gR0xfQVJCX3NoYWRlcl9pbWFnZV9sb2FkX3N0b3JlIDogcmVxdWlyZQoKLyoKCUNvcHlyaWdodCAyMDIwIEFldmEgUGFsZWNlawoKCUxpY2Vuc2VkIHVuZGVyIHRoZSBBcGFjaGUgTGljZW5zZSwgVmVyc2lvbiAyLjAgKHRoZSAiTGljZW5zZSIpOwoJeW91IG1heSBub3QgdXNlIHRoaXMgZmlsZSBleGNlcHQgaW4gY29tcGxpYW5jZSB3aXRoIHRoZSBMaWNlbnNlLgoJWW91IG1heSBvYnRhaW4gYSBjb3B5IG9mIHRoZSBMaWNlbnNlIGF0CgoJCWh0dHA6Ly93d3cuYXBhY2hlLm9yZy9saWNlbnNlcy9MSUNFTlNFLTIuMAoKCVVubGVzcyByZXF1aXJlZCBieSBhcHBsaWNhYmxlIGxhdyBvciBhZ3JlZWQgdG8gaW4gd3JpdGluZywgc29mdHdhcmUKCWRpc3RyaWJ1dGVkIHVuZGVyIHRoZSBMaWNlbnNlIGlzIGRpc3RyaWJ1dGVkIG9uIGFuICJBUyBJUyIgQkFTSVMsCglXSVRIT1VUIFdBUlJBTlRJRVMgT1IgQ09ORElUSU9OUyBPRiBBTlkgS0lORCwgZWl0aGVyIGV4cHJlc3Mgb3IgaW1wbGllZC4KCVNlZSB0aGUgTGljZW5zZSBmb3IgdGhlIHNwZWNpZmljIGxhbmd1YWdlIGdvdmVybmluZyBwZXJtaXNzaW9ucyBhbmQKCWxpbWl0YXRpb25zIHVuZGVyIHRoZSBMaWNlbnNlLgoqLwoKbGF5b3V0KHN0ZDE0MCwgYmluZGluZyA9IDApCnVuaWZvcm0gV2luZG93UGFyYW1zCnsKCXZlYzQgV2luZG93U2l6ZTsKCXZlYzQgV2luZG93U2NhbGU7CglmbG9hdCBFbGFwc2VkVGltZTsKfTsKbGF5b3V0KHJnYmEzMmYsIGJpbmRpbmcgPSAwKQp1bmlmb3JtIGltYWdlMkQgU29tZVJlc291cmNlOwpsYXlvdXQobG9jYXRpb24gPSAwKQogb3V0IHZlYzQgT3V0Q29sb3I7Cgp2b2lkIG1haW4oKQp7CglpdmVjMiBQaXhlbCA9IGl2ZWMyKGZsb29yKGdsX0ZyYWdDb29yZC54eSkpOwoJT3V0Q29sb3IgPSBpbWFnZUxvYWQoU29tZVJlc291cmNlLCBQaXhlbCAlIDEwMjQpOwp9Cg==");
		Shaders[2] = CompileShader(ShaderSource, GL_FRAGMENT_SHADER);
	}
	{
		GLuint Stages[1] = { Shaders[0] };
		ShaderPrograms[0] = LinkShaders("ComputeDemo", &Stages[0], 1);
	}
	{
		GLuint Stages[2] = { Shaders[1], Shaders[2] };
		ShaderPrograms[1] = LinkShaders("Resolve", &Stages[0], 2);
	}
	{
		glCreateSamplers(1, &SamplerHandles[0]);
		{
			// sampler "PointSampler"
			glSamplerParameteri(SamplerHandles[0], GL_TEXTURE_MIN_FILTER, GL_NEAREST);
			glSamplerParameteri(SamplerHandles[0], GL_TEXTURE_MAG_FILTER, GL_NEAREST);
			glObjectLabel(GL_SAMPLER, SamplerHandles[0], -1, "PointSampler");
		}
	}
	{
		// texture "SomeResource"
		glCreateTextures(GL_TEXTURE_2D, 1, &TextureHandles[0]);
		glTextureStorage2D(TextureHandles[0], 1, GL_RGBA32F, (GLsizei)1024, (GLsizei)1024);
		glObjectLabel(GL_TEXTURE, TextureHandles[0], -1, "SomeResource");
	}
	{
		{
			glCreateFramebuffers(1, &FrameBufferHandles[0]);
			glObjectLabel(GL_FRAMEBUFFER, FrameBufferHandles[0], -1, "ComputeDemo");
		}
		{
			glCreateFramebuffers(1, &FrameBufferHandles[1]);
			glObjectLabel(GL_FRAMEBUFFER, FrameBufferHandles[1], -1, "Resolve");
		}
	}
	{
		glCreateBuffers(1, &BufferHandles[0]);
		{
			// buffer "WindowParams"
			glNamedBufferStorage(BufferHandles[0], 48, nullptr, GL_DYNAMIC_STORAGE_BIT | GL_MAP_WRITE_BIT);
			glObjectLabel(GL_BUFFER, BufferHandles[0], -1, "WindowParams");
		}
	}
}


namespace Renderer
{
	void ComputeDemo(int FrameIndex, double CurrentTime, double DeltaTime)
	{
		glClearColor(0, 0, 0, 1.0);
		glClear(GL_COLOR_BUFFER_BIT);
		glClearDepth(0);
		glClear(GL_DEPTH_BUFFER_BIT);
		{
			glPushDebugGroup(GL_DEBUG_SOURCE_APPLICATION, 0, -1, "ComputeDemo");
			glUseProgram(ShaderPrograms[0]);
			glBindBufferBase(GL_UNIFORM_BUFFER, 0, BufferHandles[0]);
			glBindImageTexture(0, TextureHandles[0], 0, GL_FALSE, 0, GL_READ_WRITE, GL_RGBA32F);
			glDispatchCompute(128, 128, 1);
			glPopDebugGroup();
		}
		{
			glPushDebugGroup(GL_DEBUG_SOURCE_APPLICATION, 0, -1, "Resolve");
			glUseProgram(ShaderPrograms[1]);
			glBindFramebuffer(GL_FRAMEBUFFER, 0);
			glBindBufferBase(GL_UNIFORM_BUFFER, 0, BufferHandles[0]);
			glBindImageTexture(0, TextureHandles[0], 0, GL_FALSE, 0, GL_READ_WRITE, GL_RGBA32F);
			glDrawArraysInstanced(GL_TRIANGLES, 0, 3, 1);
			glPopDebugGroup();
		}
	}
}


void DrawFrame(int FrameIndex, double CurrentTime, double DeltaTime)
{
	switch (CurrentRenderer)
	{
	case 0:
		Renderer::ComputeDemo(FrameIndex, CurrentTime, DeltaTime);
		break;
	default:
		HaltAndCatchFire();
	}
}


void WindowResized()
{

}


int main()
{
	SDL_SetMainReady();
	if (SDL_Init(SDL_INIT_VIDEO) != 0)
	{
		std::cout << "Fatal Error: SDL failed to initialize: " << SDL_GetError() << std::endl;
		return 1;
	}

	SDL_GL_LoadLibrary(nullptr);
	SDL_GL_SetAttribute(SDL_GL_ACCELERATED_VISUAL, 1);
	SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 4);
	SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 2);
	SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_CORE);
#if DEBUG_BUILD
	SDL_GL_SetAttribute(SDL_GL_CONTEXT_FLAGS, SDL_GL_CONTEXT_DEBUG_FLAG);
#endif // DEBUG_BUILD

	Window = SDL_CreateWindow(WindowTitle, SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, ScreenWidth, ScreenHeight, SDL_WINDOW_RESIZABLE | SDL_WINDOW_OPENGL);
	if (!Window)
	{
		std::cout << "Fatal Error: SDL failed to create a window: " << SDL_GetError() << std::endl;
		SDL_Quit();
		return 1;
	}

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

	InitialSetup();
	UserSetupCallback(Window);

	while (!SDL_QuitRequested())
	{
		SDL_PumpEvents();
		UpdateWindowSize();
		if (WindowIsDirty)
		{
			WindowResized();
			WindowIsDirty = false;
			glViewport(0, 0, ScreenWidth, ScreenHeight);
		}
		static unsigned int FrameIndex = 0;
		static unsigned int DeltaTimeTicks = 0.0;
		static unsigned int StartTimeTicks = SDL_GetTicks();
		{
			// Times are in seconds
			const double StartTime = (double)StartTimeTicks / 1000.0;
			const double DeltaTime = (double)DeltaTimeTicks / 1000.0;
			UserFrameCallback(FrameIndex, StartTime, DeltaTime);
			DrawFrame(FrameIndex, StartTime, DeltaTime);
			SDL_GL_SwapWindow(Window);
		}
		++FrameIndex;
		unsigned int EndTimeTicks = SDL_GetTicks();
		DeltaTimeTicks = EndTimeTicks - StartTimeTicks;
		StartTimeTicks = EndTimeTicks;
	}

	
	SDL_DestroyWindow(Window);
	SDL_Quit();
	return 0;
}
