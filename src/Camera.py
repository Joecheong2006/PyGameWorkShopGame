import pygame as pg
from pyglm import glm
import math

from GameObject import GameObject
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
