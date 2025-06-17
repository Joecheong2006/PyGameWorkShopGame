import pygame as pg
from Application import *
from opengl_util import *
from QuadRenderer import *
from RenderPipeline import PostProcessingPass, DepthPass, ShadowPass
from Camera import *
from CameraController import *

from AnimationSystem import AnimationSystem
from GameObjectSystem import *

from Player import Player

from Model import Model

class Game(Application):
    def __init__(self):
        scale = (2, 2)
        PIXEL_WIDTH, PIXEL_HEIGHT = int(320 * 2.25), int(180 * 2.25)
        # scale = (1, 1)
        # PIXEL_WIDTH, PIXEL_HEIGHT = 320 * 4, 180 * 4

        WINDOW_SIZE = (PIXEL_WIDTH * scale[0], PIXEL_HEIGHT * scale[1])

        # Initalize Context
        super().__init__(WINDOW_SIZE)

        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK);

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

        self.depthPass = DepthPass(PIXEL_WIDTH, PIXEL_HEIGHT)

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

                layout(location = 0) out vec4 fragColor;
                in vec2 TexCoord;
                uniform sampler2D screenTexture;
                uniform sampler2D depthMapTexture;

                void main()
                {
                    float depth = 0;
                    float depthOrg = texture(depthMapTexture, TexCoord).r;
                    vec2 texelSize = 1.0 / textureSize(depthMapTexture, 0);
                    depth += texture(depthMapTexture, TexCoord + vec2(0, 1) * texelSize).r;
                    depth += texture(depthMapTexture, TexCoord + vec2(0, -1) * texelSize).r;
                    depth += texture(depthMapTexture, TexCoord + vec2(1, 0) * texelSize).r;
                    depth += texture(depthMapTexture, TexCoord + vec2(-1, 0) * texelSize).r;
                    depth /= 4;

                    vec3 diff = vec3(1);
                    if (depth - depthOrg > 0.0001) {
                        diff = texture(screenTexture, TexCoord + vec2(0, 1) * texelSize).rgb;
                        diff += texture(screenTexture, TexCoord + vec2(0, -1) * texelSize).rgb;
                        diff += texture(screenTexture, TexCoord + vec2(1, 0) * texelSize).rgb;
                        diff += texture(screenTexture, TexCoord + vec2(-1, 0) * texelSize).rgb;
                        diff /= 4;
                    }

                    vec3 color = texture(screenTexture, TexCoord).rgb * diff;
                    color = pow(color.rgb, vec3(1.0 / 2));
                    fragColor = vec4(color, 1);
                }
                """
                )
        self.postProcessingPass = PostProcessingPass(postProcessingShader, GL_NEAREST, PIXEL_WIDTH, PIXEL_HEIGHT)

        CameraController()
        self.cam = Camera(glm.vec3(0.0, 1.0, 3.0), self.window)

        print(f'GL_MAX_UNIFORM_BLOCK_SIZE: {glGetIntegerv(GL_MAX_UNIFORM_BLOCK_SIZE)}')

        Player()
        # Model("res/TestScene3.glb")
        Model("res/TestScene5.glb")

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
        self.postProcessingPass.delete()
        self.shadowPass.delete()
        print('Close from Game')

    def OnUpdate(self):
        self.window.dispatchEvent(self.eventHandler)

        title = ""

        previous_time = pg.time.get_ticks()
        AnimationSystem.Update(self.window.deltaTime)
        delta_time: float = (pg.time.get_ticks() - previous_time)
        title += f"anim: {delta_time}ms "

        previous_time = pg.time.get_ticks()
        GameObjectSystem.Update(self.window)
        delta_time: float = (pg.time.get_ticks() - previous_time)
        title += f"obj: {delta_time}ms "

        previous_time = pg.time.get_ticks()

        t = pg.time.get_ticks() * 0.0003

        # Shadow Pass
        self.shadowPass.bind()

        # position = 5 * glm.vec3(glm.sin(t), 1, -glm.cos(t))
        axis = glm.normalize(glm.vec3(1, 0, -1))
        position = glm.vec3(glm.rotate(glm.mat4(1.0), t, axis) * glm.vec4(-10, 0, -10, 1.0))
        aspect = self.window.width / self.window.height
        ortho = glm.ortho(-20, 20, -20 / aspect, 20 / aspect, 0.1, 100)
        forward = -glm.normalize(position)
        p = glm.vec3(0, 1, 0)
        rotation = glm.quatLookAt(-glm.normalize(position), p)
        target = position + forward
        view = glm.lookAt(position, target, rotation * p)
        vp = ortho * view
        lvp = vp.to_list()

        self.shadowPass.shadowMap.shader.bind()
        self.shadowPass.shadowMap.shader.setUniformMat4("lvp", 1, lvp)

        GameObjectSystem.RenderScene(self.shadowPass.shadowMap.shader)

        self.shadowPass.unbind()

        # Depth Pass
        self.depthPass.bind()
        self.depthPass.depthMap.shader.bind()
        GameObjectSystem.RenderScene(self.depthPass.depthMap.shader)
        self.depthPass.depthMap.unbind()

        # Render triangle to framebuffer
        self.postProcessingPass.bind()
        glClearColor(0.1, 0.1, 0.1, 1.0)

        Model.shader.bind()

        self.shadowPass.shadowMapTexture.bind(1)
        Model.shader.setUniform1i("shadowMap", 1)
        Model.shader.setUniformMat4("lvp", 1, lvp)
        Model.shader.setUniform3f("lightDir", forward)

        sunHeight = glm.dot(glm.vec3(0, 1, 0), -forward)

        lightColor = glm.vec3(0.8, 0.5, 0.3)
        lightColor = glm.vec3(1)

        if sunHeight > 0:
            lightColor = glm.lerp(
                    glm.vec3(0.8, 0.5, 0.3), glm.vec3(1),
                    sunHeight)
        else:
            lightColor = glm.lerp(
                    glm.vec3(0.8, 0.5, 0.3), glm.vec3(0.2, 0.5, 0.5) * 0.5,
                    -sunHeight)

        Model.shader.setUniform3f("lightColor", lightColor)

        # Render Scene to screen texture
        GameObjectSystem.RenderScene(Model.shader)

        delta_time: float = (pg.time.get_ticks() - previous_time)
        title += f"render: {delta_time}ms "
        pg.display.set_caption(title)

        # Render fullscreen quad with post-processing
        glViewport(0, 0, self.window.width, self.window.height)
        self.postProcessingPass.unbind()
        self.postProcessingPass.enable()

        # # binding depth map
        self.depthPass.depthMapTexture.bind(1)
        self.postProcessingPass.fb.shader.setUniform1i("depthMapTexture", 1)

        self.postProcessingPass.render()

        if self.lockCursor:
            pg.mouse.set_pos((self.window.width / 2, self.window.height / 2))

def main() -> None:
    app = Game()
    app.run()

if __name__ == "__main__":
    main()

