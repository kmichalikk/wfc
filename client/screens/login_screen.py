from direct.gui.DirectEntry import DirectEntry
from direct.gui.OnscreenImage import OnscreenImage
from direct.showbase.ShowBaseGlobal import aspect2d
from panda3d.core import TextNode, Vec3


class LoginScreen:
    def __init__(self, loader, start):
        self.start = start
        self.textNodePath = None
        self.bg_image = None
        self.login_entry = None
        self.font = loader.loadFont("../common/assets/Font.ttf")
        self.text = TextNode('login')
        self.text.setText("Log in")
        self.text.setFont(self.font)
        self.text.setAlign(TextNode.ACenter)
        self.display()

    def display(self):
        self.bg_image = OnscreenImage(image="../common/assets/login_background.png", parent=aspect2d)
        self.bg_image.setScale(1.4)
        self.textNodePath = aspect2d.attachNewNode(self.text)
        self.textNodePath.setScale(0.14)
        self.textNodePath.setPos(Vec3(0, 0.25))

        self.login_entry = DirectEntry(text="", scale=0.1, command=self.log_in, frameColor=(1, 1, 1, 0.1),
                                       text_fg=(1, 1, 1, 1), text_font=self.font, width=10)

        self.login_entry.reparentTo(aspect2d)
        self.login_entry.setScale(0.08)
        self.login_entry.setPos(Vec3(-0.4, 0))

    def log_in(self, username):
        username = username.lower()
        self.start(username)

    def hide(self):
        self.textNodePath.removeNode()
        self.bg_image.removeNode()
        self.login_entry.removeNode()
