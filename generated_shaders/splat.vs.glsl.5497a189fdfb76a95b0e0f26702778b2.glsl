#version 420
struct SomeType
{
	mat4 Whatever;
	float Etc;
};
layout(std140, binding = 0)
uniform WindowParams
{
	float ElapsedTime;
};
layout(binding = 0)
uniform sampler2D FancyTexture;

void main()
{
	gl_Position = vec4(-1.0 + float((gl_VertexID & 1) << 2), -1.0 + float((gl_VertexID & 2) << 1), 0, 1);
}