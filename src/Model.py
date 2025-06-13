from opengl_util import *
import pygltflib
import numpy as np
from pyglm import glm

from PIL import Image
import io

from collections import namedtuple
MeshData = namedtuple('MeshesData', 'primitivesLayout indices vertices normals uvs boneIDs weights')
AnimationSampler = namedtuple('AnimationSampler', 'interpolation keyframe_times keyframe_values')
AnimationChannel = namedtuple('AnimationChannel', 'sampler node path')
Animation = namedtuple('Animation', 'name samplers channels duration')
Skin = namedtuple('Skin', 'joints inverse_bind_matrices')

class Transform:
    def __init__(self):
        self.position = glm.vec3(0)
        self.scale = glm.vec3(1.0)
        self.rotation = glm.quat(0, 0, 0, 0)

    def getMatrix(self):
        return glm.translate(glm.mat4(1.0), glm.vec3(self.position)) * glm.mat4_cast(self.rotation) * glm.scale(glm.mat4(1.0), self.scale)

model_vert_shader = """
    #version 330 core
    layout (location = 0) in vec3 aPos;
    layout (location = 1) in vec3 aNormal;
    layout (location = 2) in vec2 aUV;
    layout (location = 3) in uvec4 aJointIDs;
    layout (location = 4) in vec4 aWeights;

    uniform mat4 vp;
    uniform mat4 lvp;
    uniform mat4 model;
    uniform mat4 inverseModel;

    uniform mat4 jointMatrices[100];

    uniform bool hasAnimation;

    out vec3 fragPos;
    out vec4 lightFragPos;
    out vec3 normal;
    out vec2 uv;

    void main() {
        mat4 skinMatrix = mat4(1);
        if (hasAnimation) {
            skinMatrix =
            aWeights.x * jointMatrices[aJointIDs.x] +
            aWeights.y * jointMatrices[aJointIDs.y] +
            aWeights.z * jointMatrices[aJointIDs.z] +
            aWeights.w * jointMatrices[aJointIDs.w];
        }

        mat4 fullTransform = model * skinMatrix;
        gl_Position = vp * fullTransform * vec4(aPos, 1.0);
        fragPos = vec3(model * vec4(aPos, 1.0));
        normal = normalize(mat3(inverseModel) * mat3(skinMatrix) * aNormal);
        uv = aUV;

        lightFragPos = lvp * fullTransform * vec4(aPos, 1.0);
    }
    """

model_frag_shader = """
    #version 330 core

    out vec4 FragColor;

    uniform vec3 color;
    uniform sampler2D diffuseTexture;
    uniform sampler2D shadowMap;
    uniform bool hasDiffuseTex;
    uniform vec3 lightDir;

    in vec3 fragPos;
    in vec4 lightFragPos;
    in vec3 normal;
    in vec2 uv;

    #define TOON_LEVEL 8.0

    float getShadowFactor(in vec3 lightUV, in vec3 N) {
        if (lightUV.z > 1.0)
            return 0.0;
        float bias = 0.001;
        bias = max(0.001 * (1.0 - dot(N, -lightDir)), bias);
        float depth = texture(shadowMap, lightUV.xy).r;
        return lightUV.z > depth + bias ? 0.5 : 1.0;
    }

    void main() {
        if (hasDiffuseTex && texture(diffuseTexture, uv).a < 0.1) {
            discard;
        }

        vec3 lightProjPos = lightFragPos.xyz / lightFragPos.w;
        vec3 lightUV = lightProjPos * 0.5 + 0.5;

        vec3 N = normal;

        float shadowFactor = getShadowFactor(lightUV, N);

        float factor = dot(N, -normalize(lightDir));

        // factor = factor > 0 ? ceil(factor * TOON_LEVEL) / TOON_LEVEL : 0;
        factor = factor > 0 ? factor : 0;

        vec4 finalColor = vec4(1.0);
        if (!hasDiffuseTex) {
            finalColor = vec4(color, 1);
        }
        else {
            finalColor = texture(diffuseTexture, uv);
        }

        // finalColor.rgb *= (N + 1.0) * 0.5;
        finalColor.rgb = ceil(finalColor.rgb * TOON_LEVEL) / TOON_LEVEL;
        FragColor = vec4(finalColor.rgb * shadowFactor, finalColor.a);
    }
    """

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
    pygltflib.BYTE: np.int8,
    pygltflib.UNSIGNED_BYTE: np.uint8,
    pygltflib.SHORT: np.int16,
    pygltflib.UNSIGNED_SHORT: np.uint16,
    pygltflib.UNSIGNED_INT: np.uint32,
    pygltflib.FLOAT: np.float32,
}

def load_accessor_buffer(gltf, accessorIndex):
    accessor = gltf.accessors[accessorIndex]
    bufferView = gltf.bufferViews[accessor.bufferView]
    buffer = gltf.buffers[bufferView.buffer]
    data = gltf.get_data_from_buffer_uri(buffer.uri)

    offset = (bufferView.byteOffset or 0) + (accessor.byteOffset or 0)
    count = M_num_components[accessor.type]
    buffer = np.frombuffer(data, dtype=M_dtype[accessor.componentType], count=accessor.count * count, offset=offset)
    return np.reshape(buffer, (-1, count))

def load_mesh_data(gltf) -> MeshData:
    I = np.array([], dtype=np.uint32)
    V = np.array([], dtype=np.float32)
    N = np.array([], dtype=np.float32)
    UV = np.array([], dtype=np.float32)
    BID = np.array([], dtype=np.uint8)
    W = np.array([], dtype=np.float32)

    lastIndex = 0

    primitivesLayout: list[PrimitiveEntry] = []

    for i, mesh in enumerate(gltf.meshes):
        for primitive in mesh.primitives:
            entry = PrimitiveEntry()
            entry.meshIndex = i
            entry.materialIndex = primitive.material
            entry.vertexOffset = int(len(V) / 3)

            I = np.append(I, load_accessor_buffer(gltf, primitive.indices))
            N = np.append(V, load_accessor_buffer(gltf, primitive.attributes.NORMAL))
            V = np.append(V, load_accessor_buffer(gltf, primitive.attributes.POSITION))
            if primitive.attributes.TEXCOORD_0:
                UV = np.append(UV, load_accessor_buffer(gltf, primitive.attributes.TEXCOORD_0))
            if primitive.attributes.JOINTS_0:
                BID = np.append(BID, load_accessor_buffer(gltf, primitive.attributes.JOINTS_0))
            if primitive.attributes.WEIGHTS_0:
                W = np.append(W, load_accessor_buffer(gltf, primitive.attributes.WEIGHTS_0))

            assert len(N) == len(V)
            assert N.dtype == np.float32
            assert V.dtype == np.float32
            if len(UV) > 0:
                assert UV.dtype == np.float32

            entry.indexOffset = lastIndex
            entry.indexCount = len(I) - entry.indexOffset
            lastIndex = len(I)

            primitivesLayout.append(entry)

    return MeshData(primitivesLayout, I, V, N, UV, BID, W)

def load_animations(gltf):
    if len(gltf.animations) == 0:
        return {}, [], None, None

    animNameIndexMap: dict[str, int] = {}

    animations = []
    for i, anim in enumerate(gltf.animations):
        samplers = []
        channels = []
        duration = 0
        for sampler in anim.samplers:
            keyframe_times = load_accessor_buffer(gltf, sampler.input)
            keyframe_values = load_accessor_buffer(gltf,sampler.output)
            samplers.append(AnimationSampler(sampler.interpolation, keyframe_times, keyframe_values))
            if keyframe_times[-1] > duration:
                duration = keyframe_times[-1]
        for chnl in anim.channels:
            channels.append(AnimationChannel(chnl.sampler, chnl.target.node, chnl.target.path))
        
        animNameIndexMap[anim.name] = i
        a = Animation(anim.name, samplers, channels, duration)
        animations.append(a)

    skins = []
    for skin in gltf.skins:
        joints = skin.joints
        inverse_bind_matrices = load_accessor_buffer(gltf, skin.inverseBindMatrices)
        inverse_bind_matrices = inverse_bind_matrices.reshape((-1, 16))
        assert inverse_bind_matrices.dtype == np.float32
        skins.append(Skin(joints, inverse_bind_matrices))

    def order_nodes_root_first(nodes):
        for node in nodes:
            node.parent_index = -1
        for i, node in enumerate(nodes):
            for child_node_index in node.children:
                nodes[child_node_index].parent_index = i
        ordered_parent_indexes = {}
        for i in range(len(nodes)):
            def add_node(j):
                if j in ordered_parent_indexes:
                    return
                parent_index = nodes[j].parent_index
                if parent_index >= 0:
                    add_node(parent_index)
                ordered_parent_indexes[j] = 1
            add_node(i)
        return list(ordered_parent_indexes)

    ordered_node_indexes = order_nodes_root_first(gltf.nodes)
    root = gltf.nodes[ordered_node_indexes[0]]
    if root.mesh is None and root.rotation is not None:
        root.rotation = [root.rotation[3], root.rotation[0], root.rotation[1], root.rotation[2]]
    return animNameIndexMap, animations, skins, ordered_node_indexes

class Model:
    shader: glShaderProgram
    @staticmethod
    def CompileShader():
        Model.shader = glShaderProgram(model_vert_shader, model_frag_shader)

    def __init__(self, path: str):
        from GameObjectSystem import GameObjectSystem
        GameObjectSystem.AddModelObject(self)
        self.transform = Transform()

        gltf = pygltflib.GLTF2().load(path)
        if gltf == None:
            raise RuntimeError(f"Failed to load {path}")

        meshData = load_mesh_data(gltf)
        self.layout = meshData.primitivesLayout
        self.animNameIndexMap, self.animations, self.skins, self.ordered_node_indexes = load_animations(gltf)
        self.nodes = gltf.nodes

        self.modelMats = {}

        for node in self.nodes:
            if node.mesh is None:
                continue
            T = glm.mat4()
            R = glm.mat4()
            S = glm.mat4()
            if node.translation is not None:
                T = glm.translate(glm.mat4(1.0), glm.vec3(node.translation))
            if node.rotation is not None:
                R = glm.mat4_cast(glm.quat(node.rotation))
                R = glm.mat4_cast(glm.quat(node.rotation[3], node.rotation[0], node.rotation[1], node.rotation[2]))
            if node.scale is not None:
                S = glm.scale(glm.mat4(1.0), glm.vec3(node.scale))
            self.modelMats[node.mesh] = glm.mat4(T * R * S)

        self.materials = init_materials(gltf, self.layout)

        self.vbos = glBuffers(6)

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        self.vbos.setVertexBuffer(1, meshData.vertices, meshData.vertices.nbytes, GL_STATIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))

        self.vbos.setVertexBuffer(2, meshData.normals, meshData.normals.nbytes, GL_STATIC_DRAW)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))

        if len(meshData.uvs) > 0:
            self.vbos.setVertexBuffer(3, meshData.uvs, meshData.uvs.nbytes, GL_STATIC_DRAW)
            glEnableVertexAttribArray(2)
            glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))

        if len(meshData.boneIDs) > 0:
            self.vbos.setVertexBuffer(4, meshData.boneIDs, meshData.boneIDs.nbytes, GL_STATIC_DRAW)
            glEnableVertexAttribArray(3)
            glVertexAttribIPointer(3, 4, GL_UNSIGNED_BYTE, 0, ctypes.c_void_p(0))

        if len(meshData.weights) > 0:
            self.vbos.setVertexBuffer(5, meshData.weights, meshData.weights.nbytes, GL_STATIC_DRAW)
            glEnableVertexAttribArray(4)
            glVertexAttribPointer(4, 4, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))

        self.vbos.setIndexBuffer(0, meshData.indices, meshData.indices.size, GL_STATIC_DRAW)

        self.jointMatrices = []
        self.animating = False
        glBindVertexArray(0)

    def delete(self):
        self.vbos.delete()
        glDeleteVertexArrays(1, [self.vao])

    from Camera import Camera
    def render(self, shader: glShaderProgram, camera: Camera):
        m = camera.projectionMat * camera.getViewMatrix()
        shader.setUniformMat4("vp", 1, m.to_list())
        if self.animating:
            shader.setUniform1i("hasAnimation", 1)
            shader.setUniformMat4("jointMatrices", len(self.jointMatrices), np.array(self.jointMatrices), GL_TRUE)
        else:
            shader.setUniform1i("hasAnimation", 0)

        transformMatrix = self.transform.getMatrix()

        glBindVertexArray(self.vao)
        for i, entry in enumerate(self.layout):
            shader.setUniform3f("color", self.materials[i].baseColor)
            model = self.modelMats[entry.meshIndex] * transformMatrix
            shader.setUniformMat4("model", 1, model.to_list())
            inverseModel = glm.transpose(glm.inverse(model))
            shader.setUniformMat4("inverseModel", 1, inverseModel.to_list())

            shader.setUniform1i("hasDiffuseTex", self.materials[i].hasDiffuseTex)
            if self.materials[i].hasDiffuseTex:
                self.materials[i].diffuseTexture.bind(0)
                shader.setUniform1i("diffuseTexture", 0)

            glDrawElementsBaseVertex(GL_TRIANGLES, entry.indexCount, GL_UNSIGNED_INT, ctypes.c_void_p(4 * entry.indexOffset), entry.vertexOffset)
