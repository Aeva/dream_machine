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
SDL_Window* Window;
SDL_GLContext GLContext;


extern int CurrentRenderer = 0;
extern void UserSetupCallback(SDL_Window* Window);
extern void UserFrameCallback();


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
		std::string ShaderSource = DecodeBase64("I3ZlcnNpb24gNDIwCgovKgoJQ29weXJpZ2h0IDIwMjAgQWV2YSBQYWxlY2VrCgoJTGljZW5zZWQgdW5kZXIgdGhlIEFwYWNoZSBMaWNlbnNlLCBWZXJzaW9uIDIuMCAodGhlICJMaWNlbnNlIik7Cgl5b3UgbWF5IG5vdCB1c2UgdGhpcyBmaWxlIGV4Y2VwdCBpbiBjb21wbGlhbmNlIHdpdGggdGhlIExpY2Vuc2UuCglZb3UgbWF5IG9idGFpbiBhIGNvcHkgb2YgdGhlIExpY2Vuc2UgYXQKCgkJaHR0cDovL3d3dy5hcGFjaGUub3JnL2xpY2Vuc2VzL0xJQ0VOU0UtMi4wCgoJVW5sZXNzIHJlcXVpcmVkIGJ5IGFwcGxpY2FibGUgbGF3IG9yIGFncmVlZCB0byBpbiB3cml0aW5nLCBzb2Z0d2FyZQoJZGlzdHJpYnV0ZWQgdW5kZXIgdGhlIExpY2Vuc2UgaXMgZGlzdHJpYnV0ZWQgb24gYW4gIkFTIElTIiBCQVNJUywKCVdJVEhPVVQgV0FSUkFOVElFUyBPUiBDT05ESVRJT05TIE9GIEFOWSBLSU5ELCBlaXRoZXIgZXhwcmVzcyBvciBpbXBsaWVkLgoJU2VlIHRoZSBMaWNlbnNlIGZvciB0aGUgc3BlY2lmaWMgbGFuZ3VhZ2UgZ292ZXJuaW5nIHBlcm1pc3Npb25zIGFuZAoJbGltaXRhdGlvbnMgdW5kZXIgdGhlIExpY2Vuc2UuCiovCgpsYXlvdXQoc3RkMTQwLCBiaW5kaW5nID0gMCkKdW5pZm9ybSBXaW5kb3dQYXJhbXMKewoJdmVjNCBXaW5kb3dTaXplOwoJdmVjNCBXaW5kb3dTY2FsZTsKCWZsb2F0IEVsYXBzZWRUaW1lOwp9OwpsYXlvdXQoYmluZGluZyA9IDApCnVuaWZvcm0gc2FtcGxlcjJEIEFjY3VtdWxhdG9yOwoKCnZvaWQgbWFpbigpCnsKCWdsX1Bvc2l0aW9uID0gdmVjNCgtMS4wICsgZmxvYXQoKGdsX1ZlcnRleElEICYgMSkgPDwgMiksIC0xLjAgKyBmbG9hdCgoZ2xfVmVydGV4SUQgJiAyKSA8PCAxKSwgMCwgMSk7Cn0K");
		Shaders[0] = CompileShader(ShaderSource, GL_VERTEX_SHADER);
	}
	{
		std::string ShaderSource = DecodeBase64("I3ZlcnNpb24gNDIwCgovKgoJQ29weXJpZ2h0IDIwMjAgQWV2YSBQYWxlY2VrCgoJTGljZW5zZWQgdW5kZXIgdGhlIEFwYWNoZSBMaWNlbnNlLCBWZXJzaW9uIDIuMCAodGhlICJMaWNlbnNlIik7Cgl5b3UgbWF5IG5vdCB1c2UgdGhpcyBmaWxlIGV4Y2VwdCBpbiBjb21wbGlhbmNlIHdpdGggdGhlIExpY2Vuc2UuCglZb3UgbWF5IG9idGFpbiBhIGNvcHkgb2YgdGhlIExpY2Vuc2UgYXQKCgkJaHR0cDovL3d3dy5hcGFjaGUub3JnL2xpY2Vuc2VzL0xJQ0VOU0UtMi4wCgoJVW5sZXNzIHJlcXVpcmVkIGJ5IGFwcGxpY2FibGUgbGF3IG9yIGFncmVlZCB0byBpbiB3cml0aW5nLCBzb2Z0d2FyZQoJZGlzdHJpYnV0ZWQgdW5kZXIgdGhlIExpY2Vuc2UgaXMgZGlzdHJpYnV0ZWQgb24gYW4gIkFTIElTIiBCQVNJUywKCVdJVEhPVVQgV0FSUkFOVElFUyBPUiBDT05ESVRJT05TIE9GIEFOWSBLSU5ELCBlaXRoZXIgZXhwcmVzcyBvciBpbXBsaWVkLgoJU2VlIHRoZSBMaWNlbnNlIGZvciB0aGUgc3BlY2lmaWMgbGFuZ3VhZ2UgZ292ZXJuaW5nIHBlcm1pc3Npb25zIGFuZAoJbGltaXRhdGlvbnMgdW5kZXIgdGhlIExpY2Vuc2UuCiovCgpsYXlvdXQoc3RkMTQwLCBiaW5kaW5nID0gMCkKdW5pZm9ybSBXaW5kb3dQYXJhbXMKewoJdmVjNCBXaW5kb3dTaXplOwoJdmVjNCBXaW5kb3dTY2FsZTsKCWZsb2F0IEVsYXBzZWRUaW1lOwp9OwpsYXlvdXQoYmluZGluZyA9IDApCnVuaWZvcm0gc2FtcGxlcjJEIEFjY3VtdWxhdG9yOwpsYXlvdXQobG9jYXRpb24gPSAwKQogb3V0IHZlYzQgQWNjdW11bGF0b3JUYXJnZXQ7CgoKY29uc3QgdmVjNCBNaXNzQ29sb3IgPSB2ZWM0KDAuNSwgMC41LCAwLjUsIDEuMCk7CmNvbnN0IGZsb2F0IEFsbW9zdFplcm8gPSAwLjAwMTsKCgpmbG9hdCBTcGhlcmUodmVjMyBMb2NhbCwgZmxvYXQgUmFkaXVzKQp7CglyZXR1cm4gbGVuZ3RoKExvY2FsKSAtIFJhZGl1czsKfQoKCmZsb2F0IEJveCh2ZWMzIExvY2FsLCB2ZWMzIEJvdW5kcykKewoJdmVjMyBEaXN0ID0gYWJzKExvY2FsKSAtIEJvdW5kczsKCXJldHVybiBsZW5ndGgobWF4KERpc3QsIDAuMCkpICsgbWluKG1heChEaXN0LngsIG1heChEaXN0LnksIERpc3QueikpLCAwLjApOwp9CgoKZmxvYXQgU3BodWJlKHZlYzMgTG9jYWwsIGZsb2F0IEFscGhhKQp7CglyZXR1cm4gbWl4KFNwaGVyZShMb2NhbCwgMS4wKSwgQm94KExvY2FsLCB2ZWMzKDEuMCkpLCBBbHBoYSk7Cn0KCgpmbG9hdCBHbG9vcCh2ZWMzIFBvaW50LCBmbG9hdCBTY2FsZSkKewoJcmV0dXJuIHNpbihTY2FsZSAqIFBvaW50LngpICogc2luKFNjYWxlICogUG9pbnQueSkgKiBzaW4oU2NhbGUgKiBQb2ludC56KTsKfQoKCmZsb2F0IFVuaW9uKGZsb2F0IExIUywgZmxvYXQgUkhTKQp7CglyZXR1cm4gbWluKExIUywgUkhTKTsKfQoKCmZsb2F0IFN1YnRyYWN0KGZsb2F0IExIUywgZmxvYXQgUkhTKQp7CglyZXR1cm4gbWF4KExIUywgLVJIUyk7Cn0KCgpmbG9hdCBJbnRlcnNlY3Rpb24oZmxvYXQgTEhTLCBmbG9hdCBSSFMpCnsKCXJldHVybiBtYXgoTEhTLCBSSFMpOwp9CgoKdmVjMyBUd2lzdCh2ZWMzIFBvaW50LCBmbG9hdCBJbnRlbnNpdHkpCnsKCWZsb2F0IEMgPSBjb3MoSW50ZW5zaXR5ICogUG9pbnQueik7CglmbG9hdCBTID0gc2luKEludGVuc2l0eSAqIFBvaW50LnopOwoJbWF0MiAgTSA9IG1hdDIoQywgLVMsIFMsIEMpOwoJcmV0dXJuIHZlYzMoTSAqIFBvaW50Lnh5LCBQb2ludC56KTsKfQoKCmZsb2F0IE9kZFNoYXBlKHZlYzMgTG9jYWwpCnsKCXZlYzMgQm94TG9jYWwgPSBMb2NhbDsKCWNvbnN0IGZsb2F0IFJlcGVhdCA9IDAuNTsKCUJveExvY2FsLnogPSBtb2QoQm94TG9jYWwueiArIDAuNSAqIFJlcGVhdCwgUmVwZWF0KSAtIDAuNSAqIFJlcGVhdDsKCUxvY2FsID0gVHdpc3QoTG9jYWwsIGxlbmd0aChMb2NhbC54eSkgKiA1LjApOwoJZmxvYXQgRGlzdCA9IFNwaHViZShMb2NhbCwgMC41KTsKCURpc3QgPSBJbnRlcnNlY3Rpb24oRGlzdCwgR2xvb3AoTG9jYWwsIDEwLjApKTsKCURpc3QgPSBTdWJ0cmFjdChEaXN0LCBCb3goQm94TG9jYWwsIHZlYzMoMi4wLCAyLjAsIFJlcGVhdCAqIDAuMykpKTsKCXJldHVybiBEaXN0Owp9CgoKZmxvYXQgU2NlbmVTREYodmVjMyBWaWV3KQp7CglmbG9hdCBTaGFwZSA9IE9kZFNoYXBlKFZpZXcgLSB2ZWMzKDAuMCwgMy4wLCAwLjApKTsKCXJldHVybiBTaGFwZTsKfQoKCnZlYzMgR2V0UmF5RGlyKHZlYzIgRnJhZ0Nvb3JkLCBmbG9hdCBGT1YpCnsKCWZsb2F0IEFzcGVjdCA9IFdpbmRvd1NpemUueSAqIFdpbmRvd1NpemUuejsKCXZlYzIgTkRDID0gRnJhZ0Nvb3JkICogV2luZG93U2l6ZS56dyAqIDIuMCAtIDEuMDsKCXZlYzIgQW5nbGUgPSBOREMgKiB2ZWMyKEZPViwgRk9WICogQXNwZWN0KSAqIDAuNTsKCXZlYzMgUmF5RGlyID0gdmVjMyhzaW4ocmFkaWFucyhBbmdsZSkpLCAwLjApLnh6eTsKCVJheURpci55ID0gc3FydCgxLjAgLSAoUmF5RGlyLnggKiBSYXlEaXIueCkgLSAoUmF5RGlyLnogKiBSYXlEaXIueikpOwoJcmV0dXJuIFJheURpcjsKfQoKCmJvb2wgUmF5TWFyY2godmVjMyBSYXlEaXIsIGZsb2F0IFRyYXZlbFN0YXJ0LCBvdXQgdmVjNCBQb3NpdGlvbikKewoJUG9zaXRpb24udyA9IFRyYXZlbFN0YXJ0OwoJYm9vbCBiSGl0ID0gZmFsc2U7CgkvL2ZvciAoaW50IGk9MDsgaTwxMDsgKytpKQoJewoJCVBvc2l0aW9uLnh5eiA9IFJheURpciAqIFBvc2l0aW9uLnc7CgkJZmxvYXQgRGlzdCA9IFNjZW5lU0RGKFBvc2l0aW9uLnh5eik7CgkJaWYgKERpc3QgPiAwLjApCgkJewoJCQlQb3NpdGlvbi53ICs9IERpc3Q7CgkJfQoJfQoJcmV0dXJuIGRpc3RhbmNlKFBvc2l0aW9uLncsIFRyYXZlbFN0YXJ0KSA8IEFsbW9zdFplcm87Cn0KCgp2ZWMzIEdyYWRpZW50KHZlYzMgUG9zaXRpb24pCnsKCWZsb2F0IERpc3QgPSBTY2VuZVNERihQb3NpdGlvbik7CglyZXR1cm4gbm9ybWFsaXplKHZlYzMoCgkJU2NlbmVTREYodmVjMyhQb3NpdGlvbi54ICsgQWxtb3N0WmVybywgUG9zaXRpb24ueSwgUG9zaXRpb24ueikpIC0gRGlzdCwKCQlTY2VuZVNERih2ZWMzKFBvc2l0aW9uLngsIFBvc2l0aW9uLnkgKyBBbG1vc3RaZXJvLCBQb3NpdGlvbi56KSkgLSBEaXN0LAoJCVNjZW5lU0RGKHZlYzMoUG9zaXRpb24ueCwgUG9zaXRpb24ueSwgUG9zaXRpb24ueiArIEFsbW9zdFplcm8pKSAtIERpc3QpKTsKfQoKCnZvaWQgbWFpbigpCnsKCXZlYzIgVVYgPSBnbF9GcmFnQ29vcmQueHkgKiBXaW5kb3dTaXplLnp3OwoJZmxvYXQgTGFzdCA9IHRleHR1cmUoQWNjdW11bGF0b3IsIFVWKS53OwoKCXZlYzMgUmF5RGlyID0gR2V0UmF5RGlyKGdsX0ZyYWdDb29yZC54eSwgNDUuMCk7Cgl2ZWM0IFBvc2l0aW9uOwoJaWYgKExhc3QgPCAxMDAwLjAgJiYgUmF5TWFyY2goUmF5RGlyLCBMYXN0LCBQb3NpdGlvbikpCgl7CgkJdmVjMyBOb3JtYWwgPSBHcmFkaWVudChQb3NpdGlvbi54eXopOwoJCUFjY3VtdWxhdG9yVGFyZ2V0ID0gdmVjNChOb3JtYWwsIFBvc2l0aW9uLncpOwoJfQoJZWxzZQoJewoJCUFjY3VtdWxhdG9yVGFyZ2V0ID0gdmVjNChNaXNzQ29sb3IueHl6LCBQb3NpdGlvbi53KTsKCX0KfQo=");
		Shaders[1] = CompileShader(ShaderSource, GL_FRAGMENT_SHADER);
	}
	{
		std::string ShaderSource = DecodeBase64("I3ZlcnNpb24gNDIwCgovKgoJQ29weXJpZ2h0IDIwMjAgQWV2YSBQYWxlY2VrCgoJTGljZW5zZWQgdW5kZXIgdGhlIEFwYWNoZSBMaWNlbnNlLCBWZXJzaW9uIDIuMCAodGhlICJMaWNlbnNlIik7Cgl5b3UgbWF5IG5vdCB1c2UgdGhpcyBmaWxlIGV4Y2VwdCBpbiBjb21wbGlhbmNlIHdpdGggdGhlIExpY2Vuc2UuCglZb3UgbWF5IG9idGFpbiBhIGNvcHkgb2YgdGhlIExpY2Vuc2UgYXQKCgkJaHR0cDovL3d3dy5hcGFjaGUub3JnL2xpY2Vuc2VzL0xJQ0VOU0UtMi4wCgoJVW5sZXNzIHJlcXVpcmVkIGJ5IGFwcGxpY2FibGUgbGF3IG9yIGFncmVlZCB0byBpbiB3cml0aW5nLCBzb2Z0d2FyZQoJZGlzdHJpYnV0ZWQgdW5kZXIgdGhlIExpY2Vuc2UgaXMgZGlzdHJpYnV0ZWQgb24gYW4gIkFTIElTIiBCQVNJUywKCVdJVEhPVVQgV0FSUkFOVElFUyBPUiBDT05ESVRJT05TIE9GIEFOWSBLSU5ELCBlaXRoZXIgZXhwcmVzcyBvciBpbXBsaWVkLgoJU2VlIHRoZSBMaWNlbnNlIGZvciB0aGUgc3BlY2lmaWMgbGFuZ3VhZ2UgZ292ZXJuaW5nIHBlcm1pc3Npb25zIGFuZAoJbGltaXRhdGlvbnMgdW5kZXIgdGhlIExpY2Vuc2UuCiovCgpsYXlvdXQoc3RkMTQwLCBiaW5kaW5nID0gMCkKdW5pZm9ybSBXaW5kb3dQYXJhbXMKewoJdmVjNCBXaW5kb3dTaXplOwoJdmVjNCBXaW5kb3dTY2FsZTsKCWZsb2F0IEVsYXBzZWRUaW1lOwp9OwpsYXlvdXQoYmluZGluZyA9IDApCnVuaWZvcm0gc2FtcGxlcjJEIEFjY3VtdWxhdG9yOwpsYXlvdXQobG9jYXRpb24gPSAwKQogb3V0IHZlYzQgT3V0Q29sb3I7CgoKdm9pZCBtYWluKCkKewoJdmVjMiBVViA9IGdsX0ZyYWdDb29yZC54eSAqIFdpbmRvd1NpemUuenc7Cgl2ZWM0IEFjY3VtdWxhdGVkID0gdGV4dHVyZShBY2N1bXVsYXRvciwgVVYpOwoJT3V0Q29sb3IgPSB2ZWM0KEFjY3VtdWxhdGVkLnh5eiwgMS4wKTsKfQo=");
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
		const float ClearColor[] = {0.0, 0.0, 0.0, 1.0};
		glClearTexImage(TextureHandles[0], 0, GL_RGBA32F, GL_FLOAT, &ClearColor[0]);
	}
	{
		// texture "AccumulatorTarget"
		glCreateTextures(GL_TEXTURE_2D, 1, &TextureHandles[1]);
		glTextureStorage2D(TextureHandles[1], 1, GL_RGBA32F, (GLsizei)ScreenWidth, (GLsizei)ScreenHeight);
		glObjectLabel(GL_TEXTURE, TextureHandles[1], -1, "AccumulatorTarget");
	}
	{
		const float ClearColor[] = {0.0, 0.0, 0.0, 1.0};
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
		const float ClearColor[] = {0.0, 0.0, 0.0, 1.0};
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
		const float ClearColor[] = {0.0, 0.0, 0.0, 1.0};
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

	SDL_SetMainReady();
	if(SDL_Init(SDL_INIT_VIDEO) != 0)
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
	if(!Window)
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
		std::cout << "Failed to initialize GLAD!\n";
		SDL_GL_DeleteContext(GLContext);
		SDL_DestroyWindow(Window);
		SDL_Quit();
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

	while (!SDL_QuitRequested())
	{
		UpdateWindowSize();
		if (WindowIsDirty)
		{
			WindowResized();
			WindowIsDirty = false;
		}
		glViewport(0, 0, ScreenWidth, ScreenHeight);
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

	SDL_GL_DeleteContext(GLContext);
	SDL_DestroyWindow(Window);
	SDL_Quit();
	return 0;
}
