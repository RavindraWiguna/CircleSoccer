import pygame
import pymunk

class Player:
    '''
    Store all player data and method
    '''
    def __init__(self, space, position=(0,0), radius=1, mass=1, elasticity=0.75, color=(128, 128, 128, 100)) -> None:
        # pymunk setup
        self.body = pymunk.Body()
        self.body.position = position
        self.shape = pymunk.Circle(self.body, radius)
        self.shape.mass = mass
        self.shape.color = (200, 200, 200, 100)
        self.shape.elasticity=elasticity

        self.pivot = pymunk.PivotJoint(space.static_body, self.body, (0,0), (0,0))
        self.pivot.max_bias = 0 # disable joint correction
        self.pivot.max_force = 1000 # emulate linear friction
        space.add(self.body, self.shape, self.pivot)

        # pygame setup
        self.radius = radius
        self.image = pygame.image.load('assets/images/betterball.png')
        self.image = self.image.convert_alpha()
        self.image = pygame.transform.scale(self.image, (self.radius*2, self.radius*2))