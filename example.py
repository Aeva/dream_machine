
import graffeine


class TestNode1(graffeine.DrawCall):
    size = (256, 256)
    rtv0 = graffeine.ColorTarget()


class TestNode2(graffeine.DrawCall):
    size = (512, 512)
    srv = graffeine.TextureView(TestNode1.rtv0)
    rvt0 = graffeine.ColorTarget()


if __name__ == "__main__":
    graffeine.compile("fnord", TestNode1, TestNode2)
