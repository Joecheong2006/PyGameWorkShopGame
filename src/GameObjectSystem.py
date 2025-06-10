from Window import Window

class GameObjectSystem:
    from GameObject import GameObject
    objects: list[GameObject]
    def __init__(self):
        raise RuntimeError("ScripSystem cannot be created!")

    @staticmethod
    def SetUp():
        GameObjectSystem.objects = []

    @staticmethod
    def ShutDown():
        GameObjectSystem.objects = []

    @staticmethod
    def AddGameObject(object: GameObject):
        GameObjectSystem.objects.append(object)

    @staticmethod
    def Update(window: Window):
        objs = GameObjectSystem.objects
        for object in objs:
            if not object.started:
                object.OnStart()
                object.started = True

        for object in objs:
            object.OnUpdate(window)

    @staticmethod
    def FindFirstObjectByType(type):
        objs = GameObjectSystem.objects
        for object in objs:
            if isinstance(object.inher, type):
                return object.inher
        return None
