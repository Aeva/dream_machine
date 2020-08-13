
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

precision mediump float;


「interfaces」


void main()
{
	float X = sin(ElapsedTime * 50.0 + gl_FragCoord.y * 0.1);
	float Y = sin(ElapsedTime * 50.0 + gl_FragCoord.x * 0.1);
	vec2 Offset = vec2(X, Y) * 5.0;
	vec2 UV = (gl_FragCoord.xy + Offset) * WindowSize.zw;
	gl_FragColor = texture2D(SomeTarget, UV);
}