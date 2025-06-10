import pygame as pg
from AnimationSystem import AnimationSystem
from Window import Window
from GameObject import GameObject
from Model import Model
from Animator import Animator
from pyglm import glm

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

        AnimationSystem.AddAnimation(self.animator)

        self.running: bool = False
        self.runningDir = glm.vec3(0)

        def startPlayBack(animator: Animator):
            return self.running

        def endPlayBack(animator: Animator):
            return not self.running

        self.animator.addTransition("Idle", "FastRunning", 0.12, startPlayBack)
        self.animator.addTransition("FastRunning", "Idle", 0.14, endPlayBack)

    def OnStart(self):
        pass

    def OnUpdate(self, window: Window):
        keys = window.keys

        self.running = keys[pg.K_k]
        newDir = glm.vec3(keys[pg.K_a] - keys[pg.K_d], 0, keys[pg.K_w] - keys[pg.K_s])
        if newDir != glm.vec3(0):
            self.runningDir = newDir
            self.model.transform.rotation = glm.angleAxis(glm.atan(self.runningDir[0], self.runningDir[2]), glm.vec3(0, 1, 0))

        # cam = GameObjectSystem.gameObjects[0].inher
