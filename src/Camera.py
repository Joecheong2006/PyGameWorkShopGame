import pygame as pg
from pyglm import glm
import math

from GameObjectSystem import GameObject
from Window import Window

from collections import namedtuple
PerspectiveCameraState = namedtuple('PerspectiveCameraState', 'fov aspect near far')
OrthogonalCameraState = namedtuple('OrthogonalCameraState', 'left right bottom top near far')

class Camera(GameObject):
    def __init__(self, position: glm.vec3, window: Window):
        self.position = position
        self.aspect = window.width / window.height
        super().__init__(self)

    def OnStart(self):
        self.rotation = glm.quat(glm.vec3(0))

        self.max_pitch = math.radians(89.0)
        self.pitch = 0.0
        self.yaw = 0.0

        self.projectionMat = glm.mat4(1.0)

        self.state = None

        self.calOrthogonalMat(OrthogonalCameraState(-1, 1, -1 / self.aspect, 1 / self.aspect, 0.1, 100))
        self.calPerspectiveMat(PerspectiveCameraState(glm.radians(45), self.aspect, 0.1, 100))

    def OnUpdate(self, window: Window):
        sensitivity = 0.003

        dx, dy = window.rel[0], window.rel[1]

        yaw_angle = -dx * sensitivity
        pitch_angle = -dy * sensitivity

        new_pitch = self.pitch + pitch_angle
        new_pitch = max(-self.max_pitch, min(self.max_pitch, new_pitch))
        pitch_angle = new_pitch - self.pitch
        self.pitch = new_pitch

        yaw_quat   = glm.angleAxis(yaw_angle, glm.vec3(0, 1, 0))
        pitch_quat = glm.angleAxis(pitch_angle, self.right())

        delta_rotation = yaw_quat * pitch_quat
        self.rotation = glm.normalize(delta_rotation * self.rotation)

        keys = window.keys

        dir = glm.vec3(0, 0, 0)
        if keys[pg.K_w]:
            dir += self.forward()
        if keys[pg.K_s]:
            dir -= self.forward()
        if keys[pg.K_d]:
            dir += self.right()
        if keys[pg.K_a]:
            dir -= self.right()
        if keys[pg.K_SPACE]:
            dir += glm.vec3(0, 1, 0)
        if dir != glm.vec3(0):
            self.position += 2 * glm.normalize(dir) * window.deltaTime


    def forward(self):
        return self.rotation * glm.vec3(0, 0, -1)

    def up(self):
        return self.rotation * glm.vec3(0, 1, 0)

    def right(self):
        return self.rotation * glm.vec3(1, 0, 0)

    def getViewMatrix(self):
        target = self.position + self.forward()
        return glm.lookAt(self.position, target, self.up())

    def lookAt(self, target: glm.vec3):
        self.viewMat = glm.lookAt(self.position, target, self.up())

    def calOrthogonalMat(self, state: OrthogonalCameraState):
        self.projectionMat = glm.ortho(*state)
        self.state = state

    def calPerspectiveMat(self, state: PerspectiveCameraState):
        self.projectionMat = glm.perspective(*state)
        self.state = state
