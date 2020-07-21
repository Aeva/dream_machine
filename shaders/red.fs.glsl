#version 420
「interfaces」


void main()
{
	const float Alpha = (gl_FragCoord.x * WindowSize.z) * (gl_FragCoord.y * WindowSize.w);
	const vec3 Red1 = vec3(1.0, 0.3, 0.0);
	const vec3 Red2 = vec3(1.0, 0.0, 0.3);
	RedColorTarget = vec4(mix(Red1, Red2, Alpha), 1.0);
}
