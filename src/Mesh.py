from opengl_util import *
from pygltflib import GLTF2
import numpy as np

def load_vertices(gltf, mesh):
    V = []
    I = []
    N = []
    UV = []

    indexOffset = 0
    lastIndex = 0

    # Determine number of components
    M_num_components = {
        "SCALAR": 1,
        "VEC2": 2,
        "VEC3": 3,
        "VEC4": 4,
        "MAT4": 16
    }

    M_dtype = {
        5126: np.float32,
        5123: np.uint16,
        5125: np.uint32,
    }

    print(f'Primitives Count: {len(mesh.primitives)}')

    # Get the vertices for each primitive in the mesh (in this example there is only one)
    for primitive in mesh.primitives:
        # Get the binary data for this mesh primitive from the buffer
        accessor = gltf.accessors[primitive.attributes.NORMAL]
        bufferView = gltf.bufferViews[accessor.bufferView]
        buffer = gltf.buffers[bufferView.buffer]
        data = gltf.get_data_from_buffer_uri(buffer.uri)

        offset = accessor.byteOffset + bufferView.byteOffset
        N.extend(np.frombuffer(data, dtype=M_dtype[accessor.componentType], count=accessor.count * M_num_components[accessor.type], offset=offset))

        # Get the binary data for this mesh primitive from the buffer
        accessor = gltf.accessors[primitive.attributes.TEXCOORD_0]
        bufferView = gltf.bufferViews[accessor.bufferView]
        buffer = gltf.buffers[bufferView.buffer]
        data = gltf.get_data_from_buffer_uri(buffer.uri)

        offset = accessor.byteOffset + bufferView.byteOffset
        UV.extend(np.frombuffer(data, dtype=M_dtype[accessor.componentType], count=accessor.count * M_num_components[accessor.type], offset=offset))

        # Get the binary data for this mesh primitive from the buffer
        accessor = gltf.accessors[primitive.attributes.POSITION]
        bufferView = gltf.bufferViews[accessor.bufferView]
        buffer = gltf.buffers[bufferView.buffer]
        data = gltf.get_data_from_buffer_uri(buffer.uri)

        offset = accessor.byteOffset + bufferView.byteOffset
        V.extend(np.frombuffer(data, dtype=M_dtype[accessor.componentType], count=accessor.count * M_num_components[accessor.type], offset=offset))
        print(f'Index Offset = {indexOffset}')

        accessor = gltf.accessors[primitive.indices]
        bufferView = gltf.bufferViews[accessor.bufferView]
        buffer = gltf.buffers[bufferView.buffer]
        data = gltf.get_data_from_buffer_uri(buffer.uri)

        # Get the binary data for this mesh primitive from the buffer
        offset = accessor.byteOffset + bufferView.byteOffset
        I.extend(np.frombuffer(data, dtype=M_dtype[accessor.componentType], count=accessor.count * M_num_components[accessor.type], offset=offset))
        for i in range(accessor.count):
            I[i + lastIndex] += indexOffset
        indexOffset = int(len(V) / 3)
        lastIndex = len(I)

        print(f'accessor.count = {accessor.count}')

    print(f'Vertices Count: {int(len(V) / 3)}')
    print(f'Indices Count: {len(I)}')

    # convert a numpy array for some manipulation
    return np.array(V, dtype=np.float32), np.array(I, dtype=np.uint32), np.array(N, dtype=np.float32), np.array(UV, dtype=np.float32)

class Mesh:
    def __init__(self):
        pass

    def loadGLB(self, path: str):
        self.gltf = GLTF2().load(path)

        mesh = self.gltf.meshes[0]
        vertices, indices, normals, uvs = load_vertices(self.gltf, mesh)

        vertex_count = len(vertices) // 3

        # Reshape individual arrays to Nx3 or Nx2
        V_reshaped = vertices.reshape(vertex_count, 3)
        N_reshaped = normals.reshape(vertex_count, 3)
        UV_reshaped = uvs.reshape(vertex_count, 2)

        interleaved = np.hstack((V_reshaped, N_reshaped, UV_reshaped)).astype(np.float32)

        print(mesh.primitives[0].attributes)

        stride = 8 * 4
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        self.vbo = glVertexBuffer(interleaved, interleaved.nbytes, GL_STATIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(24))

        self.ibo = glIndexBuffer(indices, indices.size);

        glBindVertexArray(0)
        self.vbo.unbind()
        self.ibo.unbind()
