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
	OutColor = vec4(0.0, 0.0, (sin(ElapsedTime * 0.01) + 1.0) * 0.5, 1.0);
}
