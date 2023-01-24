import pygame
import pymunk
import pymunk.pygame_util
from ball import Ball
from player import Player
from math_util import *

### === PYGAME SETUP === ###
pygame.init()
MULT = 8
WIDTH, HEIGHT = 160*MULT, 95*MULT
window = pygame.display.set_mode((WIDTH, HEIGHT))
bg = pygame.image.load('assets/images/bg.png')
bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))


### === PYMUNK SETUP === ###
# make space where we will simulate
space = pymunk.Space()
static_body = space.static_body
# add gravity direction (x,y)
# space.gravity = (0.0, 480) # could be 9.81 just different speed
draw_options = pymunk.pygame_util.DrawOptions(window)

def draw(space, window, draw_options, objs):
    # window.fill('white')
    window.blit(bg, (0,0))
    # space.debug_draw(draw_options)
    for obj in objs:
        obj.draw(window)
    pygame.display.update()



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
    ball = Ball(space, (WIDTH/2, HEIGHT/2))
    team_a_1 = Player(space, (50, HEIGHT/2), (200, 100, 0, 100))
    # ball = CircleObject(space, (WIDTH/2, HEIGHT/2), 24, 5)
    create_boundaries(space, WIDTH, HEIGHT)

    while isRun:
        for event in pygame.event.get():
            if(event.type== pygame.QUIT):
                isRun=False
                break
            elif(event.type==pygame.MOUSEBUTTONDOWN):
                # give impulse (m*v?) to what vector (x,y) to what local coor
                ball.body.apply_impulse_at_local_point((1000, 50), (0,0))
        draw(space, window, draw_options, [ball, team_a_1])
        for _ in range(step):
            space.step(dt)
        clock.tick(fps)
        

    
    pygame.quit()


if __name__ == '__main__':
    run(window, WIDTH, HEIGHT)