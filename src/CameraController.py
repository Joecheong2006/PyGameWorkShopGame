import pygame as pg
from Camera import *
from Player import Player

from GameObjectSystem import GameObjectSystem

class CameraController(GameObject):
    def __init__(self):
        super().__init__(self)

        self.sensitivity = 0.2
        self.offset = glm.vec3(0.0, 2.0, 0.0)
        self.distance = 5.0
        self.max_pitch = 70
        self.rotationBlendingSpeed = 40
        self.positionBlendingSpeed = 50

    def OnStart(self):
        self.playerRef: Player | None = GameObjectSystem.FindFirstObjectByType(Player)
        self.camRef: Camera | None = GameObjectSystem.FindFirstObjectByType(Camera)

        if self.camRef == None:
            return
        self.camRef.calOrthogonalMat(OrthogonalCameraState(-self.distance, self.distance, -self.distance / self.camRef.aspect, self.distance / self.camRef.aspect, 0.1, 100))
        self.camRef.calPerspectiveMat(PerspectiveCameraState(glm.radians(45), self.camRef.aspect, 0.1, 100))

    def wrapAngleDeg(self, angle_deg: float):
        return (angle_deg + 180) % 360 - 180

    def OnUpdate(self, window: Window):
        deltaTime = window.deltaTime
        if self.playerRef and self.camRef:
            dx, dy = window.rel[0], window.rel[1]
            yaw_angle = -dx * self.sensitivity
            pitch_angle = -dy * self.sensitivity

            self.camRef.yaw += yaw_angle
            new_pitch = self.camRef.pitch + pitch_angle
            new_pitch = glm.clamp(new_pitch, -self.max_pitch, self.max_pitch)
            self.camRef.pitch = new_pitch

            desired_rotation = glm.quat(glm.vec3(glm.radians(self.camRef.pitch), glm.radians(self.camRef.yaw), 0))

            self.camRef.rotation = glm.quat(glm.slerp(
                self.camRef.rotation,
                desired_rotation,
                glm.clamp(self.rotationBlendingSpeed * deltaTime, 0.0, 1.0)
            ))

            playerDirection = -self.playerRef.facingDir
            if dx != 0 or dy != 0:
                self.playerRef.followCameraDirection(self.camRef)

            desired_position = self.playerRef.transform.position + glm.vec3(0, 1.5, 0) - self.camRef.forward() * self.distance

            self.camRef.position = glm.vec3(glm.lerp(
                self.camRef.position,
                desired_position,
                glm.clamp(self.positionBlendingSpeed * deltaTime, 0.0, 1.0)
            ))

