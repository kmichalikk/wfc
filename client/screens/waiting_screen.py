from direct.showbase.ShowBaseGlobal import aspect2d
from panda3d.core import TextNode, Vec3


class WaitingScreen:
    def __init__(self, loader):
        self.textNodePath = None
        self.font = loader.loadFont("../common/assets/Font.ttf")
        self.text = TextNode('waiting')
        self.text.setText("Oczekiwanie na innych graczy...")
        self.text.setFont(self.font)
        self.text.setCardColor(0, 0, 0, 0.5)
        self.text.setCardAsMargin(20, 20, 20, 20)
        self.text.setAlign(TextNode.ACenter)

    def display(self):
        self.textNodePath = aspect2d.attachNewNode(self.text)
        self.textNodePath.setScale(0.07)
        self.textNodePath.setPos(Vec3(0, 0))

    def hide(self):
        self.textNodePath.removeNode()

    def update(self, active_players, expected_players):
        player_count_text = f"{active_players}/{expected_players}"
        self.text.setText(f"Oczekiwanie na innych graczy...\n{player_count_text}")
