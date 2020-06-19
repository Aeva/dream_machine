#version 420
struct SomeType
{
	mat4 Whatever;
	float Etc;
};
layout(std140, binding = 1)
uniform Fnord
{
	float ElapsedTime;
};
layout(std140, binding = 0)
uniform Whatsit
{
	SomeType Moop;
};

layout(location = 0) out vec4 OutColor;

void main()
{
	OutColor = vec4(0.0, 0.0, ElapsedTime, 1.0);
}
