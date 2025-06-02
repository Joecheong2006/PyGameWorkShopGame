import glm

class Camera:
    def __init__(self, position: glm.vec3, fov: float, aspect: float, near: float, far: float):
        self.fov = fov
        self.aspect = aspect
        self.near = near
        self.far = far

        self.position = position
        self.rotation = glm.vec3(0, 0, -90)

        self.up = glm.vec3(0, 1, 0)
        self.right = glm.vec3(1, 0, 0)
        self.forward = glm.vec3(0, 0, -1)

        self.viewMat = glm.mat4(1.0)
        self.projectionMat = glm.mat4(1.0)
        self.updateProjectionMat()

    def lookAt(self, target: glm.vec3):
        self.viewMat = glm.lookAt(self.position, target, self.up)

    def updateProjectionMat(self):
        self.projectionMat = glm.perspective(self.fov, self.aspect, self.near, self.far)

    def rotate(self, angle: glm.vec3):
        self.rotation += angle

        direction = glm.vec3()
        direction.x = glm.cos(glm.radians(self.rotation.z)) * glm.cos(glm.radians(self.rotation.y))
        direction.y = glm.sin(glm.radians(self.rotation.y))
        direction.z = glm.sin(glm.radians(self.rotation.z)) * glm.cos(glm.radians(self.rotation.y))

        self.forward = glm.normalize(direction)
        self.right = glm.cross(self.forward, glm.vec3(0, 1, 0))
        self.up = glm.cross(self.right, self.forward)
        self.lookAt(self.position + self.forward)
