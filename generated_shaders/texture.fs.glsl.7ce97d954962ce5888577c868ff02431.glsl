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

layout(location = 0) out vec4 OutColor;

void main()
{
	vec2 UV = gl_FragCoord.xy / 512.0;
	UV.x += sin(UV.y + ElapsedTime);
	UV.y += cos(UV.x + ElapsedTime);
	OutColor = texture(FancyTexture, UV);
}
