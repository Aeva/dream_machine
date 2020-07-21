#version 420
layout(std140, binding = 0)
uniform WindowParams
{
	vec4 WindowSize;
	vec4 WindowScale;
	float ElapsedTime;
};
layout(location = 0)
 out vec4 BlueColorTarget;
layout(location = 1)
 out vec4 SomeDepthTarget;


void main()
{
	const float Alpha = (gl_FragCoord.x * WindowSize.z) * (gl_FragCoord.y * WindowSize.w);
	const vec3 Blue1 = vec3(0.0, 0.3, 1.0);
	const vec3 Blue2 = vec3(0.3, 0.0, 1.0);
	BlueColorTarget = vec4(mix(Blue1, Blue2, Alpha), 1.0);
}
