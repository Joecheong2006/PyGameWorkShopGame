from Window import *

class Application:
    def __init__(self, window_size: tuple[int, int]):
        self.eventHandler = WindowEventHandler()
        self.eventHandler.windowClose = self.onWindowClose
        self.eventHandler.windowKeyAction = self.onWindowKeyAction

        self.window_size = window_size

        pg.init()
        print(f'Initialized Pygame {pg.version.ver}')

        self.window = Window(self.window_size[0], self.window_size[1])

    def onWindowClose(self): pass
    def onWindowKeyAction(self, key: int, mod: int, unicode: int, scancode: int): pass
    def onUpdate(self): pass

    def run(self):
        while self.window.isRunning:
            self.window.dispatchEvent(self.eventHandler)
            self.onUpdate()
            self.window.flip()
        self.onWindowClose()
