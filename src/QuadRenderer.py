from opengl_util import *
from pyglm import glm

class Quad:
    def __init__(self, size: glm.vec2 = glm.vec2(1.0), pos: glm.vec3 = glm.vec3(0.0), rotation: glm.quat = glm.quat(glm.vec3(0))):
        self.size: glm.vec3 = glm.vec3(size[0], size[1], 0)
        self.pos: glm.vec3 = pos
        self.rotation: glm.quat = rotation
        self.vertices = np.array([glm.vec3(0.0)] * 4)
        self.updateVertices()

        self.onRender = lambda quad, shader: None

    def updateVertices(self):
        hsize = self.size * 0.5
        self.vertices[0] = self.rotation * (self.pos + hsize)
        self.vertices[1] = self.rotation * (self.pos + glm.vec3(-hsize[0], hsize[1], hsize[2]))
        self.vertices[2] = self.rotation * (self.pos + glm.vec3(hsize[0], -hsize[1], hsize[2]))
        self.vertices[3] = self.rotation * (self.pos - glm.vec3(hsize[0], hsize[1], hsize[2]))

class QuadRenderer:
    def __init__(self, window: Window, quads_size: int = 4000):
        self.quads_size = quads_size
        self.vertexBuff = np.zeros(quads_size, dtype=np.float32)
        self.indexBuff = np.zeros(quads_size, dtype=np.uint32)
        self.window = window

        self.vao = glGenVertexArrays(1)
        self.vbo = glVertexBuffer(self.vertexBuff, self.vertexBuff.nbytes, GL_DYNAMIC_DRAW)

        glBindVertexArray(self.vao)

        stride = 5 * 4
        # Position (location = 0)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))

        # UV (location = 2)
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(3 * 4))

        self.ibo = glIndexBuffer(self.indexBuff, self.indexBuff.size);
        self.vbIndex = 0
        self.ibIndex = 0
        self.full = False

    def clearBuffer(self):
        self.vbIndex = 0
        self.ibIndex = 0
        self.full = False

    def drawQuad(self, q: Quad):
        if self.vbIndex >= self.quads_size - 12 - 8:
            self.full = True
            return

        if self.vbIndex >= self.quads_size - 6:
            self.full = True
            return

        cur = self.vbIndex / 5;
        self.indexBuff[self.ibIndex + 0] = cur + 0;
        self.indexBuff[self.ibIndex + 1] = cur + 1;
        self.indexBuff[self.ibIndex + 2] = cur + 3;
        self.indexBuff[self.ibIndex + 3] = cur + 0;
        self.indexBuff[self.ibIndex + 4] = cur + 2;
        self.indexBuff[self.ibIndex + 5] = cur + 3;
        self.ibIndex += 6;

        # Memory Layout: 
        #   (loc = 0) position: 3 x f32 = 12bytes
        #   (loc = 2) uv: 2 x f32 = 8bytes

        self.vertexBuff[self.vbIndex + 0] = q.vertices[0][0];
        self.vertexBuff[self.vbIndex + 1] = q.vertices[0][1];
        self.vertexBuff[self.vbIndex + 2] = q.vertices[0][2];

        self.vertexBuff[self.vbIndex + 3] = 0;
        self.vertexBuff[self.vbIndex + 4] = 0;

        self.vertexBuff[self.vbIndex + 5] = q.vertices[1][0];
        self.vertexBuff[self.vbIndex + 6] = q.vertices[1][1];
        self.vertexBuff[self.vbIndex + 7] = q.vertices[1][2];

        self.vertexBuff[self.vbIndex + 8] = 0;
        self.vertexBuff[self.vbIndex + 9] = 1;

        self.vertexBuff[self.vbIndex + 10] = q.vertices[2][0];
        self.vertexBuff[self.vbIndex + 11] = q.vertices[2][1];
        self.vertexBuff[self.vbIndex + 12] = q.vertices[2][2];

        self.vertexBuff[self.vbIndex + 13] = 1;
        self.vertexBuff[self.vbIndex + 14] = 0;

        self.vertexBuff[self.vbIndex + 15] = q.vertices[3][0];
        self.vertexBuff[self.vbIndex + 16] = q.vertices[3][1];
        self.vertexBuff[self.vbIndex + 17] = q.vertices[3][2];

        self.vertexBuff[self.vbIndex + 18] = 1;
        self.vertexBuff[self.vbIndex + 19] = 1;
        self.vbIndex += 20;

    def submit(self):
        glBindVertexArray(self.vao)
        self.vbo.setBuffer(self.vertexBuff, self.vertexBuff.nbytes)
        self.ibo.setBuffer(self.indexBuff, self.indexBuff.size)

        glDrawElements(GL_TRIANGLES, self.ibIndex, GL_UNSIGNED_INT, None)
        self.vbIndex = 0;
        self.ibIndex = 0;

    def delete(self):
        glDeleteVertexArrays(1, [self.vao])
        self.vbo.delete()
        self.ibo.delete()
