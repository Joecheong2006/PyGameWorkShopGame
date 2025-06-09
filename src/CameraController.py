from Camera import *
from GameObjectSystem import GameObjectSystem

class CameraController(GameObject):
    def __init__(self):
        super().__init__(self)

    def OnStart(self):
        self.sensitivity = 0.003

        cam: Camera = GameObjectSystem.gameObjects[0].inher
        cam.calOrthogonalMat(OrthogonalCameraState(-1, 1, -1 / cam.aspect, 1 / cam.aspect, 0.1, 100))
        cam.calPerspectiveMat(PerspectiveCameraState(glm.radians(45), cam.aspect, 0.1, 100))

    def OnUpdate(self, window: Window):
        cam: Camera = GameObjectSystem.gameObjects[0].inher

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

        keys = window.keys

        dir = glm.vec3(0, 0, 0)
        if keys[pg.K_w]:
            dir += cam.forward()
        if keys[pg.K_s]:
            dir -= cam.forward()
        if keys[pg.K_d]:
            dir += cam.right()
        if keys[pg.K_a]:
            dir -= cam.right()
        if keys[pg.K_SPACE]:
            dir += glm.vec3(0, 1, 0)
        if dir != glm.vec3(0):
            cam.position += 2 * glm.normalize(dir) * window.deltaTime
