#version 420
struct SomeType
{
	mat4 Whatever;
	float Etc;
};
uniform Fnord
{
	float ElapsedTime;
};
uniform Whatsit
{
	SomeType Moop;
};

layout(location = 0) out vec4 OutColor;
void main()
{
	OutColor = vec4(1.0, 0.0, 0.0, 1.0);
}
