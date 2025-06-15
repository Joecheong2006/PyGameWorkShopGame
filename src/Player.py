import pygame as pg
from AnimationSystem import AnimationSystem
from Window import Window
from GameObject import GameObject
from Model import Model
from Animator import Animator
from pyglm import glm
from Camera import Camera

class Player(GameObject):
    def __init__(self):
        super().__init__(self)

        self.model = Model("res/M.glb")

        self.forward: glm.vec3 = glm.vec3(0, 0, 1)
        self.right: glm.vec3 = glm.vec3(1, 0, 0)
        self.up: glm.vec3 = glm.vec3(0, 1, 0)
        self.transform = self.model.transform
        self.model.transform.rotation = glm.angleAxis(glm.pi(), glm.vec3(0, 1, 0))
        self.facingDir = glm.vec3(0)
        self.v = glm.vec3(0)

        self.animator = Animator(self.model)
        self.animator.setDefaultState("Idle")
        self.animator.addAnimationState("FastRunning")
        self.animator.addAnimationState("Sitting")

        self.animator.variables["sitTransition"] = False

        def IdleToRun(animator: Animator):
            return glm.length(self.v) > 0.1

        def RunToIdle(animator: Animator):
            return glm.length(self.v) <= 0.1

        self.sitting = False
        def StartSitting(animator: Animator):
            self.animator.variables["sitTransition"] = self.sitting
            return self.sitting

        def EndSitting(animator: Animator):
            self.animator.variables["sitTransition"] = self.sitting
            return not self.sitting

        self.animator.addTransition("Idle", "FastRunning", 0.2, IdleToRun)
        self.animator.addTransition("FastRunning", "Idle", 0.1, RunToIdle)
        self.animator.addTransition("Idle", "Sitting", 0.3, StartSitting)
        self.animator.addTransition("Sitting", "Idle", 0.3, EndSitting)

    def followCameraDirection(self, cam: Camera):
        self.forward = -glm.normalize(glm.vec3(cam.forward()) * glm.vec3(1, 0, 1))
        self.right = glm.normalize(glm.vec3(cam.right()) * glm.vec3(1, 0, 1))

    def OnUpdate(self, window: Window):
        deltaTime = window.deltaTime
        keys = window.keys

        self.sitting = keys[pg.K_SPACE]
        if self.animator.variables["sitTransition"]:
            return

        horizentalAxis = keys[pg.K_d] - keys[pg.K_a]
        horizentalDir = horizentalAxis * self.right

        verticalAxis = keys[pg.K_s] - keys[pg.K_w]
        verticalDir = verticalAxis * self.forward

        newMovementDir = horizentalDir + verticalDir

        if newMovementDir == glm.vec3(0):
            self.v = glm.lerp(self.v, glm.vec3(0), 40 * deltaTime)
        else:
            self.facingDir = glm.normalize(newMovementDir)
            self.v = glm.lerp(self.v, self.facingDir * 10, 15 * deltaTime)

        toRotation = glm.angleAxis(glm.atan(self.facingDir[0], self.facingDir[2]), glm.vec3(0, 1, 0))
        self.transform.rotation = glm.slerp(self.transform.rotation, toRotation, 12 * deltaTime)
        self.transform.position = glm.vec3(glm.lerp(self.transform.position, self.v * deltaTime + self.transform.position, 50 * deltaTime))
