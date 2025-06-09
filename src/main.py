import pygame as pg
from Application import *
from opengl_util import *
from QuadRenderer import *
from Model import Model
from Animator import Animator
from RenderPipeline import PostProcessingPass
from Camera import *
from CameraController import *

from AnimationSystem import AnimationSystem
from GameObjectSystem import *

class Player(GameObject):
    def __init__(self):
        super().__init__(self)

    def OnStart(self):
        self.model = Model("res/M.glb")
        # self.model = Model("res/Kick.glb")
        # self.model = Model("res/Capoeira.glb")
        # self.model = Model("res/AlienSoldier.glb")
        # self.model = Model("res/TestScene2.glb")
        # self.model = Model("res/Ronin.glb")
        # self.model = Model("res/Monkey.glb")

        self.animator = Animator(self.model)
        self.animator.setDefaultState("Idle")
        self.animator.addAnimationState("FastRunning")

        AnimationSystem.AddAnimation(self.animator)

        self.running: bool = False
        self.runningDir = glm.vec3(0)

        def startPlayBack(animator: Animator):
            return self.running

        def endPlayBack(animator: Animator):
            return not self.running

        self.animator.addTransition("Idle", "FastRunning", 0.12, startPlayBack)
        self.animator.addTransition("FastRunning", "Idle", 0.14, endPlayBack)

    def OnUpdate(self, window: Window):
        keys = window.keys

        self.running = keys[pg.K_k]
        newDir = glm.vec3(keys[pg.K_a] - keys[pg.K_d], 0, keys[pg.K_w] - keys[pg.K_s])
        if newDir != glm.vec3(0):
            self.runningDir = newDir
            self.model.transform.rotation = glm.angleAxis(glm.atan(self.runningDir[0], self.runningDir[2]), glm.vec3(0, 1, 0))

        cam = GameObjectSystem.gameObjects[0].inher

class Game(Application):
    def __init__(self):
        AnimationSystem.SetUp()
        scale = (4, 4)
        PIXEL_WIDTH, PIXEL_HEIGHT = 320, 180
        # scale = (1, 1)
        # PIXEL_WIDTH, PIXEL_HEIGHT = 320 * 4, 180 * 4

        WINDOW_SIZE = (PIXEL_WIDTH * scale[0], PIXEL_HEIGHT * scale[1])

        # Initalize Context
        super().__init__(WINDOW_SIZE)

        glEnable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE);

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Initialize Systems
        AnimationSystem.SetUp()
        GameObjectSystem.SetUp()

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
        # self.wallpaper = glTexture.loadTexture('res/GreenGrass.png', GL_NEAREST)

        self.cam = Camera(glm.vec3(0.0, 1.0, 3.0), self.window)
        CameraController()

        print(f'GL_MAX_UNIFORM_BLOCK_SIZE: {glGetIntegerv(GL_MAX_UNIFORM_BLOCK_SIZE)}')

        self.player = Player()

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

        AnimationSystem.Update(self.window.deltaTime)
        GameObjectSystem.Update(self.window)

        # Render triangle to framebuffer
        self.postProcessingPass.bind()
        glClearColor(0.1, 0.1, 0.1, 1.0)

        previous_time = pg.time.get_ticks()
        self.player.model.render(self.cam)
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

