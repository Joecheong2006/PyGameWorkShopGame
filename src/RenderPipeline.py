from opengl_util import *

"""
RenderPipeline:
    ShadowPass
    ScenePass
    PostProcessingPass
"""

class ShadowPass:
    def __init__(self, shaderProgram: glShaderProgram, width: int, height: int):
        self.shadowMap = glFramebuffer(shaderProgram, width, height, quad=False)
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
        glCullFace(GL_FRONT);
        glEnable(GL_BLEND)

    def unbind(self):
        self.shadowMap.unbind()
        glCullFace(GL_BACK);

class PostProcessingPass:
    def __init__(self, shaderProgram: glShaderProgram, style: int, width: int, height: int):
        self._fb = glFramebuffer(shaderProgram, width, height)
        self._fb.bind()
        self._fb.genRenderBuffer(GL_DEPTH24_STENCIL8)
        self._fb.attachRenderBuffer(GL_DEPTH_STENCIL_ATTACHMENT)
        self._screenTexture = glTexture(self._fb.width, self._fb.height, style)
        self._fb.attachTexture(self._screenTexture)

        if not self._fb.isCompleted():
            raise RuntimeError("Imcompleted framebuffer")

        self._fb.unbind()

    def bind(self):
        self._fb.bind()
        glViewport(0, 0, self._fb.width, self._fb.height)
        glClear(int(GL_COLOR_BUFFER_BIT) | int(GL_DEPTH_BUFFER_BIT))

    def unbind(self):
        self._fb.unbind()

    def render(self):
        glClear(int(GL_COLOR_BUFFER_BIT) | int(GL_DEPTH_BUFFER_BIT))
        glUseProgram(self._fb.shader.program)
        glBindVertexArray(self._fb.quad_vao)
        self._screenTexture.bind(0)
        glUniform1i(glGetUniformLocation(self._fb.shader.program, "screenTexture"), 0)
        glDrawArrays(GL_TRIANGLES, 0, 6)

    def delete(self):
        self._fb.delete()
        self._screenTexture.delete()
