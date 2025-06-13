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
        # self.model = Model("res/Kick.glb")
        # self.model = Model("res/Capoeira.glb")
        # self.model = Model("res/AlienSoldier.glb")
        # self.model = Model("res/TestScene2.glb")
        # self.model = Model("res/Ronin.glb")
        # self.model = Model("res/Monkey.glb")

        self.animator = Animator(self.model)
        self.animator.setDefaultState("Idle")
        self.animator.addAnimationState("FastRunning")

        self.running: bool = False

        def startPlayBack(animator: Animator):
            return glm.length(self.v) > 0.1
            return self.running

        def endPlayBack(animator: Animator):
            return glm.length(self.v) <= 0.1

        self.animator.addTransition("Idle", "FastRunning", 0.2, startPlayBack)
        self.animator.addTransition("FastRunning", "Idle", 0.1, endPlayBack)

        self.forward: glm.vec3 = glm.vec3(0, 0, 1)
        self.right: glm.vec3 = glm.vec3(1, 0, 0)
        self.up: glm.vec3 = glm.vec3(0, 1, 0)
        self.transform = self.model.transform
        self.model.transform.rotation = glm.angleAxis(glm.pi(), glm.vec3(0, 1, 0))
        self.facingDir = glm.vec3(0)
        self.v = glm.vec3(0)

    def followCameraDirection(self, cam: Camera):
        self.forward = -glm.vec3(cam.forward())
        self.forward[1] = 0
        self.forward = glm.normalize(self.forward)
        self.right = glm.vec3(cam.right())
        self.right[1] = 0
        self.right = glm.normalize(self.right)

    def OnUpdate(self, window: Window):
        deltaTime = window.deltaTime
        keys = window.keys

        self.running = keys[pg.K_k]

        horizentalAxis = keys[pg.K_d] - keys[pg.K_a]
        horizentalDir = horizentalAxis * self.right

        verticalAxis = keys[pg.K_s] - keys[pg.K_w]
        verticalDir = verticalAxis * self.forward

        newMovementDir = horizentalDir + verticalDir

        if newMovementDir == glm.vec3(0):
            self.v = glm.lerp(self.v, glm.vec3(0), 40 * deltaTime)
            self.facingDir = glm.vec3(0)
            return

        self.facingDir = glm.normalize(newMovementDir)

        self.v = glm.lerp(self.v, self.facingDir * 50, 15 * deltaTime)

        toRotation = glm.angleAxis(glm.atan(self.facingDir[0], self.facingDir[2]), glm.vec3(0, 1, 0))
        self.transform.rotation = glm.slerp(self.transform.rotation, toRotation, 10 * deltaTime)
        self.transform.position = glm.vec3(glm.lerp(self.transform.position, self.v * deltaTime + self.transform.position, 10 * deltaTime))
