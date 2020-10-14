
#define SDL_MAIN_HANDLED
#include <SDL.h>


extern int CurrentRenderer;


extern void UserSetupCallback(SDL_Window* Window)
{
}


extern void UserFrameCallback(unsigned int FrameIndex, double StartTime, double DeltaTime)
{
	const Uint8* KeyboardState = SDL_GetKeyboardState(nullptr);

	if (KeyboardState[SDL_SCANCODE_1])
	{
		CurrentRenderer = 0;
	}
	else if (KeyboardState[SDL_SCANCODE_2])
	{
		CurrentRenderer = 1;
	}
}
