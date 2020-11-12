#version 420
#extension GL_ARB_compute_shader : require
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

layout(local_size_x = 8, local_size_y = 8, local_size_z = 1) in;
void main()
{
	float Wave = float(gl_WorkGroupID.y * 128 + gl_WorkGroupID.x) / 16384.0;
	vec4 BoringData = vec4(Wave, vec2(gl_LocalInvocationID.xy) / 8.0, 1.0);
	imageStore(SomeResource, ivec2(gl_GlobalInvocationID.xy), BoringData);
}
