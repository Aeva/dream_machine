#include <string>
#include <iostream>
#include "generated.h"


namespace 「structs_namespace」
{
「struct_definitions」
}


const char* WindowTitle = "「window_title」";
int ScreenWidth = 「window_width」;
int ScreenHeight = 「window_height」;
float ScreenScaleX = 1.0;
float ScreenScaleY = 1.0;
bool WindowIsDirty = true;
SDL_Window* Window;


extern int CurrentRenderer = 0;
extern void UserSetupCallback(SDL_Window* Window);
extern void UserFrameCallback();


「globals」


namespace Upload
{
「uploader_definitions」
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


void WindowResized()
{
「resize_hook」
}


int main()
{
	SDL_SetMainReady();
	if (SDL_Init(SDL_INIT_VIDEO) != 0)
	{
		std::cout << "Fatal Error: SDL failed to initialize: " << SDL_GetError() << std::endl;
		return 1;
	}

	「after_sdl_init」

	Window = SDL_CreateWindow(WindowTitle, SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, ScreenWidth, ScreenHeight, SDL_WINDOW_RESIZABLE「sdl_window_flags」);
	if (!Window)
	{
		std::cout << "Fatal Error: SDL failed to create a window: " << SDL_GetError() << std::endl;
		SDL_Quit();
		return 1;
	}

	「after_sdl_window」

	InitialSetup();
	UserSetupCallback(Window);

	while (!SDL_QuitRequested())
	{
		UpdateWindowSize();
		if (WindowIsDirty)
		{
			WindowResized();
			WindowIsDirty = false;
			「set_viewport」
		}
		static int FrameIndex = 0;
		static unsigned int DeltaTime = 0.0;
		static unsigned int StartTime = SDL_GetTicks();
		{
			DrawFrame(FrameIndex++, (double)StartTime / 1000.0, (double)DeltaTime / 1000.0);
			「present」
			SDL_PumpEvents();
			UserFrameCallback();
		}
		unsigned int EndTime = SDL_GetTicks();
		DeltaTime = EndTime - StartTime;
		StartTime = EndTime;
	}

	「teardown」
	SDL_DestroyWindow(Window);
	SDL_Quit();
	return 0;
}
