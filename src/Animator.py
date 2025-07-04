from Model import Model, Animation
from pyglm import glm
import numpy as np

class AnimationState:
    def __init__(self, anim: Animation, animName: str, timeScale: float, loop: bool):
        self.animName: str = animName
        self.anim: Animation = anim
        self.duration: float = self.anim.duration[0] if self.anim else 0
        self.time: float = 0
        self.timeScale: float = timeScale
        self.loop: bool = loop
        self.finished: bool = False
        self.frameIndexes: list[int] = [0] * len(self.anim.channels)

    def calculateAnimation(self, target: Model):
        if self.anim == None:
            return

        attr_map = {
            'translation': 'translation',
            'rotation': 'rotation',
            'scale': 'scale',
        }

        for i, channel in enumerate(self.anim.channels):
            sampler = self.anim.samplers[channel.sampler]
            keyframe_times = sampler.keyframe_times
            keyframe_values = sampler.keyframe_values

            interpolated_value, self.frameIndexes[i] = interp_anim_vec(
                    channel.path, self.time, sampler.interpolation, 
                    keyframe_times, keyframe_values, self.frameIndexes[i]
                )

            setattr(target.nodes[channel.node], attr_map[channel.path], interpolated_value)

    def update(self, deltaTime: float):
        self.time += deltaTime * self.timeScale
        if self.time > self.duration:
            if self.loop:
                self.time = np.fmod(self.time, self.duration)
                self.frameIndexes = [0] * len(self.anim.channels)
            else:
                self.time = self.duration
                self.finished = True

    def reset(self):
        self.time = 0
        self.frameIndexes = [0] * len(self.anim.channels)
        self.finished = False

class Animator:
    def __init__(self, model: Model):
        from AnimationSystem import AnimationSystem
        AnimationSystem.AddAnimator(self)
        model.animating = True
        self.target: Model = model

        self.currentState: AnimationState | None = None
        self.animationStates: dict[str, AnimationState] = {}
        self.transitions: list[AnimationTransition] = []

        self.isTransitioning: bool = False
        self.transitionIndex: int = -1

        self.variables = {}

    def addTransition(self, startAnimName: str, endAnimName: str, duration: float, event = lambda : False, offset: float = 0):
        if startAnimName not in self.target.animNameIndexMap or endAnimName not in self.target.animNameIndexMap:
            return
        self.transitions.append(AnimationTransition(startAnimName, endAnimName, duration, event, offset))

    def addAnimationState(self, animName: str, timeScale: float = 1, loop: bool = True):
        if animName not in self.target.animNameIndexMap:
            return
        animIndex = self.target.animNameIndexMap[animName]
        self.animationStates[animName] = AnimationState(self.target.animations[animIndex], animName, timeScale, loop)

    def setDefaultState(self, animName: str, timeScale: float = 1, loop: bool = True):
        if animName not in self.target.animNameIndexMap:
            return
        animIndex = self.target.animNameIndexMap[animName]
        self.currentState = self.animationStates[animName] = AnimationState(self.target.animations[animIndex], animName, timeScale, loop)
    
    def playAnimation(self, deltaTime: float):
        if self.currentState == None:
            return

        self.currentState.calculateAnimation(self.target)

        self.currentState.update(deltaTime)

        if not self.isTransitioning:
            for i, transition in enumerate(self.transitions):
                if self.currentState.animName == transition.startAnimName and transition.event(self):
                    self.isTransitioning = True
                    self.transitionIndex = i
                    self.animationStates[transition.endAnimName].reset()
        else:
            transition = self.transitions[self.transitionIndex]
            if not transition.apply(deltaTime, self):
                self.currentState.reset()
                self.isTransitioning = False
                self.transitionIndex = -1
                self.currentState = self.animationStates[transition.endAnimName]
                transition.reset()

        nodes = self.target.nodes
        ordered_indexes = self.target.ordered_node_indexes

        for node in nodes:
            node.transform = calc_local_transform(node)
        for node_index in ordered_indexes:
            node = nodes[node_index]
            parent_index = node.parent_index
            if parent_index >= 0:
                parent_node = nodes[parent_index]
                node.transform = parent_node.transform @ node.transform

        self.target.jointMatrices = calc_joint_matrices(self.target)

def calc_joint_matrices(model: Model):
    if model.skins == None:
        return []
    # assert len(model.skins) == 1
    for skin in model.skins:
        return [
                model.nodes[joint_index].transform @ inverse_bind_matrix
                for joint_index, inverse_bind_matrix in zip(skin.joints, skin.inverse_bind_matrices)
            ]
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
    return np.array(translation @ rotation @ scale)

def interp_anim_vec(path: str, t: float, interpolation: str, keyframe_times, keyframe_values, frameIndex):
    aIndex, b, t = get_lerp(t, keyframe_times, frameIndex)
    a = glm.quat(keyframe_values[aIndex, [3,0,1,2]]) if path[0] == 'r' else glm.vec3(keyframe_values[aIndex])
    b = glm.quat(keyframe_values[b, [3,0,1,2]]) if path[0] == 'r' else glm.vec3(keyframe_values[b])
    if interpolation[0] == 'S':
        return a, aIndex
    elif interpolation[0] == 'L':
        if path[0] == 'r':
            return glm.slerp(a, b, t), aIndex
        return glm.lerp(a, b, t), aIndex
    assert False, 'bad interpolation'

def get_lerp(t: float, keyframe_times, frameIndex):
    a = np.insert(np.array(keyframe_times, dtype=np.float32), 0, 0)
    for i in range(frameIndex, len(a) - 1):
        t0, t1, = a[i], a[i + 1]
        if t0 <= t < t1:
            j = (i + 1) % len(keyframe_times)
            t = (t - t0) / (t1 - t0)
            return i, j, t
    return 0, 0, 0

class AnimationTransition:
    def __init__(self, startAnimName: str, endAnimName: str, duration: float, event, offset: float):
        self.startAnimName: str = startAnimName
        self.endAnimName: str = endAnimName
        self.duration: float = duration
        self.durationInverse: float = 1.0 / duration
        self.offset: float = glm.clamp(offset, 0, 1)
        self.event = event
        self.currentDuration: float = 0

    def apply(self, deltaTime: float, animator: Animator) -> bool:
        states = animator.animationStates
        endAnimState = states[self.endAnimName]
        endAnim = endAnimState.anim

        for i, channel in enumerate(endAnim.channels):
            sampler = endAnim.samplers[channel.sampler]
            keyframe_times = sampler.keyframe_times
            keyframe_values = sampler.keyframe_values

            interpolated_value, endAnimState.frameIndexes[i] = interp_anim_vec(
                    channel.path, endAnimState.time, sampler.interpolation, 
                    keyframe_times, keyframe_values, endAnimState.frameIndexes[i]
                )

            if channel.path == 'translation':
                animator.target.nodes[channel.node].translation = glm.lerp(animator.target.nodes[channel.node].translation, interpolated_value, self.currentDuration)
            elif channel.path == 'rotation':
                animator.target.nodes[channel.node].rotation = glm.slerp(glm.quat(animator.target.nodes[channel.node].rotation), interpolated_value, self.currentDuration)
            elif channel.path == 'scale':
                animator.target.nodes[channel.node].scale = interpolated_value

        self.currentDuration += deltaTime * self.durationInverse
        endAnimState.time += deltaTime * endAnimState.timeScale
        return self.currentDuration <= 1

    def reset(self):
        self.currentDuration = 0
