import pygame
import pymunk
import pymunk.pygame_util
import math

pygame.init()

MULT = 8
WIDTH, HEIGHT = 105*MULT, 68*MULT
window = pygame.display.set_mode((WIDTH, HEIGHT))

def draw(space, window, draw_options):
    window.fill('white')
    space.debug_draw(draw_options)
    pygame.display.update()

def create_ball(space, radius, mass):
    body = pymunk.Body()
    body.position = (320, 320)
    shape = pymunk.Circle(body, radius)
    shape.mass = mass
    shape.color = (128, 255, 64, 100) # R,G,B,A
    shape.elasticity=0.8
    shape.friction=0.5
    space.add(body, shape)
    return shape

def create_boundaries(space, width, height):
    # format: cx,cy, w,h
    mid_width = width/2
    mid_height = height/2
    rects = [
        # top wall
        [(mid_width, 10), (width, 20)],
        
        # bottom wall
        [(mid_width, height-10), (width, 20)],

        # left wall
        [(10, mid_height), (20, height)],

        # right wall
        [(width-10, mid_height), (20, height)]
    ]
    for pos, size in rects:
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.position = pos

        shape = pymunk.Poly.create_box(body, size)
        shape.elasticity = 0.75
        shape.friction = 0.5
        space.add(body, shape)


def run(window, width, height):
    isRun = True
    clock = pygame.time.Clock()
    fps = 120
    dt = 1/fps

    ### === pymunk setup === ###
    # make space where we will simulate
    space = pymunk.Space()
    
    # add gravity direction (x,y)
    space.gravity = (0.0, 480) # could be 9.81 just different speed
    draw_options = pymunk.pygame_util.DrawOptions(window)


    # sample object
    ball = create_ball(space, 30, 10)
    create_boundaries(space, WIDTH, HEIGHT)

    while isRun:
        for event in pygame.event.get():
            if(event.type== pygame.QUIT):
                isRun=False
                break
            elif(event.type==pygame.MOUSEBUTTONDOWN):
                ball.apply_impulse

        draw(space, window, draw_options)
        space.step(dt)
        clock.tick(fps)
        

    
    pygame.quit()


if __name__ == '__main__':
    run(window, WIDTH, HEIGHT)