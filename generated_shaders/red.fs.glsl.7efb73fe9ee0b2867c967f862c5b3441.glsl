#version 420
struct SomeType
{
	mat4 Whatever;
	float Etc;
};
layout(std140, binding = 0)
uniform Fnord
{
	float ElapsedTime;
};
layout(std140, binding = 1)
uniform Whatsit
{
	SomeType Moop;
};

layout(location = 0) out vec4 OutColor;

void main()
{
	const float Alpha = (gl_FragCoord.x / 512.0) * (gl_FragCoord.y / 512.0);
	const vec3 Red1 = vec3(1.0, 0.3, 0.0);
	const vec3 Red2 = vec3(1.0, 0.0, 0.3);
	OutColor = vec4(mix(Red1, Red2, Alpha), 1.0);
}
