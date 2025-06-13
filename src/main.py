import pygame as pg
from Application import *
from opengl_util import *
from QuadRenderer import *
from RenderPipeline import PostProcessingPass, ShadowPass
from Camera import *
from CameraController import *

from AnimationSystem import AnimationSystem
from GameObjectSystem import *

from Player import Player

from Model import Model

class Game(Application):
    def __init__(self):
        scale = (3, 3)
        PIXEL_WIDTH, PIXEL_HEIGHT = int(320 * 1.5), int(180 * 1.5)
        # scale = (1, 1)
        # PIXEL_WIDTH, PIXEL_HEIGHT = 320 * 4, 180 * 4

        WINDOW_SIZE = (PIXEL_WIDTH * scale[0], PIXEL_HEIGHT * scale[1])

        # Initalize Context
        super().__init__(WINDOW_SIZE)

        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Initialize Systems
        AnimationSystem.SetUp()
        GameObjectSystem.SetUp()

        shadowMapShader = glShaderProgram(
                """
                #version 330 core
                layout (location = 0) in vec3 aPos;
                layout (location = 2) in vec2 aUV;
                layout (location = 3) in uvec4 aJointIDs;
                layout (location = 4) in vec4 aWeights;

                uniform mat4 lvp;
                uniform mat4 model;

                uniform mat4 jointMatrices[100];
                uniform bool hasAnimation;
                out vec2 uv;

                void main() {
                    mat4 skinMatrix = mat4(1);
                    if (hasAnimation) {
                        skinMatrix =
                        aWeights.x * jointMatrices[aJointIDs.x] +
                        aWeights.y * jointMatrices[aJointIDs.y] +
                        aWeights.z * jointMatrices[aJointIDs.z] +
                        aWeights.w * jointMatrices[aJointIDs.w];
                    }
                    gl_Position = lvp * model * skinMatrix * vec4(aPos, 1.0);
                    uv = aUV;
                }
                """,
                """
                #version 330 core

                uniform sampler2D diffuseTexture;
                uniform bool hasDiffuseTex;
                in vec2 uv;

                void main() {
                    if (hasDiffuseTex && texture(diffuseTexture, uv).a < 0.1) {
                        discard;
                    }
                }
                """
                )

        self.shadowPass = ShadowPass(shadowMapShader, 2048, 2048)

        postProcessingShader = glShaderProgram(
                """
                #version 330 core
                layout (location = 0) in vec2 aPos;
                layout (location = 1) in vec2 aTexCoord;
                out vec2 TexCoord;

                void main() {
                    TexCoord = aTexCoord;
                    gl_Position = vec4(aPos, 0, 1.0);
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
        self.postProcessingPass = PostProcessingPass(postProcessingShader, GL_NEAREST, PIXEL_WIDTH, PIXEL_HEIGHT)

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
        # self.wallpaper = glTexture.loadTexture('res/GreenGrass.png', GL_NEAREST)

        CameraController()
        self.cam = Camera(glm.vec3(0.0, 1.0, 3.0), self.window)

        print(f'GL_MAX_UNIFORM_BLOCK_SIZE: {glGetIntegerv(GL_MAX_UNIFORM_BLOCK_SIZE)}')

        self.player = Player()
        self.scene = Model("res/TestScene3.glb")

        glClearColor(0.1, 0.1, 0.1, 1)

        self.lockCursor = True
        pg.event.set_grab(self.lockCursor)
        pg.mouse.set_visible(not self.lockCursor)
        pg.mouse.set_pos((self.window.width / 2, self.window.height / 2))
        pg.mouse.get_rel()

    def OnWindowKeyAction(self, key: int, type: int, mod: int, unicode: int, scancode: int):
        if key == pg.K_ESCAPE and type == pg.KEYDOWN:
            self.lockCursor = not self.lockCursor
            pg.event.set_grab(self.lockCursor)
            pg.mouse.set_visible(not self.lockCursor)

    def OnWindowClose(self):
        self.renderer.delete()
        self.postProcessingPass.delete()
        self.player.model.delete()
        print('Close from Game')

    def OnUpdate(self):
        self.window.dispatchEvent(self.eventHandler)

        previous_time = pg.time.get_ticks()

        AnimationSystem.Update(self.window.deltaTime)
        GameObjectSystem.Update(self.window)

        t = pg.time.get_ticks() * 0.0003

        # Shadow Pass
        self.shadowPass.bind()

        dummyCamera = Camera(10 * glm.vec3(glm.sin(t), 1, -glm.cos(t)), self.window)
        dummyCamera.calOrthogonalMat(OrthogonalCameraState(-30, 30, -30 / self.cam.aspect, 30 / self.cam.aspect, 0.1, 100))
        dummyCamera.rotation = glm.quatLookAt(-glm.normalize(dummyCamera.position), dummyCamera.up())
        vp = dummyCamera.projectionMat * dummyCamera.getViewMatrix()
        lvp = vp.to_list()

        self.shadowPass.shadowMap.shader.bind()
        self.shadowPass.shadowMap.shader.setUniformMat4("lvp", 1, lvp)

        self.scene.render(self.shadowPass.shadowMap.shader, self.cam)
        self.player.model.render(self.shadowPass.shadowMap.shader, self.cam)

        self.shadowPass.unbind()

        # Render triangle to framebuffer
        self.postProcessingPass.bind()
        glClearColor(0.1, 0.1, 0.1, 1.0)

        Model.shader.bind()

        self.shadowPass.shadowMapTexture.bind(1)
        Model.shader.setUniform1i("shadowMap", 1)
        Model.shader.setUniformMat4("lvp", 1, lvp)
        Model.shader.setUniform3f("lightDir", dummyCamera.forward())

        self.scene.render(Model.shader, self.cam)
        self.player.model.render(Model.shader, self.cam)

        delta_time: float = (pg.time.get_ticks() - previous_time)
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

        if self.lockCursor:
            pg.mouse.set_pos((self.window.width / 2, self.window.height / 2))

def main() -> None:
    app = Game()
    app.run()

if __name__ == "__main__":
    main()

