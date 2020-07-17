#version 420
「interfaces」

layout(location = 0) out vec4 OutColor;


float GridFix(float Coord)
{
	if (Coord < 0.0)
	{
		Coord = 1.0 - fract(abs(Coord));
	}
	if (Coord > 1.0)
	{
		Coord = fract(Coord);
	}
	return Coord;
}


vec2 GridUV(vec2 UV)
{
	return vec2(GridFix(UV.x), GridFix(UV.y));
}


void main()
{
	vec2 UV = gl_FragCoord.xy / 512.0;
	UV.x += sin(UV.y + ElapsedTime);
	UV.y += cos(UV.x + ElapsedTime);
	ivec2 Tile = ivec2(GridUV(UV) * 512.0) / 32;
	vec3 Red = texture(RedImage, UV).rgb;
	vec3 Blue = texture(BlueImage, UV).rgb;
	float Alpha;
	if (Tile.x % 2 == Tile.y % 2)
	{
		Alpha = sin(ElapsedTime * 9.0) * 0.5 + 0.5;
	}
	else
	{
		Alpha = sin(ElapsedTime * 9.0 + 1.5) * 0.5 + 0.5;
	}
	OutColor = vec4(mix(Red, Blue, Alpha), 1.0);
}
