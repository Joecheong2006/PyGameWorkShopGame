from Window import Window
from Model import Model

class GameObjectSystem:
    from GameObject import GameObject
    objects: list[GameObject]

    from Model import Model
    modelObjects: list[Model]

    from Camera import Camera
    mainCamera: Camera | None = None

    def __init__(self):
        raise RuntimeError("GmaeObjectSystem cannot be created!")

    @staticmethod
    def SetUp():
        GameObjectSystem.objects = []
        GameObjectSystem.modelObjects = []
        Model.CompileShader()

    @staticmethod
    def ShutDown():
        for obj in GameObjectSystem.modelObjects:
            obj.delete()
        GameObjectSystem.objects = []
        GameObjectSystem.modelObjects = []

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
    def FindFirstObjectByType(type):
        objs = GameObjectSystem.objects
        for object in objs:
            if isinstance(object.inher, type):
                return object.inher
        return None
