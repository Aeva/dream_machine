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


float GridFix(float Coord)
{
	if (Coord < 0.0)
	{
		Coord = 1.0 - fract(abs(Coord));
	}
	if (Coord > 1.0)
	{
		Coord = fract(Coord);
	}
	return Coord;
}


vec2 GridUV(vec2 UV)
{
	return vec2(GridFix(UV.x), GridFix(UV.y));
}


void main()
{
	vec2 UV = gl_FragCoord.xy * WindowSize.zw;
	UV.x += sin(UV.y + ElapsedTime * 0.1);
	UV.y += cos(UV.x + ElapsedTime * 0.1);
	ivec2 Tile = ivec2(GridUV(UV) * WindowSize.xy) / 32;
	vec3 Red = texture(RedColorTarget, UV).rgb;
	vec3 Blue = texture(BlueColorTarget, UV).rgb;
	float Alpha;
	if (Tile.x % 2 == Tile.y % 2)
	{
		Alpha = sin(ElapsedTime * 0.9) * 0.5 + 0.5;
	}
	else
	{
		Alpha = sin(ElapsedTime * 0.9 + 1.5) * 0.5 + 0.5;
	}
	OutColor = vec4(mix(Red, Blue, Alpha), 1.0);
}
