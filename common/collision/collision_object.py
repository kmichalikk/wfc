from panda3d.core import CollisionNode

intangible_shapes = ["water", "grass", "space"]


class CollisionObject:
    def __init__(self, parent, name, shapes):
        self.colliders = []

        if name in intangible_shapes:
            for shape in shapes:
                shape.setTangible(False)

        self.collision_node = CollisionNode(name)
        for shape in shapes:
            self.collision_node.add_solid(shape)
            self.colliders.append(parent.attachNewNode(self.collision_node))

    def show(self):
        for node in self.colliders:
            node.show()
