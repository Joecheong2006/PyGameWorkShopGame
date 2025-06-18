from opengl_util import *

"""
RenderPipeline:
    ShadowPass
    ScenePass
    PostProcessingPass
"""

class ShadowPass:
    def __init__(self, shaderProgram: glShaderProgram, width: int, height: int):
        self.shadowMap = glFramebuffer(shaderProgram, width, height)
        self.shadowMap.bind()
        self.shadowMapTexture = glTexture(
                self.shadowMap.width, self.shadowMap.height, 
                GL_NEAREST, format=GL_DEPTH_COMPONENT, type=GL_FLOAT, mipmap=False, wrapStyle=GL_CLAMP_TO_BORDER)
        self.shadowMap.attachTexture(self.shadowMapTexture, attachment=GL_DEPTH_ATTACHMENT)

        glDrawBuffer(GL_NONE)
        glReadBuffer(GL_NONE)

        if not self.shadowMap.isCompleted():
            raise RuntimeError("Imcompleted framebuffer")

        self.shadowMap.unbind()

    def bind(self):
        self.shadowMap.bind()
        glViewport(0, 0, self.shadowMap.width, self.shadowMap.height)
        glClear(GL_DEPTH_BUFFER_BIT)

    def unbind(self):
        self.shadowMap.unbind()

    def delete(self):
        self.shadowMap.delete()
        self.shadowMapTexture.delete()

class DepthNormalPass:
    def __init__(self, width: int, height: int):
        depthShader = glShaderProgram(
                """
                #version 330 core
                layout (location = 0) in vec3 aPos;
                layout (location = 1) in vec3 aNormal;
                layout (location = 2) in vec2 aUV;
                layout (location = 3) in uvec4 aJointIDs;
                layout (location = 4) in vec4 aWeights;

                uniform mat4 vp;
                uniform mat4 model;

                uniform mat4 jointMatrices[100];
                uniform bool hasAnimation;
                out vec2 uv;
                out vec3 normal;

                void main() {
                    mat4 skinMatrix = mat4(1);
                    if (hasAnimation) {
                        skinMatrix =
                        aWeights.x * jointMatrices[aJointIDs.x] +
                        aWeights.y * jointMatrices[aJointIDs.y] +
                        aWeights.z * jointMatrices[aJointIDs.z] +
                        aWeights.w * jointMatrices[aJointIDs.w];
                    }
                    gl_Position = vp * model * skinMatrix * vec4(aPos, 1.0);
                    uv = aUV;
                    normal = aNormal;
                }
                """,
                """
                #version 330 core
                layout(location = 0) out vec4 fragColor;

                uniform sampler2D diffuseTexture;
                uniform bool hasDiffuseTex;
                in vec2 uv;
                in vec3 normal;

                void main() {
                    if (hasDiffuseTex && texture(diffuseTexture, uv).a < 0.1) {
                        discard;
                    }
                    fragColor = vec4(normal * 0.5 + 0.5, gl_FragCoord.z);
                }
                """)

        self.depthMap = glFramebuffer(depthShader, width, height)
        self.depthMap.bind()
        self.depthMap.genRenderBuffer(GL_DEPTH24_STENCIL8)
        self.depthMap.attachRenderBuffer(GL_DEPTH_STENCIL_ATTACHMENT)
        self.depthMapTexture = glTexture(
                self.depthMap.width, self.depthMap.height, 
                GL_NEAREST, type=GL_FLOAT, mipmap=False, wrapStyle=GL_CLAMP_TO_BORDER, internal=GL_RGBA16F)
        self.depthMap.attachTexture(self.depthMapTexture)

        if not self.depthMap.isCompleted():
            raise RuntimeError("Imcompleted framebuffer")

        self.depthMap.unbind()
    
    def bind(self):
        self.depthMap.bind()
        glViewport(0, 0, self.depthMap.width, self.depthMap.height)
        glClear(int(GL_COLOR_BUFFER_BIT) | int(GL_DEPTH_BUFFER_BIT))
        glDisable(GL_BLEND);

    def unbind(self):
        glEnable(GL_BLEND);
        self.depthMap.unbind()

class PostProcessingPass:
    def __init__(self, shaderProgram: glShaderProgram, style: int, width: int, height: int):
        self.fb = glFramebuffer(shaderProgram, width, height)
        self.fb.bind()
        self.fb.genRenderBuffer(GL_DEPTH24_STENCIL8)
        self.fb.attachRenderBuffer(GL_DEPTH_STENCIL_ATTACHMENT)
        self.screenTexture = glTexture(self.fb.width, self.fb.height, style)
        self.fb.attachTexture(self.screenTexture)

        if not self.fb.isCompleted():
            raise RuntimeError("Imcompleted framebuffer")

        self.fb.unbind()

    def bind(self):
        self.fb.bind()
        glViewport(0, 0, self.fb.width, self.fb.height)
        glClear(int(GL_COLOR_BUFFER_BIT) | int(GL_DEPTH_BUFFER_BIT))

    def unbind(self):
        self.fb.unbind()

    def enable(self):
        glUseProgram(self.fb.shader.program)

    def delete(self):
        self.fb.delete()
        self.screenTexture.delete()
