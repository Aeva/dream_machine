#version 420
layout(std140, binding = 0)
uniform WindowParams
{
	float ElapsedTime;
};
layout(binding = 0)
uniform sampler2D RedColorTarget;
layout(binding = 1)
uniform sampler2D BlueColorTarget;

void main()
{
	gl_Position = vec4(-1.0 + float((gl_VertexID & 1) << 2), -1.0 + float((gl_VertexID & 2) << 1), 0, 1);
}