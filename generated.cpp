#include "dream_machine.hpp"


namespace Glsl
{
	struct WindowParamsType
	{
		vec4 WindowSize;
		vec4 WindowScale;
		float ElapsedTime;
	};
	struct SomeType
	{
		mat4 Whatever;
		float SomeArray[0];
	};
	struct WhatsitType
	{
		SomeType Moop;
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
	extern int MiscVar = 2048;
}


GLuint Shaders[7] = { 0 };
GLuint ShaderPrograms[4] = { 0 };
std::string ShaderPaths[7] = {
	"generated_shaders\\splat.vs.glsl.9711e0b6715ace3d1c523ad8da281db5.glsl",
	"generated_shaders\\texture.fs.glsl.e8a8ab38ee8cbb2b62fc23a034c44176.glsl",
	"generated_shaders\\splat.vs.glsl.47d065ffb14cdc019f77274fed6c505a.glsl",
	"generated_shaders\\red.fs.glsl.e27c34cae30a790b21dd71528868119f.glsl",
	"generated_shaders\\blue.fs.glsl.d76a46ffe93e604d64ff4315f1b81dce.glsl",
	"generated_shaders\\splat.vs.glsl.26aa73cf0deb87ccdbb7f72a30b02023.glsl",
	"generated_shaders\\combiner.fs.glsl.ecf4735ddbe4b4b33d07043aae129f89.glsl"
};
GLuint SamplerHandles[2] = { 0 };
GLuint TextureHandles[4] = { 0 };
GLuint FrameBufferHandles[4] = { 0 };
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
	void SomeType (GLuint Handle, Glsl::SomeType& Data)
	{
		std::int32_t* Mapped = (std::int32_t*)glMapNamedBufferRange(Handle, 0, 224, GL_MAP_WRITE_BIT | GL_MAP_INVALIDATE_BUFFER_BIT);
		if (Mapped == nullptr)
		{
			std::cout << "Fatal error in function \"Upload::SomeType\": glMapNamedBufferRange returned nullptr.\n";
			HaltAndCatchFire();
		}

		glUnmapNamedBuffer(Handle);
	}
	void WhatsitType (GLuint Handle, Glsl::WhatsitType& Data)
	{
		std::int32_t* Mapped = (std::int32_t*)glMapNamedBufferRange(Handle, 0, 224, GL_MAP_WRITE_BIT | GL_MAP_INVALIDATE_BUFFER_BIT);
		if (Mapped == nullptr)
		{
			std::cout << "Fatal error in function \"Upload::WhatsitType\": glMapNamedBufferRange returned nullptr.\n";
			HaltAndCatchFire();
		}

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
	Shaders[0] = CompileShader(ShaderPaths[0], GL_VERTEX_SHADER);
	Shaders[1] = CompileShader(ShaderPaths[1], GL_FRAGMENT_SHADER);
	Shaders[2] = CompileShader(ShaderPaths[2], GL_VERTEX_SHADER);
	Shaders[3] = CompileShader(ShaderPaths[3], GL_FRAGMENT_SHADER);
	Shaders[4] = CompileShader(ShaderPaths[4], GL_FRAGMENT_SHADER);
	Shaders[5] = CompileShader(ShaderPaths[5], GL_VERTEX_SHADER);
	Shaders[6] = CompileShader(ShaderPaths[6], GL_FRAGMENT_SHADER);
	{
		GLuint Stages[2] = { Shaders[0], Shaders[1] };
		ShaderPrograms[0] = LinkShaders("TextureTest", &Stages[0], 2);
	}
	{
		GLuint Stages[2] = { Shaders[2], Shaders[3] };
		ShaderPrograms[1] = LinkShaders("SplatRed", &Stages[0], 2);
	}
	{
		GLuint Stages[2] = { Shaders[2], Shaders[4] };
		ShaderPrograms[2] = LinkShaders("SplatBlue", &Stages[0], 2);
	}
	{
		GLuint Stages[2] = { Shaders[5], Shaders[6] };
		ShaderPrograms[3] = LinkShaders("Combiner", &Stages[0], 2);
	}
	{
		glCreateSamplers(2, &SamplerHandles[0]);
		{
			// sampler "LinearSampler"
			glSamplerParameteri(SamplerHandles[0], GL_TEXTURE_MIN_FILTER, GL_LINEAR);
			glSamplerParameteri(SamplerHandles[0], GL_TEXTURE_MAG_FILTER, GL_LINEAR);
			glObjectLabel(GL_SAMPLER, SamplerHandles[0], -1, "LinearSampler");
		}
		{
			// sampler "PointSampler"
			glSamplerParameteri(SamplerHandles[1], GL_TEXTURE_MIN_FILTER, GL_NEAREST);
			glSamplerParameteri(SamplerHandles[1], GL_TEXTURE_MAG_FILTER, GL_NEAREST);
			glObjectLabel(GL_SAMPLER, SamplerHandles[1], -1, "PointSampler");
		}
	}
	{
		{
			// texture "FancyTexture"
			ImageData Image = ReadPng("woman_taking_in_cheese_from_fire_escape.png");
			glCreateTextures(GL_TEXTURE_2D, 1, &TextureHandles[0]);
			glTextureStorage2D(TextureHandles[0], 1, GL_RGBA8, Image.Width, Image.Height);
			glObjectLabel(GL_TEXTURE, TextureHandles[0], -1, "FancyTexture");
			glTextureSubImage2D(TextureHandles[0], 0, 0, 0, Image.Width, Image.Height, GL_RGBA, GL_UNSIGNED_BYTE, Image.Data.data());
		}
		{
			// texture "RedColorTarget"
			glCreateTextures(GL_TEXTURE_2D, 1, &TextureHandles[1]);
			glTextureStorage2D(TextureHandles[1], 1, GL_RGBA8, (GLsizei)ScreenWidth, (GLsizei)ScreenHeight);
			glObjectLabel(GL_TEXTURE, TextureHandles[1], -1, "RedColorTarget");
		}
		{
			// texture "BlueColorTarget"
			glCreateTextures(GL_TEXTURE_2D, 1, &TextureHandles[2]);
			glTextureStorage2D(TextureHandles[2], 1, GL_RGBA8, (GLsizei)ScreenWidth, (GLsizei)ScreenHeight);
			glObjectLabel(GL_TEXTURE, TextureHandles[2], -1, "BlueColorTarget");
		}
		{
			// texture "SomeDepthTarget"
			glCreateTextures(GL_TEXTURE_2D, 1, &TextureHandles[3]);
			glTextureStorage2D(TextureHandles[3], 1, GL_RGBA8, (GLsizei)ScreenWidth, (GLsizei)ScreenHeight);
			glObjectLabel(GL_TEXTURE, TextureHandles[3], -1, "SomeDepthTarget");
		}
	}
	{
		{
			glCreateFramebuffers(1, &FrameBufferHandles[0]);
			glObjectLabel(GL_FRAMEBUFFER, FrameBufferHandles[0], -1, "TextureTest");
		}
		{
			glCreateFramebuffers(1, &FrameBufferHandles[1]);
			glNamedFramebufferTexture(FrameBufferHandles[1], GL_COLOR_ATTACHMENT0, TextureHandles[1], 0);
			glNamedFramebufferTexture(FrameBufferHandles[1], GL_COLOR_ATTACHMENT1, TextureHandles[3], 0);
			glObjectLabel(GL_FRAMEBUFFER, FrameBufferHandles[1], -1, "SplatRed");
		}
		{
			glCreateFramebuffers(1, &FrameBufferHandles[2]);
			glNamedFramebufferTexture(FrameBufferHandles[2], GL_COLOR_ATTACHMENT0, TextureHandles[2], 0);
			glNamedFramebufferTexture(FrameBufferHandles[2], GL_COLOR_ATTACHMENT1, TextureHandles[3], 0);
			glObjectLabel(GL_FRAMEBUFFER, FrameBufferHandles[2], -1, "SplatBlue");
		}
		{
			glCreateFramebuffers(1, &FrameBufferHandles[3]);
			glObjectLabel(GL_FRAMEBUFFER, FrameBufferHandles[3], -1, "Combiner");
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
	void TextureTest(int FrameIndex, double CurrentTime, double DeltaTime)
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
			glPushDebugGroup(GL_DEBUG_SOURCE_APPLICATION, 0, -1, "TextureTest");
			glUseProgram(ShaderPrograms[0]);
			glBindFramebuffer(GL_FRAMEBUFFER, 0);
			glBindBufferBase(GL_UNIFORM_BUFFER, 0, BufferHandles[0]);
			glBindTextureUnit(0, TextureHandles[0]);
			glBindSampler(0, SamplerHandles[0]);
			glDisable(GL_DEPTH_TEST);
			glDisable(GL_CULL_FACE);
			glDrawArraysInstanced(GL_TRIANGLES, 0, 3, 1);
			glPopDebugGroup();
		}
	}
	void Multipass(int FrameIndex, double CurrentTime, double DeltaTime)
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
			glPushDebugGroup(GL_DEBUG_SOURCE_APPLICATION, 0, -1, "SplatRed");
			glUseProgram(ShaderPrograms[1]);
			glBindFramebuffer(GL_FRAMEBUFFER, FrameBufferHandles[1]);
			glBindBufferBase(GL_UNIFORM_BUFFER, 0, BufferHandles[0]);
			glDisable(GL_DEPTH_TEST);
			glDisable(GL_CULL_FACE);
			glDrawArraysInstanced(GL_TRIANGLES, 0, 3, 1);
			glPopDebugGroup();
		}
		{
			glPushDebugGroup(GL_DEBUG_SOURCE_APPLICATION, 0, -1, "SplatBlue");
			glUseProgram(ShaderPrograms[2]);
			glBindFramebuffer(GL_FRAMEBUFFER, FrameBufferHandles[2]);
			glBindBufferBase(GL_UNIFORM_BUFFER, 0, BufferHandles[0]);
			glDisable(GL_DEPTH_TEST);
			glDisable(GL_CULL_FACE);
			glDrawArraysInstanced(GL_TRIANGLES, 0, 3, 1);
			glPopDebugGroup();
		}
		{
			glPushDebugGroup(GL_DEBUG_SOURCE_APPLICATION, 0, -1, "Combiner");
			glUseProgram(ShaderPrograms[3]);
			glBindFramebuffer(GL_FRAMEBUFFER, 0);
			glBindBufferBase(GL_UNIFORM_BUFFER, 0, BufferHandles[0]);
			glBindTextureUnit(0, TextureHandles[1]);
			glBindTextureUnit(1, TextureHandles[2]);
			glBindSampler(0, SamplerHandles[0]);
			glBindSampler(1, SamplerHandles[0]);
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
		Renderer::TextureTest(FrameIndex, CurrentTime, DeltaTime);
		break;
	case 1:
		Renderer::Multipass(FrameIndex, CurrentTime, DeltaTime);
		break;
	default:
		HaltAndCatchFire();
	}
}


void WindowResized()
{
	{
		// resize texture "BlueColorTarget"
		glDeleteTextures(1, &TextureHandles[2]);
		glCreateTextures(GL_TEXTURE_2D, 1, &TextureHandles[2]);
		glTextureStorage2D(TextureHandles[2], 1, GL_RGBA8, (GLsizei)ScreenWidth, (GLsizei)ScreenHeight);
		glObjectLabel(GL_TEXTURE, TextureHandles[2], -1, "BlueColorTarget");
	}
	{
		// resize texture "RedColorTarget"
		glDeleteTextures(1, &TextureHandles[1]);
		glCreateTextures(GL_TEXTURE_2D, 1, &TextureHandles[1]);
		glTextureStorage2D(TextureHandles[1], 1, GL_RGBA8, (GLsizei)ScreenWidth, (GLsizei)ScreenHeight);
		glObjectLabel(GL_TEXTURE, TextureHandles[1], -1, "RedColorTarget");
	}
	{
		// resize texture "SomeDepthTarget"
		glDeleteTextures(1, &TextureHandles[3]);
		glCreateTextures(GL_TEXTURE_2D, 1, &TextureHandles[3]);
		glTextureStorage2D(TextureHandles[3], 1, GL_RGBA8, (GLsizei)ScreenWidth, (GLsizei)ScreenHeight);
		glObjectLabel(GL_TEXTURE, TextureHandles[3], -1, "SomeDepthTarget");
	}
	{
		// recreate framebuffer "SplatRed"
		glDeleteFramebuffers(1, &FrameBufferHandles[1]);
		glCreateFramebuffers(1, &FrameBufferHandles[1]);
		glNamedFramebufferTexture(FrameBufferHandles[1], GL_COLOR_ATTACHMENT0, TextureHandles[1], 0);
		glNamedFramebufferTexture(FrameBufferHandles[1], GL_COLOR_ATTACHMENT1, TextureHandles[3], 0);
		glObjectLabel(GL_FRAMEBUFFER, FrameBufferHandles[1], -1, "SplatRed");
	}
	{
		// recreate framebuffer "SplatBlue"
		glDeleteFramebuffers(1, &FrameBufferHandles[2]);
		glCreateFramebuffers(1, &FrameBufferHandles[2]);
		glNamedFramebufferTexture(FrameBufferHandles[2], GL_COLOR_ATTACHMENT0, TextureHandles[2], 0);
		glNamedFramebufferTexture(FrameBufferHandles[2], GL_COLOR_ATTACHMENT1, TextureHandles[3], 0);
		glObjectLabel(GL_FRAMEBUFFER, FrameBufferHandles[2], -1, "SplatBlue");
	}
}


int main()
{
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
