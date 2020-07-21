#include "dream_machine.hpp"


namespace Glsl
{
	struct FnordType
	{
		float ElapsedTime;
	};
	struct SomeType
	{
		mat4 Whatever;
		float Etc;
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
	"generated_shaders\\splat.vs.glsl.5497a189fdfb76a95b0e0f26702778b2.glsl",
	"generated_shaders\\texture.fs.glsl.7ce97d954962ce5888577c868ff02431.glsl",
	"generated_shaders\\splat.vs.glsl.08a884f33d310b52d885de6488577633.glsl",
	"generated_shaders\\red.fs.glsl.632c2093717c2dc377913861ca5699bb.glsl",
	"generated_shaders\\blue.fs.glsl.51b4743e5fd1a43f0dabec44c330000c.glsl",
	"generated_shaders\\splat.vs.glsl.a31fbe0727541e444e8f5aed46740a15.glsl",
	"generated_shaders\\combiner.fs.glsl.91e03989d241687fa732253118476225.glsl"
};
GLuint SamplerHandles[2] = { 0 };
GLuint TextureHandles[4] = { 0 };
GLuint FrameBufferHandles[4] = { 0 };
GLuint BufferHandles[1] = { 0 };


namespace Upload
{
	void FnordType (GLuint Handle, Glsl::FnordType& Data)
	{
		std::int32_t* Mapped = (std::int32_t*)glMapNamedBufferRange(Handle, 0, 16, GL_MAP_WRITE_BIT | GL_MAP_INVALIDATE_BUFFER_BIT);
		if (Mapped == nullptr)
		{
			std::cout << "Fatal error in function \"Upload::FnordType\": glMapNamedBufferRange returned nullptr.\n";
			HaltAndCatchFire();
		}
		Reflow<float>(Mapped, 0, Data.ElapsedTime);
		glUnmapNamedBuffer(Handle);
	}
	void SomeType (GLuint Handle, Glsl::SomeType& Data)
	{
		std::int32_t* Mapped = (std::int32_t*)glMapNamedBufferRange(Handle, 0, 80, GL_MAP_WRITE_BIT | GL_MAP_INVALIDATE_BUFFER_BIT);
		if (Mapped == nullptr)
		{
			std::cout << "Fatal error in function \"Upload::SomeType\": glMapNamedBufferRange returned nullptr.\n";
			HaltAndCatchFire();
		}
		Reflow<float>(Mapped, 16, Data.Etc);
		glUnmapNamedBuffer(Handle);
	}
	void WhatsitType (GLuint Handle, Glsl::WhatsitType& Data)
	{
		std::int32_t* Mapped = (std::int32_t*)glMapNamedBufferRange(Handle, 0, 80, GL_MAP_WRITE_BIT | GL_MAP_INVALIDATE_BUFFER_BIT);
		if (Mapped == nullptr)
		{
			std::cout << "Fatal error in function \"Upload::WhatsitType\": glMapNamedBufferRange returned nullptr.\n";
			HaltAndCatchFire();
		}
		Reflow<float>(Mapped, 16, Data.Moop.Etc);
		glUnmapNamedBuffer(Handle);
	}
}


void WindowSizeCallback(GLFWwindow* Window, int Width, int Height)
{
	if (ScreenWidth != Width || ScreenHeight != Height)
	{
		ScreenWidth = Width;
		ScreenHeight = Height;
		WindowIsDirty = true;
	}
}


void WindowContentScaleCallback(GLFWwindow* Window, float ScaleX, float ScaleY)
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
			glNamedBufferStorage(BufferHandles[0], 16, nullptr, GL_DYNAMIC_STORAGE_BIT | GL_MAP_WRITE_BIT);
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
			Glsl::FnordType Data = { (float)(CurrentTime * 0.1) };
			Upload::FnordType(BufferHandles[0], Data);
		}
		{
			glPushDebugGroup(GL_DEBUG_SOURCE_APPLICATION, 0, -1, "<Pipeline TextureTest>");
			glUseProgram(ShaderPrograms[0]);
			glBindFramebuffer(GL_FRAMEBUFFER, 0);
			glBindBufferBase(GL_UNIFORM_BUFFER, 0, BufferHandles[0]);
			glBindTextureUnit(0, TextureHandles[0]);
			glBindSampler(0, SamplerHandles[0]);
			glDisable(GL_DEPTH_TEST);
			glDisable(GL_CULL_FACE);
			glDrawArraysInstanced(GL_TRIANGLES, 0, 6, 1);
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
			Glsl::FnordType Data = { (float)(CurrentTime * 0.1) };
			Upload::FnordType(BufferHandles[0], Data);
		}
		{
			glPushDebugGroup(GL_DEBUG_SOURCE_APPLICATION, 0, -1, "<Pipeline SplatRed>");
			glUseProgram(ShaderPrograms[1]);
			glBindFramebuffer(GL_FRAMEBUFFER, FrameBufferHandles[1]);
			glDisable(GL_DEPTH_TEST);
			glDisable(GL_CULL_FACE);
			glDrawArraysInstanced(GL_TRIANGLES, 0, 6, 1);
			glPopDebugGroup();
		}
		{
			glPushDebugGroup(GL_DEBUG_SOURCE_APPLICATION, 0, -1, "<Pipeline SplatBlue>");
			glUseProgram(ShaderPrograms[2]);
			glBindFramebuffer(GL_FRAMEBUFFER, FrameBufferHandles[2]);
			glDisable(GL_DEPTH_TEST);
			glDisable(GL_CULL_FACE);
			glDrawArraysInstanced(GL_TRIANGLES, 0, 6, 1);
			glPopDebugGroup();
		}
		{
			glPushDebugGroup(GL_DEBUG_SOURCE_APPLICATION, 0, -1, "<Pipeline Combiner>");
			glUseProgram(ShaderPrograms[3]);
			glBindFramebuffer(GL_FRAMEBUFFER, 0);
			glBindBufferBase(GL_UNIFORM_BUFFER, 0, BufferHandles[0]);
			glBindTextureUnit(0, TextureHandles[1]);
			glBindTextureUnit(1, TextureHandles[2]);
			glBindSampler(0, SamplerHandles[0]);
			glBindSampler(1, SamplerHandles[0]);
			glDrawArraysInstanced(GL_TRIANGLES, 0, 6, 1);
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
	glfwSetWindowSizeCallback(Window, WindowSizeCallback);

	glfwGetWindowContentScale(Window, &ScreenScaleX, &ScreenScaleY);
	glfwSetWindowContentScaleCallback(Window, WindowContentScaleCallback);

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
