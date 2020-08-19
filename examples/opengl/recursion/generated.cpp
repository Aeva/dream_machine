#include "dream_machine.hpp"


namespace Glsl
{
	struct WindowParamsType
	{
		vec4 WindowSize;
		vec4 WindowScale;
		float ElapsedTime;
	};
}


const char* WindowTitle = "Hello World!";
int ScreenWidth = 512;
int ScreenHeight = 512;
float ScreenScaleX = 1.0;
float ScreenScaleY = 1.0;
bool WindowIsDirty = true;
GLFWwindow* Window;


extern int CurrentRenderer = 0;
extern void UserSetupCallback(GLFWwindow* Window);
extern void UserFrameCallback(GLFWwindow* Window);


namespace UserVars
{
	
}


GLuint Shaders[3] = { 0 };
GLuint ShaderPrograms[2] = { 0 };
GLuint SamplerHandles[1] = { 0 };
GLuint TextureHandles[2] = { 0 };
GLuint FrameBufferHandles[2] = { 0 };
GLuint BufferHandles[1] = { 0 };


namespace Upload
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


void GlfwWindowSizeCallback(GLFWwindow* Window, int Width, int Height)
{
	if (ScreenWidth != Width || ScreenHeight != Height)
	{
		ScreenWidth = Width;
		ScreenHeight = Height;
		WindowIsDirty = true;
	}
}


void GlfwWindowContentScaleCallback(GLFWwindow* Window, float ScaleX, float ScaleY)
{
	if (ScreenScaleX != ScaleX || ScreenScaleY != ScaleY)
	{
		ScreenScaleX = ScaleX;
		ScreenScaleY = ScaleY;
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
		std::string ShaderSource = DecodeBase64("I3ZlcnNpb24gNDIwCgovKgoJQ29weXJpZ2h0IDIwMjAgQWV2YSBQYWxlY2VrCgoJTGljZW5zZWQgdW5kZXIgdGhlIEFwYWNoZSBMaWNlbnNlLCBWZXJzaW9uIDIuMCAodGhlICJMaWNlbnNlIik7Cgl5b3UgbWF5IG5vdCB1c2UgdGhpcyBmaWxlIGV4Y2VwdCBpbiBjb21wbGlhbmNlIHdpdGggdGhlIExpY2Vuc2UuCglZb3UgbWF5IG9idGFpbiBhIGNvcHkgb2YgdGhlIExpY2Vuc2UgYXQKCgkJaHR0cDovL3d3dy5hcGFjaGUub3JnL2xpY2Vuc2VzL0xJQ0VOU0UtMi4wCgoJVW5sZXNzIHJlcXVpcmVkIGJ5IGFwcGxpY2FibGUgbGF3IG9yIGFncmVlZCB0byBpbiB3cml0aW5nLCBzb2Z0d2FyZQoJZGlzdHJpYnV0ZWQgdW5kZXIgdGhlIExpY2Vuc2UgaXMgZGlzdHJpYnV0ZWQgb24gYW4gIkFTIElTIiBCQVNJUywKCVdJVEhPVVQgV0FSUkFOVElFUyBPUiBDT05ESVRJT05TIE9GIEFOWSBLSU5ELCBlaXRoZXIgZXhwcmVzcyBvciBpbXBsaWVkLgoJU2VlIHRoZSBMaWNlbnNlIGZvciB0aGUgc3BlY2lmaWMgbGFuZ3VhZ2UgZ292ZXJuaW5nIHBlcm1pc3Npb25zIGFuZAoJbGltaXRhdGlvbnMgdW5kZXIgdGhlIExpY2Vuc2UuCiovCgpsYXlvdXQoc3RkMTQwLCBiaW5kaW5nID0gMCkKdW5pZm9ybSBXaW5kb3dQYXJhbXMKewoJdmVjNCBXaW5kb3dTaXplOwoJdmVjNCBXaW5kb3dTY2FsZTsKCWZsb2F0IEVsYXBzZWRUaW1lOwp9OwpsYXlvdXQoYmluZGluZyA9IDApCnVuaWZvcm0gc2FtcGxlcjJEIEFjY3VtdWxhdG9yOwoKCnZvaWQgbWFpbigpCnsKCWdsX1Bvc2l0aW9uID0gdmVjNCgtMS4wICsgZmxvYXQoKGdsX1ZlcnRleElEICYgMSkgPDwgMiksIC0xLjAgKyBmbG9hdCgoZ2xfVmVydGV4SUQgJiAyKSA8PCAxKSwgMCwgMSk7Cn0K");
		Shaders[0] = CompileShader(ShaderSource, GL_VERTEX_SHADER);
	}
	{
		std::string ShaderSource = DecodeBase64("I3ZlcnNpb24gNDIwCgovKgoJQ29weXJpZ2h0IDIwMjAgQWV2YSBQYWxlY2VrCgoJTGljZW5zZWQgdW5kZXIgdGhlIEFwYWNoZSBMaWNlbnNlLCBWZXJzaW9uIDIuMCAodGhlICJMaWNlbnNlIik7Cgl5b3UgbWF5IG5vdCB1c2UgdGhpcyBmaWxlIGV4Y2VwdCBpbiBjb21wbGlhbmNlIHdpdGggdGhlIExpY2Vuc2UuCglZb3UgbWF5IG9idGFpbiBhIGNvcHkgb2YgdGhlIExpY2Vuc2UgYXQKCgkJaHR0cDovL3d3dy5hcGFjaGUub3JnL2xpY2Vuc2VzL0xJQ0VOU0UtMi4wCgoJVW5sZXNzIHJlcXVpcmVkIGJ5IGFwcGxpY2FibGUgbGF3IG9yIGFncmVlZCB0byBpbiB3cml0aW5nLCBzb2Z0d2FyZQoJZGlzdHJpYnV0ZWQgdW5kZXIgdGhlIExpY2Vuc2UgaXMgZGlzdHJpYnV0ZWQgb24gYW4gIkFTIElTIiBCQVNJUywKCVdJVEhPVVQgV0FSUkFOVElFUyBPUiBDT05ESVRJT05TIE9GIEFOWSBLSU5ELCBlaXRoZXIgZXhwcmVzcyBvciBpbXBsaWVkLgoJU2VlIHRoZSBMaWNlbnNlIGZvciB0aGUgc3BlY2lmaWMgbGFuZ3VhZ2UgZ292ZXJuaW5nIHBlcm1pc3Npb25zIGFuZAoJbGltaXRhdGlvbnMgdW5kZXIgdGhlIExpY2Vuc2UuCiovCgpsYXlvdXQoc3RkMTQwLCBiaW5kaW5nID0gMCkKdW5pZm9ybSBXaW5kb3dQYXJhbXMKewoJdmVjNCBXaW5kb3dTaXplOwoJdmVjNCBXaW5kb3dTY2FsZTsKCWZsb2F0IEVsYXBzZWRUaW1lOwp9OwpsYXlvdXQoYmluZGluZyA9IDApCnVuaWZvcm0gc2FtcGxlcjJEIEFjY3VtdWxhdG9yOwpsYXlvdXQobG9jYXRpb24gPSAwKQogb3V0IHZlYzQgQWNjdW11bGF0b3JUYXJnZXQ7CgoKdm9pZCBtYWluKCkKewoJdmVjMiBVViA9IGdsX0ZyYWdDb29yZC54eSAqIFdpbmRvd1NpemUuenc7Cgl2ZWM0IEFjY3VtdWxhdGVkID0gdGV4dHVyZShBY2N1bXVsYXRvciwgVVYpOwoJQWNjdW11bGF0b3JUYXJnZXQgPSBBY2N1bXVsYXRlZCArPSAwLjAwMTsKfQo=");
		Shaders[1] = CompileShader(ShaderSource, GL_FRAGMENT_SHADER);
	}
	{
		std::string ShaderSource = DecodeBase64("I3ZlcnNpb24gNDIwCgovKgoJQ29weXJpZ2h0IDIwMjAgQWV2YSBQYWxlY2VrCgoJTGljZW5zZWQgdW5kZXIgdGhlIEFwYWNoZSBMaWNlbnNlLCBWZXJzaW9uIDIuMCAodGhlICJMaWNlbnNlIik7Cgl5b3UgbWF5IG5vdCB1c2UgdGhpcyBmaWxlIGV4Y2VwdCBpbiBjb21wbGlhbmNlIHdpdGggdGhlIExpY2Vuc2UuCglZb3UgbWF5IG9idGFpbiBhIGNvcHkgb2YgdGhlIExpY2Vuc2UgYXQKCgkJaHR0cDovL3d3dy5hcGFjaGUub3JnL2xpY2Vuc2VzL0xJQ0VOU0UtMi4wCgoJVW5sZXNzIHJlcXVpcmVkIGJ5IGFwcGxpY2FibGUgbGF3IG9yIGFncmVlZCB0byBpbiB3cml0aW5nLCBzb2Z0d2FyZQoJZGlzdHJpYnV0ZWQgdW5kZXIgdGhlIExpY2Vuc2UgaXMgZGlzdHJpYnV0ZWQgb24gYW4gIkFTIElTIiBCQVNJUywKCVdJVEhPVVQgV0FSUkFOVElFUyBPUiBDT05ESVRJT05TIE9GIEFOWSBLSU5ELCBlaXRoZXIgZXhwcmVzcyBvciBpbXBsaWVkLgoJU2VlIHRoZSBMaWNlbnNlIGZvciB0aGUgc3BlY2lmaWMgbGFuZ3VhZ2UgZ292ZXJuaW5nIHBlcm1pc3Npb25zIGFuZAoJbGltaXRhdGlvbnMgdW5kZXIgdGhlIExpY2Vuc2UuCiovCgpsYXlvdXQoc3RkMTQwLCBiaW5kaW5nID0gMCkKdW5pZm9ybSBXaW5kb3dQYXJhbXMKewoJdmVjNCBXaW5kb3dTaXplOwoJdmVjNCBXaW5kb3dTY2FsZTsKCWZsb2F0IEVsYXBzZWRUaW1lOwp9OwpsYXlvdXQoYmluZGluZyA9IDApCnVuaWZvcm0gc2FtcGxlcjJEIEFjY3VtdWxhdG9yOwpsYXlvdXQobG9jYXRpb24gPSAwKQogb3V0IHZlYzQgT3V0Q29sb3I7CgoKdm9pZCBtYWluKCkKewoJdmVjMiBVViA9IGdsX0ZyYWdDb29yZC54eSAqIFdpbmRvd1NpemUuenc7Cgl2ZWM0IEFjY3VtdWxhdGVkID0gdGV4dHVyZShBY2N1bXVsYXRvciwgVVYpOwoJT3V0Q29sb3IgPSBBY2N1bXVsYXRlZDsKfQo=");
		Shaders[2] = CompileShader(ShaderSource, GL_FRAGMENT_SHADER);
	}
	{
		GLuint Stages[2] = { Shaders[0], Shaders[1] };
		ShaderPrograms[0] = LinkShaders("Accumulate", &Stages[0], 2);
	}
	{
		GLuint Stages[2] = { Shaders[0], Shaders[2] };
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
		// texture "Accumulator"
		glCreateTextures(GL_TEXTURE_2D, 1, &TextureHandles[0]);
		glTextureStorage2D(TextureHandles[0], 1, GL_RGBA32F, (GLsizei)ScreenWidth, (GLsizei)ScreenHeight);
		glObjectLabel(GL_TEXTURE, TextureHandles[0], -1, "Accumulator");
	}
	{
		const float ClearColor[] = {0.0, 0.0, 0.0, 0.0};
		glClearTexImage(TextureHandles[0], 0, GL_RGBA32F, GL_FLOAT, &ClearColor[0]);
	}
	{
		// texture "AccumulatorTarget"
		glCreateTextures(GL_TEXTURE_2D, 1, &TextureHandles[1]);
		glTextureStorage2D(TextureHandles[1], 1, GL_RGBA32F, (GLsizei)ScreenWidth, (GLsizei)ScreenHeight);
		glObjectLabel(GL_TEXTURE, TextureHandles[1], -1, "AccumulatorTarget");
	}
	{
		const float ClearColor[] = {0.0, 0.0, 0.0, 0.0};
		glClearTexImage(TextureHandles[1], 0, GL_RGBA32F, GL_FLOAT, &ClearColor[0]);
	}
	{
		{
			glCreateFramebuffers(1, &FrameBufferHandles[0]);
			glNamedFramebufferTexture(FrameBufferHandles[0], GL_COLOR_ATTACHMENT0, TextureHandles[1], 0);
			glObjectLabel(GL_FRAMEBUFFER, FrameBufferHandles[0], -1, "Accumulate");
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
	void Accumulate(int FrameIndex, double CurrentTime, double DeltaTime)
	{
		glClearColor(0, 0, 0, 1.0);
		glClear(GL_COLOR_BUFFER_BIT);
		glClearDepth(0);
		glClear(GL_DEPTH_BUFFER_BIT);
		{
			Glsl::WindowParamsType Data = 	{
				{
					(float)(ScreenWidth),
					(float)(ScreenHeight),
					1.0f / (float)(ScreenWidth),
					1.0f / (float)(ScreenHeight),
				},
				{
					ScreenScaleX,
					ScreenScaleY,
					1.0f / ScreenScaleX,
					1.0f / ScreenScaleY,
				},
				(float)(CurrentTime * 0.1),
			};
			Upload::WindowParamsType(BufferHandles[0], Data);
		}
		{
			glPushDebugGroup(GL_DEBUG_SOURCE_APPLICATION, 0, -1, "Accumulate");
			glUseProgram(ShaderPrograms[0]);
			glBindFramebuffer(GL_FRAMEBUFFER, FrameBufferHandles[0]);
			glBindBufferBase(GL_UNIFORM_BUFFER, 0, BufferHandles[0]);
			glBindTextureUnit(0, TextureHandles[0]);
			glBindSampler(0, SamplerHandles[0]);
			glDrawArraysInstanced(GL_TRIANGLES, 0, 3, 1);
			glPopDebugGroup();
		}
		{
			GLuint Tmp = TextureHandles[0];
			TextureHandles[0] = TextureHandles[1];
			TextureHandles[1] = Tmp;
		}
		{
			// recreate framebuffer "Accumulate"
			glDeleteFramebuffers(1, &FrameBufferHandles[0]);
			glCreateFramebuffers(1, &FrameBufferHandles[0]);
			glNamedFramebufferTexture(FrameBufferHandles[0], GL_COLOR_ATTACHMENT0, TextureHandles[1], 0);
			glObjectLabel(GL_FRAMEBUFFER, FrameBufferHandles[0], -1, "Accumulate");
		}
		{
			glPushDebugGroup(GL_DEBUG_SOURCE_APPLICATION, 0, -1, "Resolve");
			glUseProgram(ShaderPrograms[1]);
			glBindFramebuffer(GL_FRAMEBUFFER, 0);
			glBindBufferBase(GL_UNIFORM_BUFFER, 0, BufferHandles[0]);
			glBindTextureUnit(0, TextureHandles[0]);
			glBindSampler(0, SamplerHandles[0]);
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
		Renderer::Accumulate(FrameIndex, CurrentTime, DeltaTime);
		break;
	default:
		HaltAndCatchFire();
	}
}


void WindowResized()
{
	{
		// resize texture "AccumulatorTarget"
		glDeleteTextures(1, &TextureHandles[1]);
		glCreateTextures(GL_TEXTURE_2D, 1, &TextureHandles[1]);
		glTextureStorage2D(TextureHandles[1], 1, GL_RGBA32F, (GLsizei)ScreenWidth, (GLsizei)ScreenHeight);
		glObjectLabel(GL_TEXTURE, TextureHandles[1], -1, "AccumulatorTarget");
	}
	{
		const float ClearColor[] = {0.0, 0.0, 0.0, 0.0};
		glClearTexImage(TextureHandles[1], 0, GL_RGBA32F, GL_FLOAT, &ClearColor[0]);
	}
	{
		// resize texture "Accumulator"
		glDeleteTextures(1, &TextureHandles[0]);
		glCreateTextures(GL_TEXTURE_2D, 1, &TextureHandles[0]);
		glTextureStorage2D(TextureHandles[0], 1, GL_RGBA32F, (GLsizei)ScreenWidth, (GLsizei)ScreenHeight);
		glObjectLabel(GL_TEXTURE, TextureHandles[0], -1, "Accumulator");
	}
	{
		const float ClearColor[] = {0.0, 0.0, 0.0, 0.0};
		glClearTexImage(TextureHandles[0], 0, GL_RGBA32F, GL_FLOAT, &ClearColor[0]);
	}
	{
		// recreate framebuffer "Accumulate"
		glDeleteFramebuffers(1, &FrameBufferHandles[0]);
		glCreateFramebuffers(1, &FrameBufferHandles[0]);
		glNamedFramebufferTexture(FrameBufferHandles[0], GL_COLOR_ATTACHMENT0, TextureHandles[1], 0);
		glObjectLabel(GL_FRAMEBUFFER, FrameBufferHandles[0], -1, "Accumulate");
	}
}


int main()
{
	//std::string Fnord = DecodeBase64("SGFpbCBFcmlzISEh");
	//std::cout << Fnord;
	//HaltAndCatchFire();
#if DEBUG_BUILD
	glfwSetErrorCallback(GlfwErrorCallback);
#endif // DEBUG_BUILD
	if (!glfwInit())
	{
		std::cout << "Fatal Error: GLFW failed to initialize!\n";
		return 1;
	}

	glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4);
	glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 2);
	glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
#if DEBUG_BUILD
	glfwWindowHint(GLFW_OPENGL_DEBUG_CONTEXT, GL_TRUE);
#endif // DEBUG_BUILD
	glfwWindowHint(GLFW_ALPHA_BITS, GLFW_DONT_CARE);
	glfwWindowHint(GLFW_DEPTH_BITS, GLFW_DONT_CARE);
	glfwWindowHint(GLFW_STENCIL_BITS, GLFW_DONT_CARE);
#if RENDER_TO_IMAGES
	glfwWindowHint(GLFW_VISIBLE, GLFW_FALSE);
#else
	glfwWindowHint(GLFW_SCALE_TO_MONITOR, GL_TRUE);
#endif // RENDER_TO_IMAGES

	Window = glfwCreateWindow(ScreenWidth, ScreenHeight, WindowTitle, NULL, NULL);
	if (!Window)
	{
		std::cout << "Fatal Error: glfw failed to create a window!\n";
		glfwTerminate();
		return 1;
	}

	glfwMakeContextCurrent(Window);

	glfwGetWindowSize(Window, &ScreenWidth, &ScreenHeight);
	glfwSetWindowSizeCallback(Window, GlfwWindowSizeCallback);

	glfwGetWindowContentScale(Window, &ScreenScaleX, &ScreenScaleY);
	glfwSetWindowContentScaleCallback(Window, GlfwWindowContentScaleCallback);

	if (!gladLoadGLLoader((GLADloadproc)glfwGetProcAddress))
	{
		std::cout << "Failed to initialize OpenGL context!\n";
		glfwDestroyWindow(Window);
		glfwTerminate();
		return 1;
	}
	else
	{
		std::cout << "Found OpenGL version " << GLVersion.major << "." << GLVersion.minor << "\n";
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
			std::cout << "Debug context not available!\n";
		}
	}
	else
	{
		std::cout << "Debug output extension not available!\n";
	}
#endif

	InitialSetup();
	UserSetupCallback(Window);

	while (!glfwWindowShouldClose(Window))
	{
		if (WindowIsDirty)
		{
			WindowResized();
			WindowIsDirty = false;
		}
		glViewport(0, 0, ScreenWidth, ScreenHeight);
		static int FrameIndex = 0;
		static double DeltaTime = 0.0;
		static double StartTime = glfwGetTime();
		{
			DrawFrame(FrameIndex++, StartTime, DeltaTime);
			glfwSwapBuffers(Window);
			glfwPollEvents();
			UserFrameCallback(Window);
		}
		double EndTime = glfwGetTime();
		DeltaTime = EndTime - StartTime;
		StartTime = EndTime;
	}

	glfwDestroyWindow(Window);
	glfwTerminate();
	return 0;
}
