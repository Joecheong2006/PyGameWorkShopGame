import pygame as pg
from Application import *
from opengl_util import *
from QuadRenderer import *
from RenderPipeline import PostProcessingPass, DepthNormalPass, ShadowPass
from Camera import *
from CameraController import *

from AnimationSystem import AnimationSystem
from GameObjectSystem import *

from Player import Player

from Model import Model

from QuadTest import QuadTest

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

        self.quadRenderer = QuadRenderer(self.window)
        self.quadShader = glShaderProgram(
                """
                #version 330 core
                layout (location = 0) in vec3 aPos;
                layout (location = 2) in vec2 aUV;

                uniform mat4 vp;
                uniform mat4 lvp;
                out vec2 uv;
                out vec4 lightFragPos;

                void main() {
                    gl_Position = vp * vec4(aPos, 1.0);
                    lightFragPos = lvp * vec4(aPos, 1.0);
                    uv = aUV;
                }
                """,
                """
                #version 330 core
                layout(location = 0) out vec4 fragColor;

                in vec2 uv;
                in vec4 lightFragPos;
                uniform sampler2D diffuseTexture;
                uniform vec3 lightDir;
                uniform vec3 lightColor;

                uniform sampler2D shadowMap;

                float getShadowFactor(in vec3 lightUV, in vec3 L) {
                    if (lightUV.z > 1)
                        lightUV.z = 1;
                    float depth = texture(shadowMap, lightUV.xy).r;
                    float sunHeight = dot(vec3(0, 1, 0), L);
                    sunHeight = clamp(1 - sunHeight, 0.1, 1);
                    return lightUV.z > depth + 0.001 ? 1 - pow(sunHeight - 1, 2) : 1.0;
                }

                void main() {
                    vec3 lightProjPos = lightFragPos.xyz / lightFragPos.w;
                    vec3 lightUV = lightProjPos * 0.5 + 0.5;

                    vec3 L = -normalize(lightDir);
                    float shadowFactor = getShadowFactor(lightUV, L);

                    vec4 color = texture(diffuseTexture, uv);
                    color.rgb *= vec3(0.515, 0.8, 0.552);

                    color.rgb = color.rgb * 0.7 * shadowFactor * lightColor;
                    fragColor = color;
                }
                """
                )

        glFramebuffer.initailizeQuad()

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

        self.depthNormalPass = DepthNormalPass(PIXEL_WIDTH, PIXEL_HEIGHT)

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
                    float depthOrg = texture(depthMapTexture, TexCoord).a;
                    vec2 texelSize = 1.0 / textureSize(depthMapTexture, 0);
                    depth += texture(depthMapTexture, TexCoord + vec2(0, 1) * texelSize).a;
                    depth += texture(depthMapTexture, TexCoord + vec2(0, -1) * texelSize).a;
                    depth += texture(depthMapTexture, TexCoord + vec2(1, 0) * texelSize).a;
                    depth += texture(depthMapTexture, TexCoord + vec2(-1, 0) * texelSize).a;
                    depth /= 4;

                    vec3 normalOrg = texture(depthMapTexture, TexCoord).rgb * 2 - 1;
                    vec3 normalUp = texture(depthMapTexture, TexCoord + vec2(0, 1) * texelSize).rgb * 2 - 1;

                    vec3 diff = vec3(1);
                    bool normalCheck = abs(dot(normalUp, normalOrg)) < 0.5;

                    vec3 color = texture(screenTexture, TexCoord).rgb;
                    if (depth - depthOrg > 0.0002) {
                        color *= color;
                    }
                    else if (normalCheck) {
                        diff = texture(screenTexture, TexCoord + vec2(0, 1) * texelSize).rgb;
                        diff += texture(screenTexture, TexCoord + vec2(0, -1) * texelSize).rgb;
                        diff += texture(screenTexture, TexCoord + vec2(1, 0) * texelSize).rgb;
                        diff += texture(screenTexture, TexCoord + vec2(-1, 0) * texelSize).rgb;
                        diff /= 4;
                        color *= diff;
                    }

                    color = pow(color, vec3(1.0 / 1.8));
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
        self.depthNormalPass.delete()
        self.shadowPass.delete()
        glFramebuffer.deleteQuad()
        self.quadRenderer.delete()
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

        t = pg.time.get_ticks() * 0.0001

        # Configure light camera
        playerLocation = GameObjectSystem.FindFirstObjectByType(Player).transform.position
        axis = glm.normalize(glm.vec3(1, 0, -1))
        position = glm.vec3(glm.rotate(glm.mat4(1.0), t, axis) * glm.vec4(-30, 0, -30, 1.0))
        aspect = self.window.width / self.window.height
        ortho = glm.ortho(-30, 30, -30 / aspect, 30 / aspect, 0.1, 100)
        forward = -glm.normalize(position)
        p = glm.vec3(0, 1, 0)
        rotation = glm.quatLookAt(-glm.normalize(position), p)
        target = position + forward
        view = glm.lookAt(position + playerLocation, target + playerLocation, rotation * p)
        vp = ortho * view
        lvp = vp.to_list()

        # Shadow Pass
        self.shadowPass.bind()
        self.shadowPass.enable()
        shader = self.shadowPass.getShader()
        shader.setUniformMat4("lvp", 1, lvp)
        shader.setUniform3f("lightPos", position)
        GameObjectSystem.RenderModel(shader)
        GameObjectSystem.RenderQuads(self.quadRenderer, shader)
        self.shadowPass.unbind()

        # Depth Normal Pass
        self.depthNormalPass.bind()
        self.depthNormalPass.enable()
        shader = self.depthNormalPass.getShader()
        GameObjectSystem.RenderModel(shader)
        GameObjectSystem.RenderQuads(self.quadRenderer, shader)
        self.depthNormalPass.unbind()

        # Render scene to framebuffer
        self.postProcessingPass.bind()
        shader = Model.shader
        shader.bind()

        self.shadowPass.shadowMapTexture.bind(1)
        shader.setUniform1i("shadowMap", 1)
        shader.setUniformMat4("lvp", 1, lvp)
        shader.setUniform3f("lightPos", position)
        shader.setUniform3f("lightDir", forward)

        sunHeight = glm.dot(glm.vec3(0, 1, 0), -forward)

        lightColor = glm.vec3(1)

        if sunHeight > 0:
            lightColor = glm.lerp(
                    glm.vec3(0.9, 0.4, 0.3), glm.vec3(1),
                    sunHeight)
        else:
            nightColor = glm.vec3(0.2, 0.5, 0.3);
            lightColor = glm.lerp(
                    glm.vec3(0.9, 0.4, 0.3), nightColor * 0.5,
                    -sunHeight)

        shader.setUniform3f("lightColor", lightColor)

        GameObjectSystem.RenderModel(shader)

        shader = self.quadShader
        shader.bind()
        shader.setUniform1i("shadowMap", 1)
        shader.setUniformMat4("lvp", 1, lvp)
        shader.setUniform3f("lightPos", position)
        shader.setUniform3f("lightDir", forward)
        shader.setUniform3f("lightColor", lightColor)
        GameObjectSystem.RenderQuads(self.quadRenderer, self.quadShader)

        delta_time: float = (pg.time.get_ticks() - previous_time)
        title += f"render: {delta_time}ms "
        pg.display.set_caption(title)

        self.postProcessingPass.unbind()

        # Reset resolution to window size
        glViewport(0, 0, self.window.width, self.window.height)
        glClear(int(GL_COLOR_BUFFER_BIT) | int(GL_DEPTH_BUFFER_BIT))

        # Enable post-processing
        self.postProcessingPass.enable()
        glBindVertexArray(glFramebuffer.quad_vao)

        # Binding screen texture
        self.postProcessingPass.screenTexture.bind(0)
        shader.setUniform1i("screenTexture", 0)

        # Binding depth normal map
        self.depthNormalPass.depthNormalMapTexture.bind(1)
        shader = self.postProcessingPass.getShader()
        shader.setUniform1i("depthMapTexture", 1)

        # Render fullscreen quad with post-processing
        glDrawArrays(GL_TRIANGLES, 0, 6)

        if self.lockCursor:
            pg.mouse.set_pos((self.window.width / 2, self.window.height / 2))

def main() -> None:
    app = Game()
    app.run()

if __name__ == "__main__":
    main()

