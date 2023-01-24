import pygame
import pymunk
import pymunk.pygame_util
import cv2
import numpy as np
from ball import Ball

### === PYGAME SETUP === ###
pygame.init()
MULT = 8
WIDTH, HEIGHT = 160*MULT, 95*MULT
window = pygame.display.set_mode((WIDTH, HEIGHT))
bg_img = cv2.imread('bg.png')
bg_img = cv2.rotate(bg_img, cv2.ROTATE_90_CLOCKWISE)
bg_img = cv2.resize(bg_img, (HEIGHT, WIDTH))
bg = pygame.surfarray.make_surface(bg_img)
# print(type(bg_img), bg_img.shape, bg_img.dtype)


### === PYMUNK SETUP === ###
# make space where we will simulate
space = pymunk.Space()
static_body = space.static_body
# add gravity direction (x,y)
# space.gravity = (0.0, 480) # could be 9.81 just different speed
draw_options = pymunk.pygame_util.DrawOptions(window)

def draw(space, window, draw_options, ball):
    # window.fill('white')
    window.blit(bg, (0,0))
    # space.debug_draw(draw_options)
    window.blit(ball.image, (ball.body.position[0]-ball.radius, ball.body.position[1]-ball.radius))
    pygame.display.update()

def calculate_distance(src, dst):
    dx = src[0]-dst[0]
    dy = src[1]-dst[1]
    return np.sqrt(dx*dx + dy*dy)

def calculate_angle(src, dst):
    return np.arctan2(dst[1]-src[1], dst[0]-src[0])

# def create_ball(space, radius, mass, position):
#     body = pymunk.Body()
#     body.position = position
#     shape = pymunk.Circle(body, radius)
#     shape.mass = mass
#     shape.color = (128, 255, 64, 100) # R,G,B,A
#     shape.elasticity=0.75
#     # shape.friction=0.9
#     pivot = pymunk.PivotJoint(static_body, body, (0,0), (0,0))
#     pivot.max_bias = 0 # disable joint correction
#     pivot.max_force = 1000 # emulate linear friction
#     space.add(body, shape, pivot)
#     return shape

def create_boundaries(space, width, height):
    # format: cx,cy, w,h
    mid_width = width/2
    mid_height = height/2
    rects = [
        # top wall
        [(mid_width, 5), (width, 10)],
        
        # bottom wall
        [(mid_width, height-5), (width, 10)],

        # left wall
        [(5, mid_height), (10, height)],

        # right wall
        [(width-5, mid_height), (10, height)]
    ]
    for pos, size in rects:
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.position = pos

        shape = pymunk.Poly.create_box(body, size)
        shape.elasticity = 0.75
        # shape.friction = 0.9
        shape.color = (128, 8, 8, 100)
        space.add(body, shape)


def run(window, width, height):
    isRun = True
    clock = pygame.time.Clock()
    fps = 60
    step=3
    dt = 1/(step*fps)

    ### === pymunk setup === ###
    # sample object
    # ball = create_ball(space, 24, 5, (WIDTH/2,HEIGHT/2))
    ball = Ball(space, (WIDTH/2, HEIGHT/2), 24, 5)
    create_boundaries(space, WIDTH, HEIGHT)

    while isRun:
        for event in pygame.event.get():
            if(event.type== pygame.QUIT):
                isRun=False
                break
            elif(event.type==pygame.MOUSEBUTTONDOWN):
                # give impulse (m*v?) to what vector (x,y) to what local coor
                ball.body.apply_impulse_at_local_point((1000, 50), (0,0))
        draw(space, window, draw_options, ball)
        for _ in range(step):
            space.step(dt)
        clock.tick(fps)
        

    
    pygame.quit()


if __name__ == '__main__':
    run(window, WIDTH, HEIGHT)