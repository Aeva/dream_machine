
from ..expanders.common import SyntaxExpander


class RendererCall(SyntaxExpander):
    template = """
void 「name」(int FrameIndex, double CurrentTime, double DeltaTime)
{
「calls」
}
""".strip()
    indent = ("calls",)


class RendererCase(SyntaxExpander):
    template = """
case 「index」:
	Renderer::「name」(FrameIndex, CurrentTime, DeltaTime);
	break;
""".strip()


class RendererSwitch(SyntaxExpander):
    template = """
switch (CurrentRenderer)
{
「cases」
default:
	HaltAndCatchFire();
}
""".strip()
