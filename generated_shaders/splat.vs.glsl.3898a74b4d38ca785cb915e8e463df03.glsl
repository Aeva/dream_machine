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

void main()
{
	gl_Position = vec4(-1.0 + float((gl_VertexID & 1) << 2), -1.0 + float((gl_VertexID & 2) << 1), 0, 1);
}