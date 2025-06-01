from Window import *

class Application:
    def __init__(self, window_size: tuple[int, int]):
        self.eventHandler = WindowEventHandler()
        self.eventHandler.windowClose = self.onWindowClose
        self.eventHandler.windowKeyAction = self.onWindowKeyAction
        self.eventHandler.windowMouseButton = self.onWindowMouseButton
        self.eventHandler.windowMouseMotion = self.onWindowMouseMotion
        self.eventHandler.windowMouseWheel = self.onWindowMouseWheel

        self.window_size = window_size

        pg.init()
        print(f'Initialized Pygame {pg.version.ver}')

        self.window = Window(self.window_size[0], self.window_size[1])

    def onWindowClose(self): pass
    def onWindowKeyAction(self, key: int, mod: int, unicode: int, scancode: int): pass
    def onWindowMouseButton(self, pos: tuple[int, int], button: int, touch: bool): pass
    def onWindowMouseMotion(self, pos: tuple[int, int], rel: tuple[int, int], button: tuple[bool, bool, bool], touch: bool): pass
    def onWindowMouseWheel(self, flipped: bool, x: int, y: int, touch: bool, precise_x: float, precise_y: float): pass
    def onUpdate(self): pass

    def run(self):
        while self.window.isRunning:
            self.window.dispatchEvent(self.eventHandler)
            self.onUpdate()
            self.window.flip()
        self.onWindowClose()
