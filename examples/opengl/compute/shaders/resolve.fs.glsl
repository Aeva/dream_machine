#version 420
#extension GL_ARB_shader_image_load_store : require

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

「interfaces」

void main()
{
	ivec2 Pixel = ivec2(floor(gl_FragCoord.xy));
	OutColor = imageLoad(SomeResource, Pixel % 1024);
}
