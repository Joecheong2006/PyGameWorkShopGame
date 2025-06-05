from Model import Model
from pyglm import glm
import numpy as np

class Animator:
    def __init__(self, model: Model):
        self.animation = None
        self.target: Model = model
        self.time = 0
        self.duration = 0

    def startAnimation(self, animIndex: int):
        if len(self.target.animations) == 0:
            return 
        self.animation = self.target.animations[animIndex]
        self.time = 0 % self.animation.duration
        self.target.animating = True
    
    def playAnimation(self, deltaTime: float):
        if self.animation == None:
            return

        for channel in self.animation.channels:
            sampler = self.animation.samplers[channel.sampler]
            keyframe_times = sampler.keyframe_times
            keyframe_values = sampler.keyframe_values

            interpolated_value = interp_anim_vec(channel.path, self.time, sampler.interpolation, keyframe_times, keyframe_values)

            if channel.path == 'translation':
                self.target.nodes[channel.node].translation = interpolated_value
            elif channel.path == 'rotation':
                self.target.nodes[channel.node].rotation = interpolated_value
            elif channel.path == 'scale':
                self.target.nodes[channel.node].scale = interpolated_value

        self.time += deltaTime * 1.0
        if self.time >= self.animation.duration:
            self.time %= self.animation.duration

        for node in self.target.nodes:
            node.transform = calc_local_transform(node)
        for node_index in self.target.ordered_node_indexes:
            node = self.target.nodes[node_index]
            parent_index = node.parent_index
            if parent_index >= 0:
                parent_node = self.target.nodes[parent_index]
                node.transform = parent_node.transform @ node.transform

        self.target.jointMatrices = calc_joint_matrices(self.target)

def calc_joint_matrices(model):
    # assert len(model.skins) == 1
    for skin in model.skins:
        joint_matrices = []
        for joint_index, inverse_bind_matrix in zip(skin.joints, skin.inverse_bind_matrices):
            node = model.nodes[joint_index]
            joint_matrix = node.transform @ inverse_bind_matrix.reshape((4,4)).T
            joint_matrices.append(joint_matrix)
        return joint_matrices
    return []

def calc_local_transform(node):
    translation = glm.mat4()
    rotation = glm.mat4()
    scale = glm.mat4()
    if hasattr(node, 'translation') and node.translation is not None:
        translation = glm.translate(translation, node.translation)
    if hasattr(node, 'rotation') and node.rotation is not None:
        rotation = glm.mat4_cast(node.rotation)
    if hasattr(node, 'scale') and node.scale is not None:
        scale = glm.scale(scale, glm.vec3(node.scale))
    transform = translation @ rotation @ scale
    return np.array(transform)

def interp_anim_vec(path, t, interpolation, keyframe_times, keyframe_values):
    a,b,t = get_lerp(t, keyframe_times)
    a = glm.quat(keyframe_values[a, [3,0,1,2]]) if path == 'rotation' else glm.vec3(keyframe_values[a])
    b = glm.quat(keyframe_values[b, [3,0,1,2]]) if path == 'rotation' else glm.vec3(keyframe_values[b])
    if interpolation == 'STEP':
        return a
    elif interpolation == 'LINEAR':
        if path == 'rotation':
            return glm.slerp(a, b, t)
        return glm.lerp(a, b, t)
    assert False, 'bad interpolation'


def get_lerp(t, keyframe_times):
    for i, (t0, t1) in enumerate(zip(np.append([0.0], keyframe_times[:-1]), keyframe_times)):
        if t0 <= t < t1:
            j = (i+1) % len(keyframe_times)
            t = (t - t0) / (t1 - t0)
            return i, j, t
    return 0, 0, 0
