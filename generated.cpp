﻿#include "graffeine.hpp"


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


GLuint Shaders[5] = { 0 };
GLuint ShaderPrograms[3] = { 0 };
std::string ShaderPaths[5] = {
	"generated_shaders\\splat.vs.glsl.da0e6628e3cf2c7d201d3564cca3fd66.glsl",
	"generated_shaders\\texture.fs.glsl.9dde9a16c1c97192c8ca7823dfceb4be.glsl",
	"generated_shaders\\splat.vs.glsl.3fdbf6c0576b6e6d6cba510e637d0a75.glsl",
	"generated_shaders\\red.fs.glsl.72e5034f0934a476f7cd05199a16f1d2.glsl",
	"generated_shaders\\blue.fs.glsl.0d4bfa50448166804174e28991b2f622.glsl"
};
GLuint SamplerHandles[1] = { 0 };
GLuint TextureHandles[2] = { 0 };
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
		glCreateSamplers(1, &SamplerHandles[0]);
		{
			// sampler "SomeSampler"
			glSamplerParameteri(SamplerHandles[0], GL_TEXTURE_MIN_FILTER, GL_LINEAR);
			glSamplerParameteri(SamplerHandles[0], GL_TEXTURE_MAG_FILTER, GL_LINEAR);
			glObjectLabel(GL_SAMPLER, SamplerHandles[0], -1, "SomeSampler");
		}
	}
	{
		{
			// texture "YourTextureHere"
			ImageData Image = ReadPng("woman_taking_in_cheese_from_fire_escape.png");
			glCreateTextures(GL_TEXTURE_2D, 1, &TextureHandles[0]);
			glTextureStorage2D(TextureHandles[0], 1, GL_RGBA8, Image.Width, Image.Height);
			glObjectLabel(GL_TEXTURE, TextureHandles[0], -1, "YourTextureHere");
			glTextureSubImage2D(TextureHandles[0], 0, 0, 0, Image.Width, Image.Height, GL_RGBA, GL_UNSIGNED_BYTE, Image.Data.data());
		}
		{
			// texture "SizedTexture"
			glCreateTextures(GL_TEXTURE_2D, 1, &TextureHandles[1]);
			glTextureStorage2D(TextureHandles[1], 1, GL_RGBA8, (GLsizei)(UserVars::MiscVar / 2), (GLsizei)(UserVars::MiscVar / 2));
			glObjectLabel(GL_TEXTURE, TextureHandles[1], -1, "SizedTexture");
		}
	}
	{
		glCreateBuffers(1, &BufferHandles[0]);
		{
			// buffer "SomeHandle"
			glNamedBufferStorage(BufferHandles[0], 16, nullptr, GL_DYNAMIC_STORAGE_BIT | GL_MAP_WRITE_BIT);
			glObjectLabel(GL_BUFFER, BufferHandles[0], -1, "SomeHandle");
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
			glPushDebugGroup(GL_DEBUG_SOURCE_APPLICATION, 0, -1, "TextureTest");
			glUseProgram(ShaderPrograms[0]);
			glBindBufferBase(GL_UNIFORM_BUFFER, 0, BufferHandles[0]);
			glBindTextureUnit(0, TextureHandles[0]);
			glBindSampler(0, SamplerHandles[0]);
			glDisable(GL_DEPTH_TEST);
			glDisable(GL_CULL_FACE);
			glDrawArraysInstanced(GL_TRIANGLES, 0, 6, 1);
			glPopDebugGroup();
		}
	}
	void Blue(int FrameIndex, double CurrentTime, double DeltaTime)
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
			glPushDebugGroup(GL_DEBUG_SOURCE_APPLICATION, 0, -1, "SplatBlue");
			glUseProgram(ShaderPrograms[2]);
			glBindBufferBase(GL_UNIFORM_BUFFER, 0, BufferHandles[0]);
			glDisable(GL_DEPTH_TEST);
			glDisable(GL_CULL_FACE);
			glDrawArraysInstanced(GL_TRIANGLES, 0, 6, 1);
			glPopDebugGroup();
		}
	}
	void Red(int FrameIndex, double CurrentTime, double DeltaTime)
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
			glPushDebugGroup(GL_DEBUG_SOURCE_APPLICATION, 0, -1, "SplatRed");
			glUseProgram(ShaderPrograms[1]);
			glBindBufferBase(GL_UNIFORM_BUFFER, 0, BufferHandles[0]);
			glDisable(GL_DEPTH_TEST);
			glDisable(GL_CULL_FACE);
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
		Renderer::Blue(FrameIndex, CurrentTime, DeltaTime);
		break;
	case 2:
		Renderer::Red(FrameIndex, CurrentTime, DeltaTime);
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
