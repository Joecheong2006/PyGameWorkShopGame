import pygame as pg
from Camera import *

from GameObjectSystem import GameObjectSystem

class CameraController(GameObject):
    def __init__(self):
        super().__init__(self)

        self.sensitivity = 0.003

    def OnStart(self):
        cam: Camera | None = GameObjectSystem.FindFirstObjectByType(Camera)
        if cam == None:
            return
        cam.calOrthogonalMat(OrthogonalCameraState(-1, 1, -1 / cam.aspect, 1 / cam.aspect, 0.1, 100))
        cam.calPerspectiveMat(PerspectiveCameraState(glm.radians(45), cam.aspect, 0.1, 100))

    def OnUpdate(self, window: Window):
        cam: Camera | None = GameObjectSystem.FindFirstObjectByType(Camera)
        if cam == None:
            return

        dx, dy = window.rel[0], window.rel[1]

        yaw_angle = -dx * self.sensitivity
        pitch_angle = -dy * self.sensitivity

        new_pitch = cam.pitch + pitch_angle
        new_pitch = max(-cam.max_pitch, min(cam.max_pitch, new_pitch))
        pitch_angle = new_pitch - cam.pitch
        self.pitch = new_pitch

        yaw_quat   = glm.angleAxis(yaw_angle, glm.vec3(0, 1, 0))
        pitch_quat = glm.angleAxis(pitch_angle, cam.right())

        delta_rotation = yaw_quat * pitch_quat
        cam.rotation = glm.normalize(delta_rotation * cam.rotation)

        player: Player | None = GameObjectSystem.FindFirstObjectByType(Camera)
