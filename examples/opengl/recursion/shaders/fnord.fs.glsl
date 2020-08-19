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


const vec4 MissColor = vec4(0.5, 0.5, 0.5, 1.0);
const float AlmostZero = 0.001;


float Sphere(vec3 Local, float Radius)
{
	return length(Local) - Radius;
}


float Box(vec3 Local, vec3 Bounds)
{
	vec3 Dist = abs(Local) - Bounds;
	return length(max(Dist, 0.0)) + min(max(Dist.x, max(Dist.y, Dist.z)), 0.0);
}


float Sphube(vec3 Local, float Alpha)
{
	return mix(Sphere(Local, 1.0), Box(Local, vec3(1.0)), Alpha);
}


float Gloop(vec3 Point, float Scale)
{
	return sin(Scale * Point.x) * sin(Scale * Point.y) * sin(Scale * Point.z);
}


float Union(float LHS, float RHS)
{
	return min(LHS, RHS);
}


float Subtract(float LHS, float RHS)
{
	return max(LHS, -RHS);
}


float Intersection(float LHS, float RHS)
{
	return max(LHS, RHS);
}


vec3 Twist(vec3 Point, float Intensity)
{
	float C = cos(Intensity * Point.z);
	float S = sin(Intensity * Point.z);
	mat2  M = mat2(C, -S, S, C);
	return vec3(M * Point.xy, Point.z);
}


float OddShape(vec3 Local)
{
	vec3 BoxLocal = Local;
	const float Repeat = 0.5;
	BoxLocal.z = mod(BoxLocal.z + 0.5 * Repeat, Repeat) - 0.5 * Repeat;
	Local = Twist(Local, length(Local.xy) * 5.0);
	float Dist = Sphube(Local, 0.5);
	Dist = Intersection(Dist, Gloop(Local, 10.0));
	Dist = Subtract(Dist, Box(BoxLocal, vec3(2.0, 2.0, Repeat * 0.3)));
	return Dist;
}


float SceneSDF(vec3 View)
{
	float Shape = OddShape(View - vec3(0.0, 3.0, 0.0));
	return Shape;
}


vec3 GetRayDir(vec2 FragCoord, float FOV)
{
	float Aspect = WindowSize.y * WindowSize.z;
	vec2 NDC = FragCoord * WindowSize.zw * 2.0 - 1.0;
	vec2 Angle = NDC * vec2(FOV, FOV * Aspect) * 0.5;
	vec3 RayDir = vec3(sin(radians(Angle)), 0.0).xzy;
	RayDir.y = sqrt(1.0 - (RayDir.x * RayDir.x) - (RayDir.z * RayDir.z));
	return RayDir;
}


bool RayMarch(vec3 RayDir, float TravelStart, out vec4 Position)
{
	Position.w = TravelStart;
	bool bHit = false;
	//for (int i=0; i<10; ++i)
	{
		Position.xyz = RayDir * Position.w;
		float Dist = SceneSDF(Position.xyz);
		if (Dist > 0.0)
		{
			Position.w += Dist;
		}
	}
	return distance(Position.w, TravelStart) < AlmostZero;
}


vec3 Gradient(vec3 Position)
{
	float Dist = SceneSDF(Position);
	return normalize(vec3(
		SceneSDF(vec3(Position.x + AlmostZero, Position.y, Position.z)) - Dist,
		SceneSDF(vec3(Position.x, Position.y + AlmostZero, Position.z)) - Dist,
		SceneSDF(vec3(Position.x, Position.y, Position.z + AlmostZero)) - Dist));
}


void main()
{
	vec2 UV = gl_FragCoord.xy * WindowSize.zw;
	float Last = texture(Accumulator, UV).w;

	vec3 RayDir = GetRayDir(gl_FragCoord.xy, 45.0);
	vec4 Position;
	if (Last < 1000.0 && RayMarch(RayDir, Last, Position))
	{
		vec3 Normal = Gradient(Position.xyz);
		AccumulatorTarget = vec4(Normal, Position.w);
	}
	else
	{
		AccumulatorTarget = vec4(MissColor.xyz, Position.w);
	}
}
