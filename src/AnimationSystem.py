from Animator import *

class AnimationSystem:
    animations: list[Animator]
    def __init__(self):
        raise RuntimeError("AnimationSystem cannot be created!")

    @staticmethod
    def SetUp():
        AnimationSystem.animations = []

    @staticmethod
    def ShutDown():
        AnimationSystem.animations = []

    @staticmethod
    def AddAnimation(animator: Animator):
        AnimationSystem.animations.append(animator)

    @staticmethod
    def Update(deltaTime: float):
        for anim in AnimationSystem.animations:
            anim.playAnimation(deltaTime)

