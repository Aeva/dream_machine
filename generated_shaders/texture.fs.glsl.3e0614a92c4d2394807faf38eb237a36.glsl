#version 420
struct SomeType
{
	mat4 Whatever;
	float Etc;
};
layout(std140, binding = 0)
uniform WindowParams
{
	vec4 WindowSize;
	vec4 WindowScale;
	float ElapsedTime;
};
layout(binding = 0)
uniform sampler2D FancyTexture;
layout(location = 0)
 out vec4 OutColor;


void main()
{
	vec2 UV = gl_FragCoord.xy * WindowSize.zw;
	UV.x += sin(UV.y + ElapsedTime);
	UV.y += cos(UV.x + ElapsedTime);
	OutColor = texture(FancyTexture, UV);
}
