import pygame
import pymunk

class CircleObject:
    '''
    Store all circle object data and method
    '''
    def __init__(self, space, 
                 position=(0,0), radius=1, mass=1, elasticity=0.75, 
                 color=(128, 128, 128, 100), isDynamic=True, 
                 imgPath=None) -> None:
        
        # pymunk setup
        if(isDynamic):
            self.body = pymunk.Body()
        else:
            self.body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.body.position = position
        
        self.shape = pymunk.Circle(self.body, radius)
        self.shape.mass = mass
        self.shape.color = color
        self.shape.elasticity=elasticity
        self.radius = radius

        self.pivot = pymunk.PivotJoint(space.static_body, self.body, (0,0), (0,0))
        self.pivot.max_bias = 0 # disable joint correction
        self.pivot.max_force = 1000 # emulate linear friction
        
        space.add(self.body, self.shape, self.pivot)

        # pygame setup
        if(imgPath==None):
            # Create the circle surface
            self.image = pygame.Surface((self.radius*2, self.radius*2))
            self.image.set_colorkey((0,0,0))
            pygame.draw.circle(self.image, self.shape.color, (self.radius, self.radius), self.radius)
        else:
            self.image = pygame.image.load(imgPath)
            self.image = self.image.convert_alpha()
            self.image = pygame.transform.scale(self.image, (self.radius*2, self.radius*2))
    
    def draw(self, window):
        window.blit(self.image, (self.body.position[0]-self.radius, self.body.position[1]-self.radius))
