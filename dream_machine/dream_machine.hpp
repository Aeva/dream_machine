
/*
	Copyright 2020 Aeva Palecek

	Licensed under the Apache License, Version 2.0 (the "License");
	you may not use this file except in compliance with the License.
	You may obtain a copy of the License at

		http://www.apache.org/licenses/LICENSE-2.0

	Unless required by applicable law or agreed to in writing, software
	distributed under the License is distributed on an "AS IS" BASIS,
	WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
	See the License for the specific language governing permissions and
	limitations under the License.
*/


#include <fstream>
#include <iostream>
#include <array>
#include <string>
#include <cstdint>
#include <stdlib.h>
#include "glad/glad.h"
#include "GLFW/glfw3.h"
#include "lodepng.h"


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


struct ImageData
{
	unsigned Width;
	unsigned Height;
	std::vector<unsigned char> Data;
};


ImageData ReadPng(const char* Path)
{
	ImageData Image;
	std::vector<unsigned char> Data;
	unsigned Error = lodepng::decode(Data, Image.Width, Image.Height, Path);
	if (Error)
	{
		std::cout \
			<< "Failed to read " << Path << "!\n"
			<< " - Reason: PNG decode error:\n"
			<< " - [" << Error << "] " << lodepng_error_text(Error) << "\n";
		HaltAndCatchFire();
	}
	Image.Data.resize(Data.size());
	int Dst = 0;
	const int RowSize = Image.Width * 4;
	for (int y = Image.Height - 1; y >= 0; --y)
	{
		int Src = RowSize * y;
		for (int x = 0; x < RowSize; ++x)
		{
			Image.Data[Dst] = Data[Src];
			++Dst;
			++Src;
		}
	}
	return Image;
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
void GlfwErrorCallback(int Error, const char* Description)
{
	std::cout << "GLFW Error: " << Description << '\n';
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
	if (Type == GL_DEBUG_TYPE_PUSH_GROUP || Type == GL_DEBUG_TYPE_POP_GROUP)
	{
		return;
	}
	std::cout << "OpenGL Debug Callback - ";
	std::cout << "Source: ";
	switch (Source)
	{
	case GL_DEBUG_SOURCE_API:
		std::cout << "API";
		break;
	case GL_DEBUG_SOURCE_WINDOW_SYSTEM:
		std::cout << "Window System";
		break;
	case GL_DEBUG_SOURCE_SHADER_COMPILER:
		std::cout << "Shader Compiler";
		break;
	case GL_DEBUG_SOURCE_THIRD_PARTY:
		std::cout << "Third Party";
		break;
	case GL_DEBUG_SOURCE_APPLICATION:
		std::cout << "You!";
		break;
	default:
		std::cout << "Other";
	}

	std::cout << ", Type: ";
	switch (Type)
	{
	case GL_DEBUG_TYPE_ERROR:
		std::cout << "Error!";
		break;
	case GL_DEBUG_TYPE_DEPRECATED_BEHAVIOR:
		std::cout << "Deprecated Behavior";
		break;
	case GL_DEBUG_TYPE_UNDEFINED_BEHAVIOR:
		std::cout << "Undefined Behavior";
		break;
	case GL_DEBUG_TYPE_PORTABILITY:
		std::cout << "Portability";
		break;
	case GL_DEBUG_TYPE_PERFORMANCE:
		std::cout << "Performance";
		break;
	case GL_DEBUG_TYPE_MARKER:
		std::cout << "Marker";
		break;
	case GL_DEBUG_TYPE_PUSH_GROUP:
		std::cout << "Push";
		break;
	case GL_DEBUG_TYPE_POP_GROUP:
		std::cout << "Pop";
		break;
	default:
		std::cout << "Other";
	}

	std::cout << ", Severity: ";
	switch (Severity)
	{
	case GL_DEBUG_SEVERITY_LOW:
		std::cout << "Low";
		break;
	case GL_DEBUG_SEVERITY_MEDIUM:
		std::cout << "Medium";
		break;
	case GL_DEBUG_SEVERITY_HIGH:
		std::cout << "High";
		break;
	case GL_DEBUG_SEVERITY_NOTIFICATION:
		std::cout << "Notification";
		break;
	default:
		std::cout << "Unknown?";
	}
	std::cout << "\n\tMessage: " << ErrorMessage << "\n\n";
}
#endif // DEBUG_BUILD


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
}


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
}
