from Window import *

class Application:
    def __init__(self, window_size: tuple[int, int]):
        self.eventHandler = WindowEventHandler()
        self.eventHandler.windowClose = self.OnWindowClose
        self.eventHandler.windowKeyAction = self.OnWindowKeyAction
        self.eventHandler.windowMouseButton = self.OnWindowMouseButton
        self.eventHandler.windowMouseMotion = self.OnWindowMouseMotion
        self.eventHandler.windowMouseWheel = self.OnWindowMouseWheel

        self.window_size = window_size

        pg.init()
        print(f'Initialized Pygame {pg.version.ver}')

        self.window = Window(self.window_size[0], self.window_size[1])

    def OnWindowClose(self): pass
    def OnWindowKeyAction(self, key: int, type: int, mod: int, unicode: int, scancode: int): pass
    def OnWindowMouseButton(self, pos: tuple[int, int], button: int, touch: bool): pass
    def OnWindowMouseMotion(self, pos: tuple[int, int], rel: tuple[int, int], button: tuple[bool, bool, bool], touch: bool): pass
    def OnWindowMouseWheel(self, flipped: bool, x: int, y: int, touch: bool, precise_x: float, precise_y: float): pass
    def OnUpdate(self): pass

    def run(self):
        while self.window.isRunning:
            self.window.dispatchEvent(self.eventHandler)
            self.OnUpdate()
            self.window.flip()
        self.OnWindowClose()
