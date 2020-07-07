#version 420
layout(std140, binding = 0)
uniform Fnord
{
	float ElapsedTime;
};

layout(location = 0) out vec4 OutColor;

void main()
{
	OutColor = vec4(0.0, 1.0, ElapsedTime, 0.0);
}
