from opengl_util import *

"""
RenderPipeline:
    ShadowPass
    ScenePass
    PostProcessingPass
"""

class PostProcessingPass:
    def __init__(self, shaderProgram: glShaderProgram, style: int, screenBufferSize: tuple[int, int] = (0, 0)):
        self._fb = glFramebuffer(shaderProgram, screenBufferSize)
        self._screenTexture= glTexture(*screenBufferSize, style)
        self._fb.attachTexture(self._screenTexture)

        if not self._fb.isCompleted:
            raise RuntimeError("Imcompleted framebuffer")

    def bind(self):
        self._fb.bind()
        glViewport(0, 0, *self._fb.screenBufferSize)
        glClear(int(GL_COLOR_BUFFER_BIT) | int(GL_DEPTH_BUFFER_BIT))

    def unbind(self):
        self._fb.unbind()

    def render(self):
        glClear(int(GL_DEPTH_BUFFER_BIT))
        glUseProgram(self._fb.shader.program)
        glBindVertexArray(self._fb.quad_vao)
        self._screenTexture.bind(0)
        glUniform1i(glGetUniformLocation(self._fb.shader.program, "screenTexture"), 0)
        glDrawArrays(GL_TRIANGLES, 0, 6)

    def delete(self):
        self._fb.delete()
        self._screenTexture.delete()
