from Window import Window

class GameObjectSystem:
    from GameObject import GameObject
    gameObjects: list[GameObject]
    def __init__(self):
        raise RuntimeError("ScripSystem cannot be created!")

    @staticmethod
    def SetUp():
        GameObjectSystem.gameObjects = []

    @staticmethod
    def ShutDown():
        GameObjectSystem.gameObjects = []

    @staticmethod
    def AddGameObject(object: GameObject):
        GameObjectSystem.gameObjects.append(object)


    @staticmethod
    def Update(window: Window):
        objs = GameObjectSystem.gameObjects
        for object in objs:
            if not object.started:
                object.OnStart()
                object.started = True

        for object in objs:
            object.OnUpdate(window)
