from client.game import Game


class TestGame(Game):
    def __init__(self):
        self.map_size = 10
        super().__init__()
        self.border.show()
        self.player.colliders[0].show()
        for tile in self.tile_colliders:
            tile.show()

    def update_camera(self, task):
        self.camera.set_pos(10, 10, 50)
        self.camera.look_at(10, 10, 0)
        return task.cont


app = TestGame()
app.run()
