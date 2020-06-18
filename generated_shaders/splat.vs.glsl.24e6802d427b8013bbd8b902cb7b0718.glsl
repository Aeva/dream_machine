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

void main()
{
	gl_Position = vec4(-1.0 + float((gl_VertexID & 1) << 2), -1.0 + float((gl_VertexID & 2) << 1), 0, 1);
}