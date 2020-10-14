
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


#include "glad.h"
#define SDL_MAIN_HANDLED
#include <SDL.h>
#include "common.h"
#include "opengl_util.h"
#include "images.h"


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


namespace UserVars
{

}


namespace Upload
{
	void WindowParams(Glsl::WindowParamsType& Data);
}
