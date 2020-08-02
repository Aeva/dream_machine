#version 420

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
	const float Alpha = (gl_FragCoord.x * WindowSize.z) * (gl_FragCoord.y * WindowSize.w);
	const vec3 Blue1 = vec3(0.0, 0.3, 1.0);
	const vec3 Blue2 = vec3(0.3, 0.0, 1.0);
	BlueColorTarget = vec4(mix(Blue1, Blue2, Alpha), 1.0);
}
