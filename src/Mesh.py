from opengl_util import *
from pygltflib import GLTF2
import numpy as np

def load_vertices(gltf):
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

    # Get the vertices for each primitive in the mesh (in this example there is only one)
    primitivesCount = 0
    for mesh in gltf.meshes:
        primitivesCount += len(mesh.primitives)
        for primitive in mesh.primitives:
            print(f"Primitive Material Index: {primitive.material}")
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

    print(f"Materials Len: {len(gltf.materials)}")
    print(f'Primitives Count: {primitivesCount}')
    print(f'Vertices Count: {int(len(V) / 3)}')
    print(f'Indices Count: {len(I)}')

    # convert a numpy array for some manipulation
    return np.array(V, dtype=np.float32), np.array(I, dtype=np.uint32), np.array(N, dtype=np.float32), np.array(UV, dtype=np.float32)

class Mesh:
    def __init__(self):
        pass

    def loadGLB(self, path: str):
        self.gltf = GLTF2().load(path)
        if self.gltf == None:
            raise RuntimeError(f"Failed to load {path}")

        vertices, indices, normals, uvs = load_vertices(self.gltf)

        self.vbos = glBuffers(4)

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        self.vbos.setVertexBuffer(1, vertices, vertices.nbytes, GL_STATIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))

        self.vbos.setVertexBuffer(2, normals, normals.nbytes, GL_STATIC_DRAW)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))

        self.vbos.setVertexBuffer(3, uvs, uvs.nbytes, GL_STATIC_DRAW)
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))

        self.vbos.setIndexBuffer(0, indices, indices.size, GL_STATIC_DRAW)

        glBindVertexArray(0)

    def delete(self):
        self.vbos.delete()
        glDeleteVertexArrays(1, [self.vao])
