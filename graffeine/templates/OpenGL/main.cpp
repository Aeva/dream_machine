#include <fstream>
#include <iostream>
#include <array>
#include <string>
#include <cstdint>
#include <stdlib.h>
#include <glad/glad.h>
#include <GLFW/glfw3.h>


void HaltAndCatchFire()
{
	__fastfail(7);
}


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


「structs」
}


const char* WindowTitle = "「window_title」";
int ScreenWidth = 「window_width」;
int ScreenHeight = 「window_height」;
float ScreenScaleX = 1.0;
float ScreenScaleY = 1.0;
bool WindowIsDirty = true;
GLFWwindow* Window;
int CurrentRenderer = 1;


「globals」


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
	__forceinline void Reflow(std::int32_t* MappedBuffer, size_t Offset, GlslType Data)
	{
		*((UploadType*)(MappedBuffer + Offset)) = (UploadType)Data;
	}
「uploaders」
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


void DebugCallback(
	GLenum Source,
	GLenum Type,
	GLuint Id,
	GLenum Severity,
	GLsizei MessageLength,
	const GLchar* ErrorMessage,
	const void* UserParam)
{
	std::cout << ErrorMessage << "\n";
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
「initial_setup_hook」
}


namespace Renderer
{
「renderers」
}


void DrawFrame(int FrameIndex, double CurrentTime, double DeltaTime)
{
「draw_frame_hook」
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

	glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 「hint_version_major」);
	glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 「hint_version_minor」);
	glfwWindowHint(GLFW_OPENGL_PROFILE, 「hint_profile」);
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

	while (!glfwWindowShouldClose(Window))
	{
		static int FrameIndex = 0;
		static double DeltaTime = 0.0;
		static double StartTime = glfwGetTime();
		{
			DrawFrame(FrameIndex++, StartTime, DeltaTime);
			glfwSwapBuffers(Window);
			glfwPollEvents();
		}
		double EndTime = glfwGetTime();
		DeltaTime = EndTime - StartTime;
		StartTime = EndTime;
	}

	glfwDestroyWindow(Window);
	glfwTerminate();
	return 0;
}
