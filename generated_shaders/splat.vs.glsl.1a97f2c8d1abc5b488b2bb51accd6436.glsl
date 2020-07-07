#version 420
layout(std140, binding = 0)
uniform Fnord
{
	float ElapsedTime;
};

void main()
{
	gl_Position = vec4(-1.0 + float((gl_VertexID & 1) << 2), -1.0 + float((gl_VertexID & 2) << 1), 0, 1);
}