from Window import Window

class GameObject:
    def __init__(self, inher):
        from GameObjectSystem import GameObjectSystem
        self.inher = inher
        GameObjectSystem.AddGameObject(self)

    def OnStart(self):
        pass

    def OnUpdate(self, window: Window):
        pass

    def OnDestroy(self):
        pass
