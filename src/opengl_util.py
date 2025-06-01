from Window import Window
from OpenGL.GL import *
import numpy as np
from PIL import Image

class glVertexBuffer:
    def __init__(self, data, size: int, usage: int):
        self._id = glGenBuffers(1)
        self.usage = usage
        self.setBuffer(data, size)

    def bind(self) -> None:
        glBindBuffer(GL_ARRAY_BUFFER, self._id)

    def unbind(self) -> None:
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def setBuffer(self, data, size) -> None:
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

    def setBuffer(self, data, count) -> None:
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

    def __init__(self, width: int, height: int, style: int, format: int = GL_RGBA, data = None):
        self._id = glGenTextures(1)
        self.width = width
        self.height = height
        self.bind()
        glTexImage2D(GL_TEXTURE_2D, 0, format, width, height, 0, format, GL_UNSIGNED_BYTE, data)

        glGenerateMipmap(GL_TEXTURE_2D)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST_MIPMAP_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, style)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

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
        self.rbo = glGenRenderbuffers(1);
        glBindRenderbuffer(GL_RENDERBUFFER, self.rbo); 
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, screenBufferSize[0], screenBufferSize[1]);
        glBindRenderbuffer(GL_RENDERBUFFER, 0);

    def attachTexture(self, texture: glTexture) -> None:
        self.bind()
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, texture._id, 0)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, self.rbo)
        self.unbind()

    def isCompleted(self) -> bool:
        return glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE

    def bind(self) -> None:
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)

    def unbind(self) -> None:
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def delete(self) -> None:
        self.shader.delete()
        glDeleteVertexArrays(1, [self.quad_vao])
        glDeleteBuffers(1, [self.quad_vbo])
        glDeleteFramebuffers(1, [self.fbo])
