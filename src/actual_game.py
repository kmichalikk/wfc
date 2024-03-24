from game import Game


class ActualGame(Game):
    def __init__(self):
        self.map_size = 10
        super().__init__()

    def update_camera(self, task):
        self.camera.set_pos(self.player.model.getX(), self.player.model.getY() - 3, 7)
        self.camera.look_at(self.player.model)
        return task.cont


app = ActualGame()
app.run()
