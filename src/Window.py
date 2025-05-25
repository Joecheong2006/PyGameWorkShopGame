import pygame as pg
from typing import Callable
import numpy as np

class WindowEventHandler:
    def __init__(self):
        self.windowClose: Callable[[], None] = lambda : None
        self.windowInitialize: Callable[[], None] = lambda : None
        self.windowKeyAction: Callable[[int, int, int, int], None] = lambda key, mod, unicode, scancode : None
        self.windowCursor: Callable[[], None] = lambda : None
        self.windowMouse: Callable[[], None] = lambda : None

class Window:
    def __init__(self, width: int, height: int, fps: int = 60):
        self.width = width
        self.height = height
        self.clock = pg.time.Clock()
        self.fps = fps

        # Initialize OpenGL
        version = (3, 3)
        print(f'Initialize OpenGL {version[0]}.{version[1]} core')
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, version[0])
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, version[1])
        pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK, pg.GL_CONTEXT_PROFILE_CORE)

        # Create Window
        pg.display.set_mode((width, height), pg.OPENGL | pg.DOUBLEBUF | pg.RESIZABLE)
        self.isRunning = True

    def flip(self):
        pg.display.flip()
        self.clock.tick(self.fps)

    def dispatchEvent(self, handler: WindowEventHandler):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.isRunning = False
            elif event.type == pg.KEYDOWN or event.type == pg.KEYUP:
                handler.windowKeyAction(event.key, event.mod, event.unicode, event.scancode)
            elif event.type == pg.MOUSEMOTION:
                handler.windowCursor()
            elif event.type == pg.MOUSEBUTTONUP or pg.MOUSEBUTTONDOWN:
                handler.windowMouse()
