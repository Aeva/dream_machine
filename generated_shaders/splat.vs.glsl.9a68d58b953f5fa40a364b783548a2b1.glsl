#version 420
layout(location = 0)
 out vec4 BlueColorTarget;
layout(location = 1)
 out vec4 SomeDepthTarget;

void main()
{
	gl_Position = vec4(-1.0 + float((gl_VertexID & 1) << 2), -1.0 + float((gl_VertexID & 2) << 1), 0, 1);
}