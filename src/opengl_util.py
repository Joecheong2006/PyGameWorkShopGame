from Window import Window
from OpenGL.GL import *
import numpy as np

class glVertexBuffer:
    def __init__(self, data, size: int, usage: int):
        self._id = glGenBuffers(1)
        self.usage = usage
        self.setBuffer(data, size)

    def bind(self):
        glBindBuffer(GL_ARRAY_BUFFER, self._id)

    def unbind(self):
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def setBuffer(self, data, size):
        self.bind();
        glBufferData(GL_ARRAY_BUFFER, size, data, self.usage)
        self.size = size
        self.data = data

    def delete(self):
        glDeleteBuffers(1, [self._id])

class glIndexBuffer:
    def __init__(self, data, count: int):
        self._id = glGenBuffers(1)
        self.count = count
        self.setBuffer(data, count)

    def bind(self):
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self._id);

    def unbind(self):
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0);

    def setBuffer(self, data, count):
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self._id);
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, 4 * count, data, GL_STATIC_DRAW);

    def delete(self):
        glDeleteBuffers(1, [self._id])

def compile_shader(src: str, type: int):
    shader = glCreateShader(type)
    glShaderSource(shader, src)
    glCompileShader(shader)
    if glGetShaderiv(shader, GL_COMPILE_STATUS) != GL_TRUE:
        raise RuntimeError(glGetShaderInfoLog(shader).decode())
    return shader

def create_program(vs_src: str, fs_src: str):
    vs = compile_shader(vs_src, GL_VERTEX_SHADER)
    fs = compile_shader(fs_src, GL_FRAGMENT_SHADER)
    prog = glCreateProgram()
    glAttachShader(prog, vs)
    glAttachShader(prog, fs)
    glLinkProgram(prog)
    if glGetProgramiv(prog, GL_LINK_STATUS) != GL_TRUE:
        raise RuntimeError(glGetProgramInfoLog(prog).decode())
    glDeleteShader(vs)
    glDeleteShader(fs)
    return prog

class glShaderProgram:
    def __init__(self, vertex_src: str, fragment_src: str):
        self.vertex_src = vertex_src
        self.fragment_src =fragment_src 
        self.program = create_program(vertex_src, fragment_src);

    def bind(self):
        glUseProgram(self.program)

    def unbind(self):
        glUseProgram(0)

    def delete(self):
        glDeleteProgram(self.program);

class glTexture:
    def __init__(self, width: int, height: int, style: int, data = None):
        self._id = glGenTextures(1)
        self.width = width
        self.height = height
        self.bind()
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)

        glGenerateMipmap(GL_TEXTURE_2D)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, style)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, style)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

    def bind(self, slot: int = 0):
        glActiveTexture(int(GL_TEXTURE0) + slot)
        glBindTexture(GL_TEXTURE_2D, self._id)

    def unbind(self):
        glBindTexture(GL_TEXTURE_2D, 0)

    def delete(self):
        glDeleteTextures(1, [self._id])

class glFramebuffer:
    quad_vertices = np.array([
        # positions    # texCoords
        -1.0,  1.0,     0.0, 1.0,
        -1.0, -1.0,     0.0, 0.0,
         1.0, -1.0,     1.0, 0.0,

        -1.0,  1.0,     0.0, 1.0,
         1.0, -1.0,     1.0, 0.0,
         1.0,  1.0,     1.0, 1.0
    ], dtype=np.float32)

    def __init__(self, shaderProgram: glShaderProgram, screenBufferSize: tuple[int, int] = (0, 0)):
        self.screenBufferSize = screenBufferSize
        self.quad_vao = glGenVertexArrays(1)
        self.quad_vbo = glGenBuffers(1)
        self.shader = shaderProgram
        glBindVertexArray(self.quad_vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.quad_vbo)
        glBufferData(GL_ARRAY_BUFFER, self.quad_vertices.nbytes, self.quad_vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * self.quad_vertices.itemsize, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * self.quad_vertices.itemsize, ctypes.c_void_p(8))
        glEnableVertexAttribArray(1)
        self.fbo = glGenFramebuffers(1)

    def attachTexture(self, texture: glTexture):
        self.bind()
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, texture._id, 0)
        self.unbind()

    def bind(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)

    def unbind(self):
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def delete(self):
        self.shader.delete()
        glDeleteVertexArrays(1, [self.quad_vao])
        glDeleteBuffers(1, [self.quad_vbo])
        glDeleteFramebuffers(1, [self.fbo])

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
        self.vbo = glVertexBuffer(None, 0, GL_DYNAMIC_DRAW);

        glBindVertexArray(self.vao)

        stride = 5 * 4
        # Position (location = 0)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))

        # UV (location = 1)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(3 * 4))

        self.ibo = glIndexBuffer(None, 0);
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
