from direct.showbase.ShowBaseGlobal import aspect2d
import panda3d.core as p3d


class PlayerStats:
    def __init__(self, loader, player_id: str):
        self.loader = loader
        self.textures = [
            self.loader.load_texture(f"../common/assets/graphics/player{player_id}-energy-0.png"),
            self.loader.load_texture(f"../common/assets/graphics/player{player_id}-energy-1.png"),
            self.loader.load_texture(f"../common/assets/graphics/player{player_id}-energy-2.png"),
            self.loader.load_texture(f"../common/assets/graphics/player{player_id}-energy-3.png"),
            self.loader.load_texture(f"../common/assets/graphics/player{player_id}-energy-4.png"),
            self.loader.load_texture(f"../common/assets/graphics/player{player_id}-energy-5.png"),
            self.loader.load_texture(f"../common/assets/graphics/player{player_id}-energy-6.png")
        ]
        self.maker = p3d.CardMaker('card')
        self.card = None
        self.maker.set_frame(
            p3d.Vec3(0.5, 0.5),
            p3d.Vec3(0.96, 0.5),
            p3d.Vec3(0.96, 0.9),
            p3d.Vec3(0.5, 0.9)
        )

    def display(self):
        self.card = aspect2d.attach_new_node(self.maker.generate())
        self.card.set_texture(self.textures[6])

    def set_energy(self, level: float):
        """sets texture according to energy level [0,1]"""
        if self.card is not None:
            self.card.set_texture(self.textures[min(max(int(level * 6), 0), 6)])
