
#include <iostream>
#include <GLFW/glfw3.h>

extern int CurrentRenderer;


extern void UserSetupCallback(GLFWwindow* Window)
{
}


extern void UserFrameCallback(GLFWwindow* Window)
{
	if (glfwGetKey(Window, GLFW_KEY_1) == GLFW_PRESS)
	{
		CurrentRenderer = 0;
	}
	else if (glfwGetKey(Window, GLFW_KEY_2) == GLFW_PRESS)
	{
		CurrentRenderer = 1;
	}
}
