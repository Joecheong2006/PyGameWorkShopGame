from opengl_util import *
from pygltflib import GLTF2
import numpy as np
import glm

from PIL import Image
import io

class Material:
    def __init__(self):
        self.baseColor = [1, 1, 1]
        self.diffuseTexture: glTexture | None = None
        self.hasDiffuseTex: bool = False

class PrimitiveEntry:
    def __init__(self):
        self.indexCount: int = 0
        self.indexOffset: int = 0
        self.vertexOffset: int = 0
        self.materialIndex: int | None = None
        self.meshIndex: int = 0

def init_materials(gltf, layout):
    materials = []
    for entry in layout:
        m = Material()
        if entry.materialIndex == None:
            materials.append(m)
            continue
        print(gltf.materials[entry.materialIndex])
        texture = gltf.materials[entry.materialIndex].pbrMetallicRoughness.baseColorTexture
        color = gltf.materials[entry.materialIndex].pbrMetallicRoughness.baseColorFactor
        emissiveColor = gltf.materials[entry.materialIndex].emissiveFactor
        if color:
            m.baseColor = color[0:3]
        if texture:
            image_index = gltf.textures[texture.index].source
            image = gltf.images[image_index]
            view = gltf.bufferViews[image.bufferView]
            data = gltf.get_data_from_buffer_uri(gltf.buffers[view.buffer].uri)
            image_data = data[view.byteOffset : view.byteOffset + view.byteLength]
            img = Image.open(io.BytesIO(image_data)).convert("RGBA")
            pixels = img.tobytes()
            width, height = img.size
            m.diffuseTexture = glTexture(width, height, GL_NEAREST, data=pixels)
            m.hasDiffuseTex = True
        materials.append(m)
    return materials

def load_vertices(gltf):
    V = []
    I = []
    N = []
    UV = []
    BID = []
    W = []

    lastIndex = 0

    # Determine number of components
    M_num_components = {
        "SCALAR": 1,
        "VEC2": 2,
        "VEC3": 3,
        "VEC4": 4,
        "MAT2": 4,
        "MAT3": 9,
        "MAT4": 16,
    }

    M_dtype = {
        5120: np.int8,
        5121: np.uint8,
        5122: np.int16,
        5123: np.uint16,
        5125: np.uint32,
        5126: np.float32,
    }

    primitivesLayout: list[PrimitiveEntry] = []

    # Get the vertices for each primitive in the mesh (in this example there is only one)
    for i, mesh in enumerate(gltf.meshes):
        print(mesh.name)
        for primitive in mesh.primitives:
            entry = PrimitiveEntry()
            entry.meshIndex = i
            entry.materialIndex = primitive.material

            print(f"Primitive Material Index: {primitive.material}")
            # Get the binary data for this mesh primitive from the buffer
            accessor = gltf.accessors[primitive.attributes.NORMAL]
            bufferView = gltf.bufferViews[accessor.bufferView]
            buffer = gltf.buffers[bufferView.buffer]
            data = gltf.get_data_from_buffer_uri(buffer.uri)

            offset = (bufferView.byteOffset or 0) + (accessor.byteOffset or 0)
            N.extend(np.frombuffer(data, dtype=M_dtype[accessor.componentType], count=accessor.count * M_num_components[accessor.type], offset=offset))

            # Get the binary data for this mesh primitive from the buffer
            if primitive.attributes.TEXCOORD_0:
                accessor = gltf.accessors[primitive.attributes.TEXCOORD_0]
                bufferView = gltf.bufferViews[accessor.bufferView]
                buffer = gltf.buffers[bufferView.buffer]
                data = gltf.get_data_from_buffer_uri(buffer.uri)

                offset = (bufferView.byteOffset or 0) + (accessor.byteOffset or 0)
                UV.extend(np.frombuffer(data, dtype=M_dtype[accessor.componentType], count=accessor.count * M_num_components[accessor.type], offset=offset))

            # Get the binary data for this mesh primitive from the buffer
            accessor = gltf.accessors[primitive.attributes.POSITION]
            bufferView = gltf.bufferViews[accessor.bufferView]
            buffer = gltf.buffers[bufferView.buffer]
            data = gltf.get_data_from_buffer_uri(buffer.uri)

            entry.vertexOffset = int(len(V) / 3)

            offset = (bufferView.byteOffset or 0) + (accessor.byteOffset or 0)
            V.extend(np.frombuffer(data, dtype=M_dtype[accessor.componentType], count=accessor.count * M_num_components[accessor.type], offset=offset))

            accessor = gltf.accessors[primitive.indices]
            bufferView = gltf.bufferViews[accessor.bufferView]
            buffer = gltf.buffers[bufferView.buffer]
            data = gltf.get_data_from_buffer_uri(buffer.uri)

            # Get the binary data for this mesh primitive from the buffer
            offset = (bufferView.byteOffset or 0) + (accessor.byteOffset or 0)
            I.extend(np.frombuffer(data, dtype=M_dtype[accessor.componentType], count=accessor.count * M_num_components[accessor.type], offset=offset))

            entry.indexOffset = lastIndex
            entry.indexCount = len(I) - entry.indexOffset
            lastIndex = len(I)

            print(f'accessor.count = {accessor.count}')

            print(f'Entry: indexCount={entry.indexCount}, indexOffset={entry.indexOffset}, vertexOffset={entry.vertexOffset}, materailIndex={entry.materialIndex}')
            primitivesLayout.append(entry)

            if primitive.attributes.JOINTS_0:
                accessor = gltf.accessors[primitive.attributes.JOINTS_0]
                bufferView = gltf.bufferViews[accessor.bufferView]
                buffer = gltf.buffers[bufferView.buffer]
                data = gltf.get_data_from_buffer_uri(buffer.uri)

                offset = (bufferView.byteOffset or 0) + (accessor.byteOffset or 0)
                BID.extend(np.frombuffer(data, dtype=M_dtype[accessor.componentType], count=accessor.count * M_num_components[accessor.type], offset=offset))

            if primitive.attributes.WEIGHTS_0:
                accessor = gltf.accessors[primitive.attributes.WEIGHTS_0]
                bufferView = gltf.bufferViews[accessor.bufferView]
                buffer = gltf.buffers[bufferView.buffer]
                data = gltf.get_data_from_buffer_uri(buffer.uri)

                offset = (bufferView.byteOffset or 0) + (accessor.byteOffset or 0)
                W.extend(np.frombuffer(data, dtype=M_dtype[accessor.componentType], count=accessor.count * M_num_components[accessor.type], offset=offset))

    print(f"Materials Len: {len(gltf.materials)}")
    print(f'Vertices Count: {int(len(V) / 3)}')
    print(f'Indices Count: {len(I)}')

    # convert a numpy array for some manipulation
    return primitivesLayout, np.array(V, dtype=np.float32), np.array(I, dtype=np.uint32), np.array(N, dtype=np.float32), np.array(UV, dtype=np.float32), np.array(BID), np.array(W, dtype=np.float32)

class Mesh:
    def __init__(self):
        self.gltf = None
        self.modelMats = []

    def loadGLB(self, path: str):
        self.gltf = GLTF2().load(path)
        if self.gltf == None:
            raise RuntimeError(f"Failed to load {path}")

        self.layout, vertices, indices, normals, uvs, boneIDs, weights = load_vertices(self.gltf)

        self.modelMats = [glm.mat4(1)] * len(self.gltf.nodes)
        self.normalMats = [glm.mat4(1)] * len(self.gltf.nodes)

        for node in self.gltf.nodes:
            if node.mesh == None:
                continue
            print(node)
            print(node.mesh)
            T = glm.translate(glm.mat4(1.0), glm.vec3(node.translation)) if node.translation else glm.mat4(1.0)
            R = glm.mat4_cast(glm.quat(node.rotation[3], node.rotation[0], node.rotation[1], node.rotation[2])) if node.rotation else glm.mat4(1.0)
            S = glm.scale(glm.mat4(1.0), glm.vec3(node.scale)) if node.scale else glm.mat4(1.0)
            self.modelMats[node.mesh] = glm.mat4(T * R * S)
            self.normalMats[node.mesh] = R

        self.materials = init_materials(self.gltf, self.layout)

        self.vbos = glBuffers(6)

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        self.vbos.setVertexBuffer(1, vertices, vertices.nbytes, GL_STATIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))

        self.vbos.setVertexBuffer(2, normals, normals.nbytes, GL_STATIC_DRAW)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))

        if len(uvs) > 0:
            self.vbos.setVertexBuffer(3, uvs, uvs.nbytes, GL_STATIC_DRAW)
            glEnableVertexAttribArray(2)
            glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))

        if len(boneIDs) > 0:
            self.vbos.setVertexBuffer(4, boneIDs, boneIDs.nbytes, GL_STATIC_DRAW)
            glEnableVertexAttribArray(3)
            glVertexAttribIPointer(3, 4, GL_UNSIGNED_BYTE, 0, ctypes.c_void_p(0))

        if len(weights) > 0:
            self.vbos.setVertexBuffer(5, weights, weights.nbytes, GL_STATIC_DRAW)
            glEnableVertexAttribArray(4)
            glVertexAttribPointer(4, 4, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))

        self.vbos.setIndexBuffer(0, indices, indices.size, GL_STATIC_DRAW)

        glBindVertexArray(0)

    def delete(self):
        self.vbos.delete()
        glDeleteVertexArrays(1, [self.vao])

    def render(self, shader):
        if self.gltf == None:
            return

        glBindVertexArray(self.vao)
        for i, entry in enumerate(self.layout):
            glUniform3f(glGetUniformLocation(shader.program, "color"), *self.materials[i].baseColor)
            model = self.modelMats[entry.meshIndex]
            glUniformMatrix4fv(glGetUniformLocation(shader.program, "model"), 1, GL_FALSE, model.to_list())
            mn = self.normalMats[entry.meshIndex]
            glUniformMatrix4fv(glGetUniformLocation(shader.program, "mn"), 1, GL_FALSE, mn.to_list())

            glUniform1i(glGetUniformLocation(shader.program, "hasDiffuseTex"), self.materials[i].hasDiffuseTex)
            if self.materials[i].hasDiffuseTex:
                self.materials[i].diffuseTexture.bind(0)
                glUniform1i(glGetUniformLocation(shader.program, "diffuseTexture"), 0)

            glDrawElementsBaseVertex(GL_TRIANGLES, entry.indexCount, GL_UNSIGNED_INT, ctypes.c_void_p(4 * entry.indexOffset), entry.vertexOffset)
