from direct.showbase.ShowBaseGlobal import aspect2d
import panda3d.core as p3d


class EndScreen:
    def __init__(self, loader):
        self.textNodePath = None
        self.font = loader.loadFont("../common/assets/Font.ttf")
        self.displayed = False

    def display(self, winning: bool, winner_id: int):
        if self.displayed:
            return

        self.displayed = True
        heading = p3d.TextNode('heading')
        heading.set_text("Koniec gry" if not winning else "Wygrana!")
        heading.set_font(self.font)
        heading.set_card_color((0, 0, 0, 0.5))
        heading.set_card_as_margin(20, 20, 20, 20)
        heading.set_align(p3d.TextNode.ACenter)
        heading_node_path = aspect2d.attach_new_node(heading)
        heading_node_path.set_pos(p3d.Vec3(0, 0.2))
        heading_node_path.set_scale(0.15)
        if not winning:
            subtext = p3d.TextNode('subtext')
            subtext.set_text(f"Gracz {winner_id} wrócił do bazy z flagą")
            subtext.set_font(self.font)
            subtext.set_align(p3d.TextNode.ACenter)
            subtext_node_path = aspect2d.attach_new_node(subtext)
            subtext_node_path.set_pos(p3d.Vec3(0, 0))
            subtext_node_path.set_scale(0.07)
