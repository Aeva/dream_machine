#version 420
uniform TestStruct
{
	float ElapsedTime;
};

layout(location = 0) out vec4 OutColor;

void main()
{
	OutColor = vec4(0.0, 0.0, (sin(ElapsedTime * 10.0) + 1.0) * 0.5, 1.0);
}
