﻿#include <fstream>
#include <iostream>
#include <string>
#include <stdlib.h>
#include <glad/glad.h>
#include <GLFW/glfw3.h>


const char* WindowTitle = "Hello World!";
int ScreenWidth = 512;
int ScreenHeight = 512;
float ScreenScaleX = 1.0;
float ScreenScaleY = 1.0;
bool WindowIsDirty = true;
GLFWwindow* Window;


GLuint Shaders[3] = { 0 };
GLuint ShaderPrograms[2] = { 0 };


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
	Shaders[0] = CompileShader("shaders/blue.fs.glsl", GL_FRAGMENT_SHADER);
	Shaders[1] = CompileShader("shaders/red.fs.glsl", GL_FRAGMENT_SHADER);
	Shaders[2] = CompileShader("shaders/splat.vs.glsl", GL_VERTEX_SHADER);
	{
		GLuint Stages[2] = { Shaders[1], Shaders[2] };
		ShaderPrograms[0] = LinkShaders("draw red", &Stages[0], 2);
	}
	{
		GLuint Stages[2] = { Shaders[2], Shaders[0] };
		ShaderPrograms[1] = LinkShaders("draw blue", &Stages[0], 2);
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
