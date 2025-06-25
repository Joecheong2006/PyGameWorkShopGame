from opengl_util import *

class Quad:
    def __init__(self, size: tuple[float, float] = (1 ,1), pos: tuple[float, float] = (0, 0), angle: float = 0):
        self.size = size
        self.pos = pos
        self.angle = angle

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

        # UV (location = 1)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(3 * 4))

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

        ratioy = self.window.height / self.window.width
        size = np.array(q.size, dtype=np.float32) * 0.5
        pos = np.array([q.pos[0] * ratioy, q.pos[1]], dtype=np.float32)

        cur = self.vbIndex / 5;
        self.indexBuff[self.ibIndex] = cur + 0;
        self.indexBuff[self.ibIndex + 1] = cur + 1;
        self.indexBuff[self.ibIndex + 2] = cur + 3;
        self.indexBuff[self.ibIndex + 3] = cur + 0;
        self.indexBuff[self.ibIndex + 4] = cur + 2;
        self.indexBuff[self.ibIndex + 5] = cur + 3;
        self.ibIndex += 6;

        # Memory Layout: 
        #   (loc = 0) position: 3 x f32 = 12bytes
        #   (loc = 1) uv: 2 x f32 = 8bytes

        c, s = np.cos(q.angle), np.sin(q.angle)
        mat = np.array([
            [c, -s],
            [s,  c]
        ], dtype=np.float32);

        v1 = mat @ np.array([-size[0], -size[1]], dtype=np.float32)
        v2 = mat @ np.array([-size[0], size[1]], dtype=np.float32)

        self.vertexBuff[self.vbIndex] = pos[0] + v1[0] * ratioy;
        self.vertexBuff[self.vbIndex + 1] = pos[1] + v1[1];
        self.vertexBuff[self.vbIndex + 2] = 0;

        self.vertexBuff[self.vbIndex + 3] = 0;
        self.vertexBuff[self.vbIndex + 4] = 0;

        self.vertexBuff[self.vbIndex + 5] = pos[0] + v2[0] * ratioy;
        self.vertexBuff[self.vbIndex + 6] = pos[1] + v2[1];
        self.vertexBuff[self.vbIndex + 7] = 0;

        self.vertexBuff[self.vbIndex + 8] = 0;
        self.vertexBuff[self.vbIndex + 9] = 1;

        self.vertexBuff[self.vbIndex + 10] = pos[0] - v2[0] * ratioy;
        self.vertexBuff[self.vbIndex + 11] = pos[1] - v2[1];
        self.vertexBuff[self.vbIndex + 12] = 0;

        self.vertexBuff[self.vbIndex + 13] = 1;
        self.vertexBuff[self.vbIndex + 14] = 0;

        self.vertexBuff[self.vbIndex + 15] = pos[0] - v1[0] * ratioy;
        self.vertexBuff[self.vbIndex + 16] = pos[1] - v1[1];
        self.vertexBuff[self.vbIndex + 17] = 0;

        self.vertexBuff[self.vbIndex + 18] = 1;
        self.vertexBuff[self.vbIndex + 19] = 1;
        self.vbIndex += 20;

    def submit(self):
        self.vbo.setBuffer(self.vertexBuff, self.vertexBuff.nbytes)
        self.ibo.setBuffer(self.indexBuff, self.indexBuff.size)

        glBindVertexArray(self.vao)
        glDrawElements(GL_TRIANGLES, self.ibIndex, GL_UNSIGNED_INT, None)
        self.vbIndex = 0;
        self.ibIndex = 0;

    def delete(self):
        glDeleteVertexArrays(1, [self.vao])
        self.vbo.delete()
        self.ibo.delete()
