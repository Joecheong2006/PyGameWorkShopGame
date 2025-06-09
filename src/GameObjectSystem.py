from GameObject import *

class GameObjectSystem:
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
        GameObjectSystem.gameObjects[-1].OnStart()

    @staticmethod
    def Update(window: Window):
        for object in GameObjectSystem.gameObjects:
            object.OnUpdate(window)
