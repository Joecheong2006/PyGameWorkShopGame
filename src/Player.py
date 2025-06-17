import pygame as pg
from AnimationSystem import AnimationSystem
from Window import Window
from GameObject import GameObject
from Model import Model
from Animator import Animator
from pyglm import glm
from Camera import Camera

from collections import namedtuple
AABB = namedtuple('AABB', 'min max')

def aabbCollision(boxA: AABB, boxB: AABB):
    return (
        boxA.min[0] <= boxB.max[0] and boxA.max[0] >= boxB.min[0] and
        boxA.min[1] <= boxB.max[1] and boxA.max[1] >= boxB.min[1] and
        boxA.min[2] <= boxB.max[2] and boxA.max[2] >= boxB.min[2]
    )

def resolve_aabb_collision(boxA, boxB):
    dx1 = boxB.max[0] - boxA.min[0]
    dx2 = boxA.max[0] - boxB.min[0]
    dy1 = boxB.max[1] - boxA.min[1]
    dy2 = boxA.max[1] - boxB.min[1]
    dz1 = boxB.max[2] - boxA.min[2]
    dz2 = boxA.max[2] - boxB.min[2]

    mtv_x = dx1 if dx1 < dx2 else -dx2
    mtv_y = dy1 if dy1 < dy2 else -dy2
    mtv_z = dz1 if dz1 < dz2 else -dz2

    abs_mtv = [(abs(mtv_x), (mtv_x, 0, 0)),
               (abs(mtv_y), (0, mtv_y, 0)),
               (abs(mtv_z), (0, 0, mtv_z))]
    min_mtv = min(abs_mtv, key=lambda x: x[0])[1]

    return min_mtv 

class Player(GameObject):
    def __init__(self):
        super().__init__(self)

        self.model = Model("res/N.glb")

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

        self.aabb = AABB(self.transform.position + glm.vec3(-0.3, 0, -0.3), self.transform.position + glm.vec3(0.3, 2, 0.3))

        sitLocation = glm.vec3(-2, 0, -1)
        self.aabbBoxes: list[AABB] = [ 
                AABB(sitLocation + glm.vec3(-1.8, 0, -1.2), sitLocation + glm.vec3(0.6, 1, 0.5))
            ]

    def followCameraDirection(self, cam: Camera):
        self.forward = -glm.normalize(glm.vec3(cam.forward()) * glm.vec3(1, 0, 1))
        self.right = glm.normalize(glm.vec3(cam.right()) * glm.vec3(1, 0, 1))

    def OnUpdate(self, window: Window):
        deltaTime = window.deltaTime
        keys = window.keys

        self.aabb = AABB(self.transform.position + glm.vec3(-0.3, 0, -0.3), self.transform.position + glm.vec3(0.3, 2, 0.3))

        for box in self.aabbBoxes:
            if aabbCollision(self.aabb, box):
                self.transform.position += resolve_aabb_collision(self.aabb, box)

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
