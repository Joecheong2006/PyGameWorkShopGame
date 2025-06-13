from Window import Window
from OpenGL.GL import *
import numpy as np
from PIL import Image

class glBufferStatus:
    def __init__(self, size: int, usage: int):
        self.size = size
        self.usage = usage

class glBuffers:
    def __init__(self, buffersCount: int):
        self._bufs = glGenBuffers(buffersCount)
        self.bufsStatus = [glBufferStatus(0, 0)] * buffersCount * 2
        self.count = buffersCount

    def bindVertexBuffer(self, bufferIndex: int):
        glBindBuffer(GL_ARRAY_BUFFER, self._bufs[bufferIndex])

    def setVertexBuffer(self, bufferIndex: int, data, size: int, usage: int):
        self.bindVertexBuffer(bufferIndex)
        glBufferData(GL_ARRAY_BUFFER, size, data, usage)
        self.bufsStatus[bufferIndex] = glBufferStatus(size, usage)

    def bindIndexBuffer(self, bufferIndex: int):
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self._bufs[bufferIndex]);

    def setIndexBuffer(self, bufferIndex: int, data, count: int, usage: int) -> None:
        self.bindIndexBuffer(bufferIndex)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, 4 * count, data, usage);
        self.bufsStatus[bufferIndex] = glBufferStatus(4 * count, usage)

    def delete(self):
        glDeleteBuffers(self.count, self._bufs)

class glVertexBuffer:
    def __init__(self, data, size: int, usage: int):
        self._id = glGenBuffers(1)
        self.usage = usage
        self.setBuffer(data, size)

    def bind(self) -> None:
        glBindBuffer(GL_ARRAY_BUFFER, self._id)

    def unbind(self) -> None:
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def setBuffer(self, data, size: int) -> None:
        self.bind();

        glBufferData(GL_ARRAY_BUFFER, size, data, self.usage)
        self.size = size
        self.data = data

    def delete(self) -> None:
        glDeleteBuffers(1, [self._id])

class glIndexBuffer:
    def __init__(self, data, count: int):
        self._id = glGenBuffers(1)
        self.count = count
        self.setBuffer(data, count)

    def bind(self) -> None:
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self._id);

    def unbind(self) -> None:
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0);

    def setBuffer(self, data, count: int) -> None:
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self._id);
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, 4 * count, data, GL_STATIC_DRAW);

    def delete(self) -> None:
        glDeleteBuffers(1, [self._id])

def compile_shader(src: str, type: int) -> int:
    shader = glCreateShader(type)
    if shader is None:
        raise RuntimeError("Failed to create shader")

    glShaderSource(shader, src)
    glCompileShader(shader)
    if glGetShaderiv(shader, GL_COMPILE_STATUS) != GL_TRUE:
        raise RuntimeError(glGetShaderInfoLog(shader).decode())
    return int(shader)

def create_program(vs_src: str, fs_src: str) -> int:
    vs = compile_shader(vs_src, GL_VERTEX_SHADER)
    fs = compile_shader(fs_src, GL_FRAGMENT_SHADER)
    program = glCreateProgram()
    if program is None:
        raise RuntimeError("Failed to create program")

    glAttachShader(program, vs)
    glAttachShader(program, fs)
    glLinkProgram(program)
    if glGetProgramiv(program, GL_LINK_STATUS) != GL_TRUE:
        raise RuntimeError(glGetProgramInfoLog(program).decode())

    glDeleteShader(vs)
    glDeleteShader(fs)
    return int(program)

class glShaderProgram:
    def __init__(self, vertex_src: str, fragment_src: str):
        self.vertex_src = vertex_src
        self.fragment_src =fragment_src 
        self.program = create_program(vertex_src, fragment_src);

    def setUniform3f(self, name: str, v3):
        id = glGetUniformLocation(self.program, name)
        if id != -1:
            glUniform3f(id, *v3)

    def setUniform1f(self, name: str, v):
        id = glGetUniformLocation(self.program, name)
        if id != -1:
            glUniform1f(id, v)

    def setUniformMat4(self, name: str, count: int, mats, transpose = GL_FALSE):
        id = glGetUniformLocation(self.program, name)
        if id != -1:
            glUniformMatrix4fv(id, count, transpose, mats)

    def setUniform1i(self, name: str, val: int):
        id = glGetUniformLocation(self.program, name)
        if id != -1:
            glUniform1i(id, val)

    def bind(self) -> None:
        glUseProgram(self.program)

    def unbind(self) -> None:
        glUseProgram(0)

    def delete(self) -> None:
        glDeleteProgram(self.program);

class glTexture:
    @staticmethod
    def loadTexture(path: str, style: int):
        image = Image.open(path)
        mode = image.mode  # "RGB" or "RGBA" or others
        if mode not in ["RGB", "RGBA"]:
            image = image.convert("RGBA")  # safest fallback

        # Flip image vertically
        img_data = np.array(image)[::-1]

        # Determine format
        format = GL_RGBA if image.mode == "RGBA" else GL_RGB        
        return glTexture(image.width, image.height, style, format, img_data)

    def __init__(self, width: int, height: int, style: int, format: int = GL_RGBA, data = None, type = GL_UNSIGNED_BYTE, mipmap: bool = True, wrapStyle=GL_CLAMP_TO_EDGE):
        self._id = glGenTextures(1)
        self.width = width
        self.height = height
        self.bind()
        glTexImage2D(GL_TEXTURE_2D, 0, format, width, height, 0, format, type, data)

        if mipmap:
            glGenerateMipmap(GL_TEXTURE_2D)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST_MIPMAP_NEAREST if (mipmap and style == GL_NEAREST) else style)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, style)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, wrapStyle)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, wrapStyle)

    def bind(self, slot: int = 0) -> None:
        glActiveTexture(int(GL_TEXTURE0) + slot)
        glBindTexture(GL_TEXTURE_2D, self._id)

    def unbind(self) -> None:
        glBindTexture(GL_TEXTURE_2D, 0)

    def delete(self) -> None:
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
    quad_vao: int
    quad_vbo: int

    @staticmethod
    def initailizeQuad():
        glFramebuffer.quad_vao = glGenVertexArrays(1)
        glFramebuffer.quad_vbo = glGenBuffers(1)
        glBindVertexArray(glFramebuffer.quad_vao)
        glBindBuffer(GL_ARRAY_BUFFER, glFramebuffer.quad_vbo)
        glBufferData(GL_ARRAY_BUFFER, glFramebuffer.quad_vertices.nbytes, glFramebuffer.quad_vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * glFramebuffer.quad_vertices.itemsize, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * glFramebuffer.quad_vertices.itemsize, ctypes.c_void_p(8))
        glEnableVertexAttribArray(1)

    @staticmethod
    def deleteQuad():
        glDeleteVertexArrays(1, [glFramebuffer.quad_vao])
        glDeleteBuffers(1, [glFramebuffer.quad_vbo])

    def __init__(self, shaderProgram: glShaderProgram, width: int, height: int):
        self.width = width
        self.height = height
        self.shader = shaderProgram

        self.fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glBindRenderbuffer(GL_RENDERBUFFER, 0);

    def genRenderBuffer(self, internalFormat):
        self.rbo = glGenRenderbuffers(1);
        glBindRenderbuffer(GL_RENDERBUFFER, self.rbo); 
        glRenderbufferStorage(GL_RENDERBUFFER, internalFormat, self.width, self.height);

    def attachRenderBuffer(self, attachment):
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, attachment, GL_RENDERBUFFER, self.rbo)

    def attachTexture(self, texture: glTexture, attachment = GL_COLOR_ATTACHMENT0) -> None:
        glFramebufferTexture2D(GL_FRAMEBUFFER, attachment, GL_TEXTURE_2D, texture._id, 0)

    def isCompleted(self) -> bool:
        return glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE

    def bind(self) -> None:
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self.fbo)

    def unbind(self) -> None:
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def delete(self) -> None:
        self.shader.delete()
        glDeleteFramebuffers(1, [self.fbo])
