from panda3d.core import CollisionNode


class CollisionObject:
    def __init__(self, parent, name, shapes):
        self.colliders = []
        collision_node = CollisionNode(name)
        for shape in shapes:
            collision_node.add_solid(shape)
            self.colliders.append(parent.attachNewNode(collision_node))

    def show(self):
        for node in self.colliders:
            node.show()
