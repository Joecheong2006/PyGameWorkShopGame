from Window import Window
from Model import Model

class GameObjectSystem:
    from GameObject import GameObject
    objects: list[GameObject]

    from Model import Model
    modelObjects: list[Model]

    from QuadRenderer import Quad, QuadRenderer
    quadObjects: list[Quad]

    from Camera import Camera
    mainCamera: Camera | None = None

    def __init__(self):
        raise RuntimeError("GmaeObjectSystem cannot be created!")

    @staticmethod
    def SetUp():
        GameObjectSystem.objects = []
        GameObjectSystem.modelObjects = []
        GameObjectSystem.quadObjects = []
        Model.CompileShader()

    @staticmethod
    def ShutDown():
        for obj in GameObjectSystem.modelObjects:
            obj.delete()
        GameObjectSystem.objects = []
        GameObjectSystem.modelObjects = []
        GameObjectSystem.quadObjects = []

    @staticmethod
    def AddGameObject(object: GameObject):
        from Camera import Camera
        if isinstance(object.inher, Camera):
            if GameObjectSystem.mainCamera != None:
                raise RuntimeError("Currently only support one camera!")
            GameObjectSystem.mainCamera = object.inher
        GameObjectSystem.objects.append(object)

    @staticmethod
    def AddModelObject(object: Model):
        GameObjectSystem.modelObjects.append(object)

    @staticmethod
    def AddQuadObject(object: Quad):
        GameObjectSystem.quadObjects.append(object)

    @staticmethod
    def Update(window: Window):
        objs = GameObjectSystem.objects
        for object in objs:
            if not object.started:
                object.OnStart()
                object.started = True

        for object in objs:
            object.OnUpdate(window)

    from opengl_util import glShaderProgram
    @staticmethod
    def RenderModel(shader: glShaderProgram):
        mainCamera = GameObjectSystem.mainCamera
        if mainCamera == None:
            return

        modelObjects = GameObjectSystem.modelObjects
        for model in modelObjects:
            model.render(shader, mainCamera)

    @staticmethod
    def RenderQuads(renderer: QuadRenderer, shader: glShaderProgram):
        mainCamera = GameObjectSystem.mainCamera
        if mainCamera == None:
            return

        from OpenGL.GL import glDisable, glEnable, GL_CULL_FACE
        from pyglm import glm
        glDisable(GL_CULL_FACE)

        m = mainCamera.projectionMat * mainCamera.getViewMatrix()
        shader.setUniformMat4("vp", 1, m.to_list())
        shader.setUniform1i("hasDiffuseTex", 0)
        shader.setUniform1i("hasAnimation", 0)
        shader.setUniformMat4("model", 1, glm.mat4(1).to_list())
        quadObjects = GameObjectSystem.quadObjects
        for quad in quadObjects:
            quad.onRender(quad, shader)
            renderer.drawQuad(quad)
            if renderer.full:
                renderer.submit()
                renderer.clearBuffer()
        renderer.submit()

        glEnable(GL_CULL_FACE)

    @staticmethod
    def FindFirstObjectByType(type):
        objs = GameObjectSystem.objects
        for object in objs:
            if isinstance(object.inher, type):
                return object.inher
        return None
