
#define SDL_MAIN_HANDLED
#include <SDL.h>
#include "generated.h"


extern int CurrentRenderer;


extern void UserSetupCallback(SDL_Window* Window)
{
}


extern void UserFrameCallback(unsigned int FrameIndex, double CurrentTime, double DeltaTime)
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


	WindowParams Screen = GetWindowInfo();
	Glsl::WindowParamsType Data = \
	{
		{
			(float)(Screen.Width),
			(float)(Screen.Height),
			1.0f / (float)(Screen.Width),
			1.0f / (float)(Screen.Height),
		},
		{
			Screen.ScaleX,
			Screen.ScaleY,
			1.0f / Screen.ScaleX,
			1.0f / Screen.ScaleY,
		},
		(float)(CurrentTime),
	};
	Upload::WindowParams(Data);
}
