#include <string>
#include <iostream>
#include "generated.h"


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
		float SomeArray[10];
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
SDL_Window* Window;


extern int CurrentRenderer = 0;
extern void UserSetupCallback(SDL_Window* Window);
extern void UserFrameCallback();


SDL_GLContext GLContext;
GLuint Shaders[7] = { 0 };
GLuint ShaderPrograms[4] = { 0 };
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
		Reflow< vec4>(Mapped, 0, Data.Whatever[0]);
		Reflow< vec4>(Mapped, 4, Data.Whatever[1]);
		Reflow< vec4>(Mapped, 8, Data.Whatever[2]);
		Reflow< vec4>(Mapped, 12, Data.Whatever[3]);
		Reflow<float>(Mapped, 16, Data.SomeArray[0]);
		Reflow<float>(Mapped, 20, Data.SomeArray[1]);
		Reflow<float>(Mapped, 24, Data.SomeArray[2]);
		Reflow<float>(Mapped, 28, Data.SomeArray[3]);
		Reflow<float>(Mapped, 32, Data.SomeArray[4]);
		Reflow<float>(Mapped, 36, Data.SomeArray[5]);
		Reflow<float>(Mapped, 40, Data.SomeArray[6]);
		Reflow<float>(Mapped, 44, Data.SomeArray[7]);
		Reflow<float>(Mapped, 48, Data.SomeArray[8]);
		Reflow<float>(Mapped, 52, Data.SomeArray[9]);
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
		Reflow< vec4>(Mapped, 0, Data.Moop.Whatever[0]);
		Reflow< vec4>(Mapped, 4, Data.Moop.Whatever[1]);
		Reflow< vec4>(Mapped, 8, Data.Moop.Whatever[2]);
		Reflow< vec4>(Mapped, 12, Data.Moop.Whatever[3]);
		Reflow<float>(Mapped, 16, Data.Moop.SomeArray[0]);
		Reflow<float>(Mapped, 20, Data.Moop.SomeArray[1]);
		Reflow<float>(Mapped, 24, Data.Moop.SomeArray[2]);
		Reflow<float>(Mapped, 28, Data.Moop.SomeArray[3]);
		Reflow<float>(Mapped, 32, Data.Moop.SomeArray[4]);
		Reflow<float>(Mapped, 36, Data.Moop.SomeArray[5]);
		Reflow<float>(Mapped, 40, Data.Moop.SomeArray[6]);
		Reflow<float>(Mapped, 44, Data.Moop.SomeArray[7]);
		Reflow<float>(Mapped, 48, Data.Moop.SomeArray[8]);
		Reflow<float>(Mapped, 52, Data.Moop.SomeArray[9]);
		glUnmapNamedBuffer(Handle);
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
		std::string ShaderSource = DecodeBase64("I3ZlcnNpb24gNDIwCgovKgoJQ29weXJpZ2h0IDIwMjAgQWV2YSBQYWxlY2VrCgoJTGljZW5zZWQgdW5kZXIgdGhlIEFwYWNoZSBMaWNlbnNlLCBWZXJzaW9uIDIuMCAodGhlICJMaWNlbnNlIik7Cgl5b3UgbWF5IG5vdCB1c2UgdGhpcyBmaWxlIGV4Y2VwdCBpbiBjb21wbGlhbmNlIHdpdGggdGhlIExpY2Vuc2UuCglZb3UgbWF5IG9idGFpbiBhIGNvcHkgb2YgdGhlIExpY2Vuc2UgYXQKCgkJaHR0cDovL3d3dy5hcGFjaGUub3JnL2xpY2Vuc2VzL0xJQ0VOU0UtMi4wCgoJVW5sZXNzIHJlcXVpcmVkIGJ5IGFwcGxpY2FibGUgbGF3IG9yIGFncmVlZCB0byBpbiB3cml0aW5nLCBzb2Z0d2FyZQoJZGlzdHJpYnV0ZWQgdW5kZXIgdGhlIExpY2Vuc2UgaXMgZGlzdHJpYnV0ZWQgb24gYW4gIkFTIElTIiBCQVNJUywKCVdJVEhPVVQgV0FSUkFOVElFUyBPUiBDT05ESVRJT05TIE9GIEFOWSBLSU5ELCBlaXRoZXIgZXhwcmVzcyBvciBpbXBsaWVkLgoJU2VlIHRoZSBMaWNlbnNlIGZvciB0aGUgc3BlY2lmaWMgbGFuZ3VhZ2UgZ292ZXJuaW5nIHBlcm1pc3Npb25zIGFuZAoJbGltaXRhdGlvbnMgdW5kZXIgdGhlIExpY2Vuc2UuCiovCgpzdHJ1Y3QgU29tZVR5cGUKewoJbWF0NCBXaGF0ZXZlcjsKCWZsb2F0IFNvbWVBcnJheVsxMF07Cn07CmxheW91dChzdGQxNDAsIGJpbmRpbmcgPSAwKQp1bmlmb3JtIFdpbmRvd1BhcmFtcwp7Cgl2ZWM0IFdpbmRvd1NpemU7Cgl2ZWM0IFdpbmRvd1NjYWxlOwoJZmxvYXQgRWxhcHNlZFRpbWU7Cn07CmxheW91dChiaW5kaW5nID0gMCkKdW5pZm9ybSBzYW1wbGVyMkQgRmFuY3lUZXh0dXJlOwoKCnZvaWQgbWFpbigpCnsKCWdsX1Bvc2l0aW9uID0gdmVjNCgtMS4wICsgZmxvYXQoKGdsX1ZlcnRleElEICYgMSkgPDwgMiksIC0xLjAgKyBmbG9hdCgoZ2xfVmVydGV4SUQgJiAyKSA8PCAxKSwgMCwgMSk7Cn0K");
		Shaders[0] = CompileShader(ShaderSource, GL_VERTEX_SHADER);
	}
	{
		std::string ShaderSource = DecodeBase64("I3ZlcnNpb24gNDIwCgovKgoJQ29weXJpZ2h0IDIwMjAgQWV2YSBQYWxlY2VrCgoJTGljZW5zZWQgdW5kZXIgdGhlIEFwYWNoZSBMaWNlbnNlLCBWZXJzaW9uIDIuMCAodGhlICJMaWNlbnNlIik7Cgl5b3UgbWF5IG5vdCB1c2UgdGhpcyBmaWxlIGV4Y2VwdCBpbiBjb21wbGlhbmNlIHdpdGggdGhlIExpY2Vuc2UuCglZb3UgbWF5IG9idGFpbiBhIGNvcHkgb2YgdGhlIExpY2Vuc2UgYXQKCgkJaHR0cDovL3d3dy5hcGFjaGUub3JnL2xpY2Vuc2VzL0xJQ0VOU0UtMi4wCgoJVW5sZXNzIHJlcXVpcmVkIGJ5IGFwcGxpY2FibGUgbGF3IG9yIGFncmVlZCB0byBpbiB3cml0aW5nLCBzb2Z0d2FyZQoJZGlzdHJpYnV0ZWQgdW5kZXIgdGhlIExpY2Vuc2UgaXMgZGlzdHJpYnV0ZWQgb24gYW4gIkFTIElTIiBCQVNJUywKCVdJVEhPVVQgV0FSUkFOVElFUyBPUiBDT05ESVRJT05TIE9GIEFOWSBLSU5ELCBlaXRoZXIgZXhwcmVzcyBvciBpbXBsaWVkLgoJU2VlIHRoZSBMaWNlbnNlIGZvciB0aGUgc3BlY2lmaWMgbGFuZ3VhZ2UgZ292ZXJuaW5nIHBlcm1pc3Npb25zIGFuZAoJbGltaXRhdGlvbnMgdW5kZXIgdGhlIExpY2Vuc2UuCiovCgpzdHJ1Y3QgU29tZVR5cGUKewoJbWF0NCBXaGF0ZXZlcjsKCWZsb2F0IFNvbWVBcnJheVsxMF07Cn07CmxheW91dChzdGQxNDAsIGJpbmRpbmcgPSAwKQp1bmlmb3JtIFdpbmRvd1BhcmFtcwp7Cgl2ZWM0IFdpbmRvd1NpemU7Cgl2ZWM0IFdpbmRvd1NjYWxlOwoJZmxvYXQgRWxhcHNlZFRpbWU7Cn07CmxheW91dChiaW5kaW5nID0gMCkKdW5pZm9ybSBzYW1wbGVyMkQgRmFuY3lUZXh0dXJlOwpsYXlvdXQobG9jYXRpb24gPSAwKQogb3V0IHZlYzQgT3V0Q29sb3I7CgoKdm9pZCBtYWluKCkKewoJdmVjMiBVViA9IGdsX0ZyYWdDb29yZC54eSAqIFdpbmRvd1NpemUuenc7CglVVi54ICs9IHNpbihVVi55ICsgRWxhcHNlZFRpbWUpOwoJVVYueSArPSBjb3MoVVYueCArIEVsYXBzZWRUaW1lKTsKCU91dENvbG9yID0gdGV4dHVyZShGYW5jeVRleHR1cmUsIFVWKTsKfQo=");
		Shaders[1] = CompileShader(ShaderSource, GL_FRAGMENT_SHADER);
	}
	{
		std::string ShaderSource = DecodeBase64("I3ZlcnNpb24gNDIwCgovKgoJQ29weXJpZ2h0IDIwMjAgQWV2YSBQYWxlY2VrCgoJTGljZW5zZWQgdW5kZXIgdGhlIEFwYWNoZSBMaWNlbnNlLCBWZXJzaW9uIDIuMCAodGhlICJMaWNlbnNlIik7Cgl5b3UgbWF5IG5vdCB1c2UgdGhpcyBmaWxlIGV4Y2VwdCBpbiBjb21wbGlhbmNlIHdpdGggdGhlIExpY2Vuc2UuCglZb3UgbWF5IG9idGFpbiBhIGNvcHkgb2YgdGhlIExpY2Vuc2UgYXQKCgkJaHR0cDovL3d3dy5hcGFjaGUub3JnL2xpY2Vuc2VzL0xJQ0VOU0UtMi4wCgoJVW5sZXNzIHJlcXVpcmVkIGJ5IGFwcGxpY2FibGUgbGF3IG9yIGFncmVlZCB0byBpbiB3cml0aW5nLCBzb2Z0d2FyZQoJZGlzdHJpYnV0ZWQgdW5kZXIgdGhlIExpY2Vuc2UgaXMgZGlzdHJpYnV0ZWQgb24gYW4gIkFTIElTIiBCQVNJUywKCVdJVEhPVVQgV0FSUkFOVElFUyBPUiBDT05ESVRJT05TIE9GIEFOWSBLSU5ELCBlaXRoZXIgZXhwcmVzcyBvciBpbXBsaWVkLgoJU2VlIHRoZSBMaWNlbnNlIGZvciB0aGUgc3BlY2lmaWMgbGFuZ3VhZ2UgZ292ZXJuaW5nIHBlcm1pc3Npb25zIGFuZAoJbGltaXRhdGlvbnMgdW5kZXIgdGhlIExpY2Vuc2UuCiovCgpsYXlvdXQoc3RkMTQwLCBiaW5kaW5nID0gMCkKdW5pZm9ybSBXaW5kb3dQYXJhbXMKewoJdmVjNCBXaW5kb3dTaXplOwoJdmVjNCBXaW5kb3dTY2FsZTsKCWZsb2F0IEVsYXBzZWRUaW1lOwp9OwoKCnZvaWQgbWFpbigpCnsKCWdsX1Bvc2l0aW9uID0gdmVjNCgtMS4wICsgZmxvYXQoKGdsX1ZlcnRleElEICYgMSkgPDwgMiksIC0xLjAgKyBmbG9hdCgoZ2xfVmVydGV4SUQgJiAyKSA8PCAxKSwgMCwgMSk7Cn0K");
		Shaders[2] = CompileShader(ShaderSource, GL_VERTEX_SHADER);
	}
	{
		std::string ShaderSource = DecodeBase64("I3ZlcnNpb24gNDIwCgovKgoJQ29weXJpZ2h0IDIwMjAgQWV2YSBQYWxlY2VrCgoJTGljZW5zZWQgdW5kZXIgdGhlIEFwYWNoZSBMaWNlbnNlLCBWZXJzaW9uIDIuMCAodGhlICJMaWNlbnNlIik7Cgl5b3UgbWF5IG5vdCB1c2UgdGhpcyBmaWxlIGV4Y2VwdCBpbiBjb21wbGlhbmNlIHdpdGggdGhlIExpY2Vuc2UuCglZb3UgbWF5IG9idGFpbiBhIGNvcHkgb2YgdGhlIExpY2Vuc2UgYXQKCgkJaHR0cDovL3d3dy5hcGFjaGUub3JnL2xpY2Vuc2VzL0xJQ0VOU0UtMi4wCgoJVW5sZXNzIHJlcXVpcmVkIGJ5IGFwcGxpY2FibGUgbGF3IG9yIGFncmVlZCB0byBpbiB3cml0aW5nLCBzb2Z0d2FyZQoJZGlzdHJpYnV0ZWQgdW5kZXIgdGhlIExpY2Vuc2UgaXMgZGlzdHJpYnV0ZWQgb24gYW4gIkFTIElTIiBCQVNJUywKCVdJVEhPVVQgV0FSUkFOVElFUyBPUiBDT05ESVRJT05TIE9GIEFOWSBLSU5ELCBlaXRoZXIgZXhwcmVzcyBvciBpbXBsaWVkLgoJU2VlIHRoZSBMaWNlbnNlIGZvciB0aGUgc3BlY2lmaWMgbGFuZ3VhZ2UgZ292ZXJuaW5nIHBlcm1pc3Npb25zIGFuZAoJbGltaXRhdGlvbnMgdW5kZXIgdGhlIExpY2Vuc2UuCiovCgpsYXlvdXQoc3RkMTQwLCBiaW5kaW5nID0gMCkKdW5pZm9ybSBXaW5kb3dQYXJhbXMKewoJdmVjNCBXaW5kb3dTaXplOwoJdmVjNCBXaW5kb3dTY2FsZTsKCWZsb2F0IEVsYXBzZWRUaW1lOwp9OwpsYXlvdXQobG9jYXRpb24gPSAwKQogb3V0IHZlYzQgUmVkQ29sb3JUYXJnZXQ7CmxheW91dChsb2NhdGlvbiA9IDEpCiBvdXQgdmVjNCBTb21lRGVwdGhUYXJnZXQ7CgoKdm9pZCBtYWluKCkKewoJY29uc3QgZmxvYXQgQWxwaGEgPSAoZ2xfRnJhZ0Nvb3JkLnggKiBXaW5kb3dTaXplLnopICogKGdsX0ZyYWdDb29yZC55ICogV2luZG93U2l6ZS53KTsKCWNvbnN0IHZlYzMgUmVkMSA9IHZlYzMoMS4wLCAwLjMsIDAuMCk7Cgljb25zdCB2ZWMzIFJlZDIgPSB2ZWMzKDEuMCwgMC4wLCAwLjMpOwoJUmVkQ29sb3JUYXJnZXQgPSB2ZWM0KG1peChSZWQxLCBSZWQyLCBBbHBoYSksIDEuMCk7Cn0K");
		Shaders[3] = CompileShader(ShaderSource, GL_FRAGMENT_SHADER);
	}
	{
		std::string ShaderSource = DecodeBase64("I3ZlcnNpb24gNDIwCgovKgoJQ29weXJpZ2h0IDIwMjAgQWV2YSBQYWxlY2VrCgoJTGljZW5zZWQgdW5kZXIgdGhlIEFwYWNoZSBMaWNlbnNlLCBWZXJzaW9uIDIuMCAodGhlICJMaWNlbnNlIik7Cgl5b3UgbWF5IG5vdCB1c2UgdGhpcyBmaWxlIGV4Y2VwdCBpbiBjb21wbGlhbmNlIHdpdGggdGhlIExpY2Vuc2UuCglZb3UgbWF5IG9idGFpbiBhIGNvcHkgb2YgdGhlIExpY2Vuc2UgYXQKCgkJaHR0cDovL3d3dy5hcGFjaGUub3JnL2xpY2Vuc2VzL0xJQ0VOU0UtMi4wCgoJVW5sZXNzIHJlcXVpcmVkIGJ5IGFwcGxpY2FibGUgbGF3IG9yIGFncmVlZCB0byBpbiB3cml0aW5nLCBzb2Z0d2FyZQoJZGlzdHJpYnV0ZWQgdW5kZXIgdGhlIExpY2Vuc2UgaXMgZGlzdHJpYnV0ZWQgb24gYW4gIkFTIElTIiBCQVNJUywKCVdJVEhPVVQgV0FSUkFOVElFUyBPUiBDT05ESVRJT05TIE9GIEFOWSBLSU5ELCBlaXRoZXIgZXhwcmVzcyBvciBpbXBsaWVkLgoJU2VlIHRoZSBMaWNlbnNlIGZvciB0aGUgc3BlY2lmaWMgbGFuZ3VhZ2UgZ292ZXJuaW5nIHBlcm1pc3Npb25zIGFuZAoJbGltaXRhdGlvbnMgdW5kZXIgdGhlIExpY2Vuc2UuCiovCgpsYXlvdXQoc3RkMTQwLCBiaW5kaW5nID0gMCkKdW5pZm9ybSBXaW5kb3dQYXJhbXMKewoJdmVjNCBXaW5kb3dTaXplOwoJdmVjNCBXaW5kb3dTY2FsZTsKCWZsb2F0IEVsYXBzZWRUaW1lOwp9OwpsYXlvdXQobG9jYXRpb24gPSAwKQogb3V0IHZlYzQgQmx1ZUNvbG9yVGFyZ2V0OwpsYXlvdXQobG9jYXRpb24gPSAxKQogb3V0IHZlYzQgU29tZURlcHRoVGFyZ2V0OwoKCnZvaWQgbWFpbigpCnsKCWNvbnN0IGZsb2F0IEFscGhhID0gKGdsX0ZyYWdDb29yZC54ICogV2luZG93U2l6ZS56KSAqIChnbF9GcmFnQ29vcmQueSAqIFdpbmRvd1NpemUudyk7Cgljb25zdCB2ZWMzIEJsdWUxID0gdmVjMygwLjAsIDAuMywgMS4wKTsKCWNvbnN0IHZlYzMgQmx1ZTIgPSB2ZWMzKDAuMywgMC4wLCAxLjApOwoJQmx1ZUNvbG9yVGFyZ2V0ID0gdmVjNChtaXgoQmx1ZTEsIEJsdWUyLCBBbHBoYSksIDEuMCk7Cn0K");
		Shaders[4] = CompileShader(ShaderSource, GL_FRAGMENT_SHADER);
	}
	{
		std::string ShaderSource = DecodeBase64("I3ZlcnNpb24gNDIwCgovKgoJQ29weXJpZ2h0IDIwMjAgQWV2YSBQYWxlY2VrCgoJTGljZW5zZWQgdW5kZXIgdGhlIEFwYWNoZSBMaWNlbnNlLCBWZXJzaW9uIDIuMCAodGhlICJMaWNlbnNlIik7Cgl5b3UgbWF5IG5vdCB1c2UgdGhpcyBmaWxlIGV4Y2VwdCBpbiBjb21wbGlhbmNlIHdpdGggdGhlIExpY2Vuc2UuCglZb3UgbWF5IG9idGFpbiBhIGNvcHkgb2YgdGhlIExpY2Vuc2UgYXQKCgkJaHR0cDovL3d3dy5hcGFjaGUub3JnL2xpY2Vuc2VzL0xJQ0VOU0UtMi4wCgoJVW5sZXNzIHJlcXVpcmVkIGJ5IGFwcGxpY2FibGUgbGF3IG9yIGFncmVlZCB0byBpbiB3cml0aW5nLCBzb2Z0d2FyZQoJZGlzdHJpYnV0ZWQgdW5kZXIgdGhlIExpY2Vuc2UgaXMgZGlzdHJpYnV0ZWQgb24gYW4gIkFTIElTIiBCQVNJUywKCVdJVEhPVVQgV0FSUkFOVElFUyBPUiBDT05ESVRJT05TIE9GIEFOWSBLSU5ELCBlaXRoZXIgZXhwcmVzcyBvciBpbXBsaWVkLgoJU2VlIHRoZSBMaWNlbnNlIGZvciB0aGUgc3BlY2lmaWMgbGFuZ3VhZ2UgZ292ZXJuaW5nIHBlcm1pc3Npb25zIGFuZAoJbGltaXRhdGlvbnMgdW5kZXIgdGhlIExpY2Vuc2UuCiovCgpsYXlvdXQoc3RkMTQwLCBiaW5kaW5nID0gMCkKdW5pZm9ybSBXaW5kb3dQYXJhbXMKewoJdmVjNCBXaW5kb3dTaXplOwoJdmVjNCBXaW5kb3dTY2FsZTsKCWZsb2F0IEVsYXBzZWRUaW1lOwp9OwpsYXlvdXQoYmluZGluZyA9IDApCnVuaWZvcm0gc2FtcGxlcjJEIFJlZENvbG9yVGFyZ2V0OwpsYXlvdXQoYmluZGluZyA9IDEpCnVuaWZvcm0gc2FtcGxlcjJEIEJsdWVDb2xvclRhcmdldDsKCgp2b2lkIG1haW4oKQp7CglnbF9Qb3NpdGlvbiA9IHZlYzQoLTEuMCArIGZsb2F0KChnbF9WZXJ0ZXhJRCAmIDEpIDw8IDIpLCAtMS4wICsgZmxvYXQoKGdsX1ZlcnRleElEICYgMikgPDwgMSksIDAsIDEpOwp9Cg==");
		Shaders[5] = CompileShader(ShaderSource, GL_VERTEX_SHADER);
	}
	{
		std::string ShaderSource = DecodeBase64("I3ZlcnNpb24gNDIwCgovKgoJQ29weXJpZ2h0IDIwMjAgQWV2YSBQYWxlY2VrCgoJTGljZW5zZWQgdW5kZXIgdGhlIEFwYWNoZSBMaWNlbnNlLCBWZXJzaW9uIDIuMCAodGhlICJMaWNlbnNlIik7Cgl5b3UgbWF5IG5vdCB1c2UgdGhpcyBmaWxlIGV4Y2VwdCBpbiBjb21wbGlhbmNlIHdpdGggdGhlIExpY2Vuc2UuCglZb3UgbWF5IG9idGFpbiBhIGNvcHkgb2YgdGhlIExpY2Vuc2UgYXQKCgkJaHR0cDovL3d3dy5hcGFjaGUub3JnL2xpY2Vuc2VzL0xJQ0VOU0UtMi4wCgoJVW5sZXNzIHJlcXVpcmVkIGJ5IGFwcGxpY2FibGUgbGF3IG9yIGFncmVlZCB0byBpbiB3cml0aW5nLCBzb2Z0d2FyZQoJZGlzdHJpYnV0ZWQgdW5kZXIgdGhlIExpY2Vuc2UgaXMgZGlzdHJpYnV0ZWQgb24gYW4gIkFTIElTIiBCQVNJUywKCVdJVEhPVVQgV0FSUkFOVElFUyBPUiBDT05ESVRJT05TIE9GIEFOWSBLSU5ELCBlaXRoZXIgZXhwcmVzcyBvciBpbXBsaWVkLgoJU2VlIHRoZSBMaWNlbnNlIGZvciB0aGUgc3BlY2lmaWMgbGFuZ3VhZ2UgZ292ZXJuaW5nIHBlcm1pc3Npb25zIGFuZAoJbGltaXRhdGlvbnMgdW5kZXIgdGhlIExpY2Vuc2UuCiovCgpsYXlvdXQoc3RkMTQwLCBiaW5kaW5nID0gMCkKdW5pZm9ybSBXaW5kb3dQYXJhbXMKewoJdmVjNCBXaW5kb3dTaXplOwoJdmVjNCBXaW5kb3dTY2FsZTsKCWZsb2F0IEVsYXBzZWRUaW1lOwp9OwpsYXlvdXQoYmluZGluZyA9IDApCnVuaWZvcm0gc2FtcGxlcjJEIFJlZENvbG9yVGFyZ2V0OwpsYXlvdXQoYmluZGluZyA9IDEpCnVuaWZvcm0gc2FtcGxlcjJEIEJsdWVDb2xvclRhcmdldDsKbGF5b3V0KGxvY2F0aW9uID0gMCkKIG91dCB2ZWM0IE91dENvbG9yOwoKCmZsb2F0IEdyaWRGaXgoZmxvYXQgQ29vcmQpCnsKCWlmIChDb29yZCA8IDAuMCkKCXsKCQlDb29yZCA9IDEuMCAtIGZyYWN0KGFicyhDb29yZCkpOwoJfQoJaWYgKENvb3JkID4gMS4wKQoJewoJCUNvb3JkID0gZnJhY3QoQ29vcmQpOwoJfQoJcmV0dXJuIENvb3JkOwp9CgoKdmVjMiBHcmlkVVYodmVjMiBVVikKewoJcmV0dXJuIHZlYzIoR3JpZEZpeChVVi54KSwgR3JpZEZpeChVVi55KSk7Cn0KCgp2b2lkIG1haW4oKQp7Cgl2ZWMyIFVWID0gZ2xfRnJhZ0Nvb3JkLnh5ICogV2luZG93U2l6ZS56dzsKCVVWLnggKz0gc2luKFVWLnkgKyBFbGFwc2VkVGltZSk7CglVVi55ICs9IGNvcyhVVi54ICsgRWxhcHNlZFRpbWUpOwoJaXZlYzIgVGlsZSA9IGl2ZWMyKEdyaWRVVihVVikgKiBXaW5kb3dTaXplLnh5KSAvIDMyOwoJdmVjMyBSZWQgPSB0ZXh0dXJlKFJlZENvbG9yVGFyZ2V0LCBVVikucmdiOwoJdmVjMyBCbHVlID0gdGV4dHVyZShCbHVlQ29sb3JUYXJnZXQsIFVWKS5yZ2I7CglmbG9hdCBBbHBoYTsKCWlmIChUaWxlLnggJSAyID09IFRpbGUueSAlIDIpCgl7CgkJQWxwaGEgPSBzaW4oRWxhcHNlZFRpbWUgKiA5LjApICogMC41ICsgMC41OwoJfQoJZWxzZQoJewoJCUFscGhhID0gc2luKEVsYXBzZWRUaW1lICogOS4wICsgMS41KSAqIDAuNSArIDAuNTsKCX0KCU91dENvbG9yID0gdmVjNChtaXgoUmVkLCBCbHVlLCBBbHBoYSksIDEuMCk7Cn0K");
		Shaders[6] = CompileShader(ShaderSource, GL_FRAGMENT_SHADER);
	}
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
		glNamedFramebufferTexture(FrameBufferHandles[1], GL_COLOR_ATTACHMENT0, TextureHandles[1], 0);
		glNamedFramebufferTexture(FrameBufferHandles[1], GL_COLOR_ATTACHMENT1, TextureHandles[3], 0);
		glObjectLabel(GL_FRAMEBUFFER, FrameBufferHandles[1], -1, "SplatRed");
	}
	{
		// recreate framebuffer "SplatBlue"
		glNamedFramebufferTexture(FrameBufferHandles[2], GL_COLOR_ATTACHMENT0, TextureHandles[2], 0);
		glNamedFramebufferTexture(FrameBufferHandles[2], GL_COLOR_ATTACHMENT1, TextureHandles[3], 0);
		glObjectLabel(GL_FRAMEBUFFER, FrameBufferHandles[2], -1, "SplatBlue");
	}
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
		UpdateWindowSize();
		if (WindowIsDirty)
		{
			WindowResized();
			WindowIsDirty = false;
			glViewport(0, 0, ScreenWidth, ScreenHeight);
		}
		static int FrameIndex = 0;
		static unsigned int DeltaTime = 0.0;
		static unsigned int StartTime = SDL_GetTicks();
		{
			DrawFrame(FrameIndex++, (double)StartTime / 1000.0, (double)DeltaTime / 1000.0);
			SDL_GL_SwapWindow(Window);
			SDL_PumpEvents();
			UserFrameCallback();
		}
		unsigned int EndTime = SDL_GetTicks();
		DeltaTime = EndTime - StartTime;
		StartTime = EndTime;
	}

	
	SDL_DestroyWindow(Window);
	SDL_Quit();
	return 0;
}
