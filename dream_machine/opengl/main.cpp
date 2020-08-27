#include "dream_machine.hpp"


namespace Glsl
{
「structs」
}


const char* WindowTitle = "「window_title」";
int ScreenWidth = 「window_width」;
int ScreenHeight = 「window_height」;
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
	「user_vars」
}


「globals」


namespace Upload
{
「uploaders」
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
	SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 「hint_version_major」);
	SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 「hint_version_minor」);
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
