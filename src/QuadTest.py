from Window import Window
from GameObject import GameObject
from GameObjectSystem import GameObjectSystem
from QuadRenderer import Quad
from pyglm import glm

class QuadTest(GameObject):
    def __init__(self):
        super().__init__(self)

        def onRender(quadRenderer, quad):
            pass

        self.quad = Quad(glm.vec2(1, 1), glm.vec3(0, 3, 0))
        self.quad.onRender = onRender

        GameObjectSystem.AddQuadObject(self.quad)

    def OnUpdate(self, window: Window):
        deltaTime = window.deltaTime
        self.quad.rotation *= glm.angleAxis(deltaTime, glm.vec3(0, 1, 0))
        self.quad.updateVertices()
