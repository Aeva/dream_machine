#version 420
「interfaces」


void main()
{
	vec2 UV = gl_FragCoord.xy * WindowSize.zw;
	UV.x += sin(UV.y + ElapsedTime);
	UV.y += cos(UV.x + ElapsedTime);
	OutColor = texture(FancyTexture, UV);
}
