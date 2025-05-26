import pygame as pg
from Window import *
from opengl_util import *
from QuadRenderer import *
import numpy as np

quad_vertex_src = """
#version 330 core

layout(location = 0) in vec3 position;
layout(location = 1) in vec2 texCoord;

out vec2 uv; 

void main()
{
    gl_Position = vec4(position, 1);
    uv = texCoord;
}
"""

quad_fragment_src = """
#version 330 core

layout(location = 0) out vec4 frag_color;
in vec2 uv;
uniform sampler2D screenTexture;

void main()
{
    vec3 color = texture(screenTexture, uv).rgb;
    frag_color = vec4(color, 1.0);
}
"""

quad_vertices = np.array([
    # positions    # texCoords
    -1.0,  1.0,     0.0, 1.0,
    -1.0, -1.0,     0.0, 0.0,
     1.0, -1.0,     1.0, 0.0,

    -1.0,  1.0,     0.0, 1.0,
     1.0, -1.0,     1.0, 0.0,
     1.0,  1.0,     1.0, 1.0
], dtype=np.float32)

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

class Game(Application):
    def __init__(self):
        scale = (4, 4)
        PIXEL_WIDTH, PIXEL_HEIGHT = 320, 180
        WINDOW_SIZE = (PIXEL_WIDTH * scale[0], PIXEL_HEIGHT * scale[1])

        super().__init__(WINDOW_SIZE)

        self.fb = glFramebuffer(glShaderProgram(
            """
            #version 330 core
            layout (location = 0) in vec2 aPos;
            layout (location = 1) in vec2 aTexCoord;
            out vec2 TexCoord;

            void main() {
                TexCoord = aTexCoord;
                gl_Position = vec4(aPos, 0.0, 1.0);
            }
            """,
            """
            #version 330 core
            in vec2 TexCoord;
            out vec4 FragColor;
            uniform sampler2D screenTexture;

            void main() {
                vec3 color = texture(screenTexture, TexCoord).rgb;
                FragColor = vec4(color, 1.0);
            }
            """
            ), (PIXEL_WIDTH, PIXEL_HEIGHT))

        # Empty texture
        self.screenTex = glTexture(PIXEL_WIDTH, PIXEL_HEIGHT, GL_NEAREST)
        self.fb.attachTexture(self.screenTex)

        self.renderer = QuadRenderer(self.window)
        self.quad_shader = glShaderProgram(quad_vertex_src, quad_fragment_src)

        self.wallpaper = glTexture.loadTexture('wallpaper.jpg', GL_NEAREST)

        glClearColor(0.1, 0.1, 0.1, 1)

    def onWindowClose(self):
        self.renderer.delete()
        self.fb.delete()
        self.screenTex.delete()
        print('Close from Game')

    def onUpdate(self):
        self.window.dispatchEvent(self.eventHandler)

        # Render triangle to framebuffer
        self.fb.bind()
        glViewport(0, 0, *self.fb.screenBufferSize)
        glClearColor(0.1, 0.1, 0.1, 1.0)

        glClear(GL_COLOR_BUFFER_BIT)

        t = pg.time.get_ticks() * 0.001

        ratio = self.wallpaper.height / self.wallpaper.width
        q = Quad((2, 2 * ratio), (0, 0), 0)
        self.renderer.drawQuad(q);

        # r = 4
        # for i in range(r):
        #     for j in range(r):
        #         q = Quad((2.0 / r, 2.0 / r * ratio), (2.0 * i / r - 1.0 + 1.0 / r, 2.0 * j / r - 1.0 + 1.0 / r), t)
        #         self.renderer.drawQuad(q)
        #         if self.renderer.full:
        #             self.quad_shader.bind()
        #             self.renderer.submit()
        #             self.wallpaper.bind(0)
        #             glUniform1i(glGetUniformLocation(self.quad_shader.program, "screenTexture"), 0)
        #             self.renderer.clearBuffer()
        #             self.renderer.drawQuad(q)

        if self.renderer.vbIndex > 0:
            self.quad_shader.bind()
            self.wallpaper.bind(0)
            glUniform1i(glGetUniformLocation(self.quad_shader.program, "screenTexture"), 0)
            self.renderer.submit()
        
        # Render fullscreen quad with post-processing
        self.fb.unbind()
        glViewport(0, 0, self.window.width, self.window.height)
        glClearColor(0.2, 0.3, 0.3, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        glUseProgram(self.fb.shader.program)
        glBindVertexArray(self.fb.quad_vao)
        self.screenTex.bind(0)
        glUniform1i(glGetUniformLocation(self.fb.shader.program, "screenTexture"), 0)
        glDrawArrays(GL_TRIANGLES, 0, 6)

def main():
    app = Game()
    app.run()

if __name__ == "__main__":
    main()
