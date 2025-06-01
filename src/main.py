import pygame as pg
from Application import *
from opengl_util import *
from QuadRenderer import *
from Mesh import Mesh
from RenderPipeline import PostProcessingPass
from Camera import *

quad_vertex_src = """
#version 330 core

layout(location = 0) in vec3 position;
layout(location = 1) in vec2 texCoord;

uniform mat4 m;

out vec2 uv; 

void main()
{
    gl_Position = m * vec4(position, 1);
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

class Game(Application):
    def __init__(self):
        scale = (4, 4)
        PIXEL_WIDTH, PIXEL_HEIGHT = 320, 180
        WINDOW_SIZE = (PIXEL_WIDTH * scale[0], PIXEL_HEIGHT * scale[1])

        super().__init__(WINDOW_SIZE)

        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)

        postProcessingShader = glShaderProgram(
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
                )
        self.postProcessingPass = PostProcessingPass(postProcessingShader, GL_NEAREST, (PIXEL_WIDTH, PIXEL_HEIGHT))

        self.renderer = QuadRenderer(self.window)
        self.quad_shader = glShaderProgram(quad_vertex_src, quad_fragment_src)

        self.wallpaper = glTexture.loadTexture('res/wallpaper.jpg', GL_NEAREST)

        self.cam = Camera(glm.vec3(0.0, 0.0, 1.0), glm.radians(90), self.window.width / self.window.height, 0.1, 100)
        self.cam.lookAt(self.cam.position + glm.vec3(0, 0, -1))

        self.shader = glShaderProgram(
            """
            #version 330 core
            layout (location = 0) in vec3 aPos;
            layout (location = 1) in vec3 aNormal;
            layout (location = 2) in vec2 aUV;

            uniform mat4 m;

            out vec3 normal;
            out vec2 uv;

            void main() {
                gl_Position = m * vec4(aPos, 1.0);
                normal = aNormal;
                uv = aUV;
            }
            """,
            """
            #version 330 core

            out vec4 FragColor;

            uniform float t;

            in vec3 normal;
            in vec2 uv;

            void main() {
                float fractor = dot(normalize(normal), vec3(cos(t), 0.2, sin(t)));
                vec3 color = vec3(max(fractor, 0));
                // FragColor = vec4(1, uv, 1);
                FragColor = vec4(color, 1);
            }
            """
            )

        self.mesh = Mesh()
        self.mesh.loadGLB("res/Idle.glb")
        # self.mesh.loadGLB("res/Cube.glb")
        # self.mesh.loadGLB("res/GEKKOU_lowpoly.glb")

        glClearColor(0.1, 0.1, 0.1, 1)
        pg.mouse.set_visible(False)

    def onWindowKeyAction(self, key: int, mod: int, unicode: int, scancode: int):
        pass

    def onWindowMouseMotion(self, pos: tuple[int, int], rel: tuple[int, int], button: tuple[bool, bool, bool], touch: bool):
        sensitivity = 0.1

        if self.cam.rotation.y > 89.0:
            self.cam.rotation.y = 89.0
        if self.cam.rotation.y < -89.0:
            self.cam.rotation.y = -89.0

        dx, dy = rel[0], rel[1]

        # Lock cursor to the center of window
        self.last_mouse_pos = (self.window.width * 0.5, self.window.height * 0.5)
        pg.mouse.set_pos(self.last_mouse_pos)
        
        self.cam.rotate(glm.vec3(0, -dy * sensitivity, dx * sensitivity))

    def onWindowClose(self):
        self.renderer.delete()
        self.postProcessingPass.delete()
        self.mesh.delete()
        print('Close from Game')

    def onUpdate(self):
        self.window.dispatchEvent(self.eventHandler)

        # Render triangle to framebuffer
        self.postProcessingPass.bind()
        glClearColor(0.1, 0.1, 0.1, 1.0)

        t = pg.time.get_ticks() * 0.001

        ratio = self.wallpaper.height / self.wallpaper.width

        m = self.cam.projectionMat * self.cam.viewMat

        self.shader.bind()
        glBindVertexArray(self.mesh.vao)
        glUniformMatrix4fv(glGetUniformLocation(self.shader.program, "m"), 1, GL_FALSE, m.to_list())
        glUniform1f(glGetUniformLocation(self.shader.program, "t"), t)
        glDrawElements(GL_TRIANGLES, int(self.mesh.vbos.bufsStatus[0].size / 4), GL_UNSIGNED_INT, None)

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
        #             glUniformMatrix4fv(glGetUniformLocation(self.quad_shader.program, "m"), 1, GL_FALSE, m.to_list())
        #             self.renderer.clearBuffer()
        #             self.renderer.drawQuad(q)
        #
        # if self.renderer.vbIndex > 0:
        #     self.quad_shader.bind()
        #     self.wallpaper.bind(0)
        #     glUniform1i(glGetUniformLocation(self.quad_shader.program, "screenTexture"), 0)
        #     glUniformMatrix4fv(glGetUniformLocation(self.quad_shader.program, "m"), 1, GL_FALSE, m.to_list())
        #     self.renderer.submit()

        # Render fullscreen quad with post-processing
        glViewport(0, 0, self.window.width, self.window.height)
        self.postProcessingPass.unbind()
        self.postProcessingPass.render()

        keys = self.window.keys
        dir = glm.vec3(0, 0, 0)
        if keys[pg.K_w]:
            dir += self.cam.forward
        if keys[pg.K_s]:
            dir -= self.cam.forward
        if keys[pg.K_d]:
            dir += self.cam.right
        if keys[pg.K_a]:
            dir -= self.cam.right
        if keys[pg.K_SPACE]:
            dir += glm.vec3(0, 1, 0)
        if dir != glm.vec3(0):
            self.cam.position += glm.normalize(dir) / self.window.fps

def main() -> None:
    app = Game()
    app.run()

if __name__ == "__main__":
    main()

