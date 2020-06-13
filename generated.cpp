#include <fstream>
#include <iostream>
#include <array>
#include <string>
#include <cstdint>
#include <stdlib.h>
#include <glad/glad.h>
#include <GLFW/glfw3.h>


namespace Glsl
{
	using uint = unsigned int;
	using bvec2 = std::array<std::int32_t, 2>;
	using bvec3 = std::array<std::int32_t, 3>;
	using bvec4 = std::array<std::int32_t, 4>;
	using ivec2 = std::array<int, 2>;
	using ivec3 = std::array<int, 3>;
	using ivec4 = std::array<int, 4>;
	using uvec2 = std::array<unsigned int, 2>;
	using uvec3 = std::array<unsigned int, 3>;
	using uvec4 = std::array<unsigned int, 4>;
	using vec2 = std::array<float, 2>;
	using vec3 = std::array<float, 3>;
	using vec4 = std::array<float, 4>;
	using mat2 = std::array<std::array<float, 2>, 2>;
	using mat3 = std::array<std::array<float, 3>, 3>;
	using mat4 = std::array<std::array<float, 4>, 4>;


	struct Fnord
	{
		bvec3 eggs;
		float cheese;
		ivec2 butter;
		mat3 milk;
		bool kale;
		vec3 oranges[3];
		int lemons;
	};
	struct Meep
	{
		Fnord wat;
		Fnord fhqwhgads[2];
	};
}


const char* WindowTitle = "Hello World!";
int ScreenWidth = 512;
int ScreenHeight = 512;
float ScreenScaleX = 1.0;
float ScreenScaleY = 1.0;
bool WindowIsDirty = true;
GLFWwindow* Window;


GLuint Shaders[3] = { 0 };
GLuint ShaderPrograms[2] = { 0 };
GLuint BufferHandles[2] = { 0 };


namespace Upload
{
	using _int = std::int32_t;
	using _bool = std::int32_t;
	using uint = std::uint32_t;
	using bvec2 = std::array<std::int32_t, 2>;
	using bvec3 = std::array<std::int32_t, 3>;
	using bvec4 = std::array<std::int32_t, 4>;
	using ivec2 = std::array<std::int32_t, 2>;
	using ivec3 = std::array<std::int32_t, 3>;
	using ivec4 = std::array<std::int32_t, 4>;
	using uvec2 = std::array<std::uint32_t, 2>;
	using uvec3 = std::array<std::uint32_t, 3>;
	using uvec4 = std::array<std::uint32_t, 4>;
	using vec2 = std::array<float, 2>;
	using vec3 = std::array<float, 3>;
	using vec4 = std::array<float, 4>;

	template <typename UploadType, typename GlslType>
	__forceinline void Reflow(char* MappedBuffer, size_t Offset, GlslType Data)
	{
		*((UploadType*)(MappedBuffer + Offset)) = (UploadType)Data;
	}
	void Fnord (GLuint Handle, Glsl::Fnord& Data)
	{
		char* Mapped = (char*)glMapNamedBufferRange(Handle, 0, 40, GL_MAP_WRITE_BIT | GL_MAP_INVALIDATE_BUFFER_BIT );
		Reflow<bvec3>(Mapped, 0, Data.eggs);
		Reflow<float>(Mapped, 3, Data.cheese);
		Reflow<ivec2>(Mapped, 4, Data.butter);
		Reflow< vec3>(Mapped, 8, Data.milk[0]);
		Reflow< vec3>(Mapped, 12, Data.milk[1]);
		Reflow< vec3>(Mapped, 16, Data.milk[2]);
		Reflow<_bool>(Mapped, 20, Data.kale);
		Reflow< vec3>(Mapped, 24, Data.oranges[0]);
		Reflow< vec3>(Mapped, 28, Data.oranges[1]);
		Reflow< vec3>(Mapped, 32, Data.oranges[2]);
		Reflow< _int>(Mapped, 36, Data.lemons);
		glUnmapNamedBuffer(Handle);
	}
	void Meep (GLuint Handle, Glsl::Meep& Data)
	{
		char* Mapped = (char*)glMapNamedBufferRange(Handle, 0, 120, GL_MAP_WRITE_BIT | GL_MAP_INVALIDATE_BUFFER_BIT );
		Reflow<bvec3>(Mapped, 0, Data.wat.eggs);
		Reflow<float>(Mapped, 3, Data.wat.cheese);
		Reflow<ivec2>(Mapped, 4, Data.wat.butter);
		Reflow< vec3>(Mapped, 8, Data.wat.milk[0]);
		Reflow< vec3>(Mapped, 12, Data.wat.milk[1]);
		Reflow< vec3>(Mapped, 16, Data.wat.milk[2]);
		Reflow<_bool>(Mapped, 20, Data.wat.kale);
		Reflow< vec3>(Mapped, 24, Data.wat.oranges[0]);
		Reflow< vec3>(Mapped, 28, Data.wat.oranges[1]);
		Reflow< vec3>(Mapped, 32, Data.wat.oranges[2]);
		Reflow< _int>(Mapped, 36, Data.wat.lemons);
		Reflow<bvec3>(Mapped, 40, Data.fhqwhgads[0].eggs);
		Reflow<float>(Mapped, 43, Data.fhqwhgads[0].cheese);
		Reflow<ivec2>(Mapped, 44, Data.fhqwhgads[0].butter);
		Reflow< vec3>(Mapped, 48, Data.fhqwhgads[0].milk[0]);
		Reflow< vec3>(Mapped, 52, Data.fhqwhgads[0].milk[1]);
		Reflow< vec3>(Mapped, 56, Data.fhqwhgads[0].milk[2]);
		Reflow<_bool>(Mapped, 60, Data.fhqwhgads[0].kale);
		Reflow< vec3>(Mapped, 64, Data.fhqwhgads[0].oranges[0]);
		Reflow< vec3>(Mapped, 68, Data.fhqwhgads[0].oranges[1]);
		Reflow< vec3>(Mapped, 72, Data.fhqwhgads[0].oranges[2]);
		Reflow< _int>(Mapped, 76, Data.fhqwhgads[0].lemons);
		Reflow<bvec3>(Mapped, 80, Data.fhqwhgads[1].eggs);
		Reflow<float>(Mapped, 83, Data.fhqwhgads[1].cheese);
		Reflow<ivec2>(Mapped, 84, Data.fhqwhgads[1].butter);
		Reflow< vec3>(Mapped, 88, Data.fhqwhgads[1].milk[0]);
		Reflow< vec3>(Mapped, 92, Data.fhqwhgads[1].milk[1]);
		Reflow< vec3>(Mapped, 96, Data.fhqwhgads[1].milk[2]);
		Reflow<_bool>(Mapped, 100, Data.fhqwhgads[1].kale);
		Reflow< vec3>(Mapped, 104, Data.fhqwhgads[1].oranges[0]);
		Reflow< vec3>(Mapped, 108, Data.fhqwhgads[1].oranges[1]);
		Reflow< vec3>(Mapped, 112, Data.fhqwhgads[1].oranges[2]);
		Reflow< _int>(Mapped, 116, Data.fhqwhgads[1].lemons);
		glUnmapNamedBuffer(Handle);
	}
}


void HaltAndCatchFire()
{
	__fastfail(7);
}


void ReadFile(std::string& Source, std::string Path)
{
	std::ifstream File(Path);
	if (!File.is_open())
	{
		std::cout << "Error: cannot open file \"" << Path << "\"\n";
		HaltAndCatchFire();
	}
	std::string Line;
	while (getline(File, Line))
	{
		Source += Line + "\n";
	}
}


GLuint CompileShader(std::string Path, GLenum ShaderType)
{
	std::cout << "compiling shader: " << Path << "\n";
	std::string Source;
	ReadFile(Source, Path);
	GLuint Handle = glCreateShader(ShaderType);
	const char* SourcePtr = Source.c_str();
	glShaderSource(Handle, 1, &SourcePtr, nullptr);
	glCompileShader(Handle);
	{
		GLint LogLength;
		glGetShaderiv(Handle, GL_INFO_LOG_LENGTH, &LogLength);
		if (LogLength > 0)
		{
			char* InfoLog = (char*)malloc(sizeof(char) * LogLength);
			glGetShaderInfoLog(Handle, LogLength, nullptr, InfoLog);
			std::cout \
				<< "Shader info log for \"" << Path << "\":\n"
				<< InfoLog << "\n\n";
			free(InfoLog);
		}
		GLint Status;
		glGetShaderiv(Handle, GL_COMPILE_STATUS, &Status);
		if (Status == GL_FALSE)
		{
			std::cout << "Failed to compile shader \"" << Path << "\"!\n";
			glDeleteShader(Handle);
			HaltAndCatchFire();
		}
	}
	return Handle;
}


GLuint LinkShaders(std::string Name, GLuint* Shaders, int ShaderCount)
{
	std::cout << "linking shader program: " << Name << "\n";
	GLuint Handle = glCreateProgram();
	for (int i = 0; i < ShaderCount; ++i)
	{
		glAttachShader(Handle, Shaders[i]);
	}
	glLinkProgram(Handle);
	{
		GLint LogLength;
		glGetProgramiv(Handle, GL_INFO_LOG_LENGTH, &LogLength);
		if (LogLength > 0)
		{
			char* InfoLog = (char*)malloc(sizeof(char) * LogLength);
			glGetProgramInfoLog(Handle, LogLength, nullptr, InfoLog);
			std::cout \
				<< "Shader linking info log for program \"" << Name << "\":\n"
				<< InfoLog << "\n\n";
			free(InfoLog);
		}
		GLint Status;
		glGetProgramiv(Handle, GL_LINK_STATUS, &Status);
		if (Status == GL_FALSE)
		{
			std::cout << "Failed to link shader program \"" << Name << "\"!\n";
			glDeleteProgram(Handle);
			for (int i = 0; i < ShaderCount; ++i)
			{
				glDeleteShader(Shaders[i]);
			}
			HaltAndCatchFire();
		}
	}
	for (int i = 0; i < ShaderCount; ++i)
	{
		glDetachShader(Handle, Shaders[i]);
	}
	return Handle;
}


#if DEBUG_BUILD
void ErrorCallback(int Error, const char* Description)
{
	std::cout << "OpenGL Error: " << Description << '\n';
	HaltAndCatchFire();
}
#endif // DEBUG_BUILD


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
	glDisable(GL_DEPTH_TEST);
	glDisable(GL_CULL_FACE);
	glClipControl(GL_LOWER_LEFT, GL_NEGATIVE_ONE_TO_ONE);
	glDepthRange(1.0, 0.0);
	glFrontFace(GL_CCW);
	glCreateBuffers(2, &BufferHandles[0]);
	Shaders[0] = CompileShader("shaders/blue.fs.glsl", GL_FRAGMENT_SHADER);
	Shaders[1] = CompileShader("shaders/red.fs.glsl", GL_FRAGMENT_SHADER);
	Shaders[2] = CompileShader("shaders/splat.vs.glsl", GL_VERTEX_SHADER);
	{
		GLuint Stages[2] = { Shaders[2], Shaders[1] };
		ShaderPrograms[0] = LinkShaders("draw red", &Stages[0], 2);
	}
	{
		GLuint Stages[2] = { Shaders[2], Shaders[0] };
		ShaderPrograms[1] = LinkShaders("draw blue", &Stages[0], 2);
	}
	glNamedBufferStorage(0, 40, nullptr, GL_DYNAMIC_STORAGE_BIT | GL_MAP_WRITE_BIT);
	glNamedBufferStorage(1, 120, nullptr, GL_DYNAMIC_STORAGE_BIT | GL_MAP_WRITE_BIT);
	{
		Glsl::Fnord TestUpload = { 0 };
		Upload::Fnord (0, TestUpload);
	}
	{
		Glsl::Meep TestUpload = { 0 };
		Upload::Meep (1, TestUpload);
	}
}


void DrawFrame(int FrameIndex, double ElapsedTime)
{
	glClearColor(0.5, 0.5, 0.5, 1.0);
	glClear(GL_COLOR_BUFFER_BIT);
	glClearDepth(0.0);
	glClear(GL_DEPTH_BUFFER_BIT);
	{
		glPushDebugGroup(GL_DEBUG_SOURCE_APPLICATION, 0, -1, "draw red");
		glUseProgram(ShaderPrograms[0]);
		glDrawArraysInstanced(GL_TRIANGLES, 0, 6, 1);
		glPopDebugGroup();
	}
	{
		glPushDebugGroup(GL_DEBUG_SOURCE_APPLICATION, 0, -1, "draw blue");
		glUseProgram(ShaderPrograms[1]);
		glDrawArraysInstanced(GL_TRIANGLES, 0, 6, 1);
		glPopDebugGroup();
	}
}


int main()
{
#if DEBUG_BUILD
	glfwSetErrorCallback(ErrorCallback);
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

	InitialSetup();

	while (!glfwWindowShouldClose(Window))
	{
		static int FrameIndex = 0;
		static double ElapsedTime = 0.0;
		static double StartTime = glfwGetTime();
		{
			DrawFrame(FrameIndex++, ElapsedTime);
			glfwSwapBuffers(Window);
			glfwPollEvents();
		}
		double EndTime = glfwGetTime();
		ElapsedTime = EndTime - StartTime;
		StartTime = EndTime;
	}

	glfwDestroyWindow(Window);
	glfwTerminate();
	return 0;
}
