import pygame
import pymunk

class CircleObject:
    '''
    Store all circle object data and method
    '''
    def __init__(self, space, 
                 position=(0,0), radius=1, mass=1, elasticity=0.75,
                 pivot_max_force=500,
                 color=(128, 128, 128, 100), isDynamic=True, 
                 imgPath=None) -> None:
        
        # pymunk setup
        self.original_position=position
        self.add_to_space=[]
        if(isDynamic):
            self.body = pymunk.Body()
            self.pivot = pymunk.PivotJoint(space.static_body, self.body, (0,0), (0,0))
            self.pivot.max_bias = 0 # disable joint correction
            self.pivot.max_force = pivot_max_force # emulate linear friction
            self.add_to_space.extend([self.body, self.pivot])
        else:
            self.body = pymunk.Body(body_type=pymunk.Body.STATIC)
            self.add_to_space.extend(self.body)
        
        self.body.position = position
        self.shape = pymunk.Circle(self.body, radius)
        self.shape.mass = mass
        self.shape.color = color
        self.shape.elasticity=elasticity
        self.add_to_space.extend([self.shape])
        self.radius = radius
        
        space.add(*self.add_to_space)

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
        
        self.rect = self.image.get_rect()
    
    def draw(self, window):
        window.blit(self.image, (self.body.position[0]-self.radius, self.body.position[1]-self.radius))
    
    def reset(self):
        # print('done')
        self.body._set_position(self.original_position)
        self.body._set_velocity((0.0, 0.0))


class RectObject:
    '''
    Store all rectangle object data and method
    '''
    def __init__(self, space, 
                 position=(0,0), size=(50,50), mass=1, elasticity=0.75,
                 pivot_max_force=500,
                 color=(128, 128, 128, 100), isDynamic=True, 
                 imgPath=None) -> None:
        
        # pymunk setup
        if(isDynamic):
            self.body = pymunk.Body()
        else:
            self.body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.body.position = position
        
        self.shape = pymunk.Poly.create_box(self.body, size)
        self.shape.mass = mass
        self.shape.color = color
        self.shape.elasticity=elasticity
        self.size=size

        # self.pivot = pymunk.PivotJoint(space.static_body, self.body, (0,0), (0,0))
        # self.pivot.max_bias = 0 # disable joint correction
        # self.pivot.max_force = pivot_max_force # emulate linear friction
        # self.pivot
        space.add(self.body, self.shape)

        # pygame setup
        if(imgPath==None):
            # Create the circle surface
            self.image = pygame.Surface(self.size)
            self.image.fill(self.shape.color[:3])
            # self.image.set_colorkey((0,0,0))
            # pygame.draw.rect(self.image, self.shape.color, ((0,0), self.size))
        else:
            self.image = pygame.image.load(imgPath)
            self.image = self.image.convert_alpha()
            self.image = pygame.transform.scale(self.image, (self.radius*2, self.radius*2))
        
        self.rect = self.image.get_rect()
    
    def draw(self, window):
        window.blit(self.image, (self.body.position[0]-self.size[0]/2, self.body.position[1]-self.size[1]/2))
