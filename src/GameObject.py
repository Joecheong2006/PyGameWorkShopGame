from Window import Window
import GameObjectSystem as GOsys

class GameObject:
    def __init__(self):
        GOsys.GameObjectSystem.AddGameObject(self)

    def OnStart(self):
        pass

    def OnUpdate(self, window: Window):
        pass

    def OnDestroy(self):
        pass

