import pygame as pg
from Application import *
from opengl_util import *
from QuadRenderer import *
from Mesh import Mesh
from RenderPipeline import PostProcessingPass
from Camera import *

class Game(Application):
    def __init__(self):
        # scale = (4, 4)
        # PIXEL_WIDTH, PIXEL_HEIGHT = 320, 180
        scale = (1, 1)
        PIXEL_WIDTH, PIXEL_HEIGHT = 320 * 4, 180 * 4
        WINDOW_SIZE = (PIXEL_WIDTH * scale[0], PIXEL_HEIGHT * scale[1])

        super().__init__(WINDOW_SIZE)

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

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
        self.quad_shader = glShaderProgram(
                """
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
                """,
                """
                #version 330 core

                layout(location = 0) out vec4 frag_color;
                in vec2 uv;
                uniform sampler2D screenTexture;

                void main()
                {
                    vec4 color = texture(screenTexture, uv);
                    frag_color = color;
                }
                """)
        self.wallpaper = glTexture.loadTexture('res/GreenGrass.png', GL_NEAREST)

        self.cam = Camera(glm.vec3(0.0, 0.0, 1.0), glm.radians(45), self.window.width / self.window.height, 0.1, 100)
        self.cam.lookAt(self.cam.position + self.cam.forward)

        self.shader = glShaderProgram(
            """
            #version 330 core
            layout (location = 0) in vec3 aPos;
            layout (location = 1) in vec3 aNormal;
            layout (location = 2) in vec2 aUV;
            layout (location = 3) in uvec4 aJointIDs;
            layout (location = 4) in vec4 aWeights;

            uniform mat4 m;
            uniform mat4 model;
            uniform mat4 mn;

            uniform mat4 jointMatrices[100];

            out vec3 fragPos;
            out vec3 normal;
            out vec2 uv;

            out vec4 weights;
            flat out uvec4 boneIDs;

            void main() {
                gl_Position = m * model * vec4(aPos, 1.0);
                fragPos = vec3(model * vec4(aPos, 1.0));
                normal = (mn * vec4(aNormal, 1.0)).xyz;
                uv = aUV;

                weights = aWeights;
                boneIDs = aJointIDs;
            }
            """,
            """
            #version 330 core

            out vec4 FragColor;

            uniform float t;
            uniform vec3 color;
            uniform sampler2D diffuseTexture;
            uniform bool hasDiffuseTex;

            in vec3 fragPos;
            in vec3 normal;
            in vec2 uv;

            in vec4 weights;
            flat in uvec4 boneIDs;

            #define TOON_LEVEL 10.0

            void main() {
                bool found = false;
                for (int i = 0; i < 4; ++i) {
                    if (boneIDs[i] == uint(t) && weights[i] >= 0.1) {
                        vec3 color = vec3(1);
                        if (weights[i] >= 0.7) {
                            color = vec3(1, 0, 0) * weights[i];
                        }
                        else if (weights[i] >= 0.4) {
                            color = vec3(0, 1, 0) * weights[i];
                        }
                        else if (weights[i] >= 0.1) {
                            color = vec3(0, 0, 1) * weights[i];
                        }
                        FragColor = vec4(color, 1);
                        found = true;
                        break;
                    }
                }

                if (found)
                    return;

                vec3 N = normalize(normal);
                if (!gl_FrontFacing) {
                    N = -N;
                }

                float R = 2;
                vec3 lightPos = vec3(R * sin(t), 2, R * cos(t));
                vec3 lightDir = normalize(lightPos - fragPos);
                float factor = dot(N, lightDir);

                if (factor > 0) {
                    factor = ceil(factor * TOON_LEVEL) / TOON_LEVEL;
                }
                else {
                    factor = 0;
                }

                if (!hasDiffuseTex) {
                    FragColor = vec4(color * factor, 1);
                    return;
                }
                FragColor = vec4(texture(diffuseTexture, uv).rgb * factor, 1);
            }
            """
            )

        self.mesh = Mesh()
        # self.mesh.loadGLB("res/SportsCar.glb")
        # self.mesh.loadGLB("res/Dragon.glb")
        # self.mesh.loadGLB("res/AlienSoldier.glb")
        # self.mesh.loadGLB("res/Idle.glb")
        self.mesh.loadGLB("res/Ronin.glb")

        glClearColor(0.1, 0.1, 0.1, 1)

        self.lockCursor = True
        pg.event.set_grab(self.lockCursor)
        pg.mouse.set_visible(not self.lockCursor)
        pg.mouse.set_pos((self.window.width / 2, self.window.height / 2))
        pg.mouse.get_rel()

    def onWindowKeyAction(self, key: int, type: int, mod: int, unicode: int, scancode: int):
        if key == pg.K_ESCAPE and type == pg.KEYDOWN:
            self.lockCursor = not self.lockCursor
            pg.event.set_grab(self.lockCursor)
            pg.mouse.set_visible(not self.lockCursor)

    def onWindowMouseMotion(self, pos: tuple[int, int], rel: tuple[int, int], button: tuple[bool, bool, bool], touch: bool):
        sensitivity = 0.1

        if self.cam.rotation.y > 89.0:
            self.cam.rotation.y = 89.0
        if self.cam.rotation.y < -89.0:
            self.cam.rotation.y = -89.0

        dx, dy = rel[0], rel[1]
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

        previous_time = pg.time.get_ticks()
        self.shader.bind()
        glUniformMatrix4fv(glGetUniformLocation(self.shader.program, "m"), 1, GL_FALSE, m.to_list())
        glUniform1f(glGetUniformLocation(self.shader.program, "t"), t)
        self.mesh.render(self.shader)
        self.shader.unbind()
        delta_time: float = (pg.time.get_ticks() - previous_time) / 1000.0
        pg.display.set_caption(f'{delta_time}')

        # ratio = self.wallpaper.height / self.wallpaper.width
        # q = Quad((0.4, 0.4 * ratio), (0, 0), t)
        # self.quad_shader.bind()
        # self.wallpaper.bind(0)
        # glUniform1i(glGetUniformLocation(self.quad_shader.program, "screenTexture"), 0)
        # glUniformMatrix4fv(glGetUniformLocation(self.quad_shader.program, "m"), 1, GL_FALSE, m.to_list())
        # self.renderer.drawQuad(q)
        # self.renderer.submit()

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
            self.cam.lookAt(self.cam.position + self.cam.forward)
        
        if self.lockCursor:
            pg.mouse.set_pos((self.window.width / 2, self.window.height / 2))

def main() -> None:
    app = Game()
    app.run()

if __name__ == "__main__":
    main()

