import pygame as pg
from typing import Callable, Any
import numpy as np

class WindowEventHandler:
    def __init__(self):
        self.windowClose: Callable[[], None] = lambda : None
        self.windowInitialize: Callable[[], None] = lambda : None
        self.windowKeyAction: Callable[[int, int, int, int], None] = lambda key, mod, unicode, scancode : None
        self.windowCursor: Callable[[], None] = lambda : None
        self.windowMouseMotion: Callable[[tuple[int, int], tuple[int, int], tuple[bool, bool, bool], bool], None] = lambda pos, rel, button, touch: None
        self.windowMouseButton: Callable[[tuple[int, int], int, bool], None] = lambda pos, button, touch: None
        self.windowMouseWheel: Callable[[bool, int, int, bool, float, float], None] = lambda flipped, x, y, touch, precise_x, precise_y: None

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

        self.keys = pg.key.get_pressed()

        # Create Window
        pg.display.set_mode((width, height), pg.OPENGL | pg.DOUBLEBUF)
        self.isRunning = True

    def flip(self):
        pg.display.flip()
        self.clock.tick(self.fps)

    def dispatchEvent(self, handler: WindowEventHandler):
        self.keys = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.isRunning = False
            elif event.type == pg.KEYDOWN or event.type == pg.KEYUP:
                handler.windowKeyAction(event.key, event.mod, event.unicode, event.scancode)
            elif event.type == pg.MOUSEBUTTONUP or event.type == pg.MOUSEBUTTONDOWN:
                handler.windowMouseButton(event.pos, event.button, event.touch)
            elif event.type == pg.MOUSEMOTION:
                handler.windowMouseMotion(event.pos, event.rel, event.buttons, event.touch)
            elif event.type == pg.MOUSEWHEEL:
                handler.windowMouseWheel(event.flipped, event.x, event.y, event.touch, event.precise_x, event.precise_y)
