from Window import Window
from GameObject import GameObject
from GameObjectSystem import GameObjectSystem
from QuadRenderer import Quad
from pyglm import glm

class QuadTest(GameObject):
    def __init__(self):
        super().__init__(self)

        from opengl_util import glTexture, GL_NEAREST
        self.grass = glTexture.loadTexture('res/grass27.png', GL_NEAREST)

        def onRender(quad, shader):
            self.grass.bind(3)
            shader.setUniform1i("hasDiffuseTex", 1)
            shader.setUniform1i("diffuseTexture", 3)

        self.quad = Quad(glm.vec2(0.6, 0.6), glm.vec3(0, 0.3, -1))
        self.quad.onRender = onRender

        GameObjectSystem.AddQuadObject(self.quad)

    def OnUpdate(self, window: Window):
        deltaTime = window.deltaTime
        from Camera import Camera
        position = GameObjectSystem.FindFirstObjectByType(Camera).position
        self.quad.rotation = glm.quatLookAt(glm.normalize(glm.vec3(position.x, 0, position.z)), glm.vec3(0, 1, 0))
        self.quad.updateVertices()
