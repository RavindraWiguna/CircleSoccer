import pygame
import pymunk
import pymunk.pygame_util

from ball import Ball
from player import Player
from gameobject import RectObject
from enums import CollisionType, GamePhase
from math_util import *

import time
import os
import random
from functools import partial
import neat
from neatUtils import visualize

### === PYGAME SETUP === ###
pygame.init()
MULT = 8
WIDTH, HEIGHT = 160*MULT, 95*MULT
min_dim = min(WIDTH, HEIGHT)
norm_div = min_dim/2
constant = 2/min_dim
window = pygame.display.set_mode((WIDTH, HEIGHT))
bg = pygame.image.load('assets/images/bg.png')
bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))
SCORE_FONT = pygame.font.SysFont('magneto', 40)
score_data = {'A':0,'B':0}
game_phase = GamePhase.Normal

### === neat reward setup ###
second_last_toucher=0
last_ball_toucher_id=0
fitness_recorder = {'A':0, 'B':0} # team fitness and individu fitness too
ronde_time = time.perf_counter()
solo_touch_ball_counter=0

multiplier_fitness_iter_touch = 500
max_touch = 4
max_drible = 3
# list of 24 bool per list containing 4 boolean for 4 wall for 6 player tanda ngetouch
# males ngehandle duplikat, takut ngappend modif list gonna ada bug (barengan?)
isHitWall = [0]*24

### === PYMUNK SETUP === ###
# make space where we will simulate
space = pymunk.Space()
static_body = space.static_body
draw_options = pymunk.pygame_util.DrawOptions(window)

### === DRAWING FUNCTIONS === ###

def draw_score(window, a, b):
    pygame.draw.rect(window, (255, 255, 255), (WIDTH/2-90, 0, 180, 50))
    score_text = SCORE_FONT.render(f'{a:02d} : {b:02d}', 1, (16, 16, 16))
    window.blit(score_text, (WIDTH/2-85, 10))

def draw(window, objs, score_data, space=None, drawing_options=None, isDebug=False):
    window.blit(bg, (0,0))
    draw_score(window, score_data['A'], score_data['B'])
    
    if(isDebug):
        space.debug_draw(drawing_options)
    else:
        for obj in objs:
            obj.draw(window)


### === GAME SPECIFIC FUNCTIONS === ###

def create_boundaries(space, width, height, bwidth):
    # format: cx,cy, w,h
    mid_width = width/2
    mid_height = height/2
    offset = bwidth/3
    rects = [
        # top wall
        [(mid_width, -offset), (width, bwidth), CollisionType.WALL_TOP.value],
        
        # bottom wall
        [(mid_width, height+offset), (width, bwidth), CollisionType.WALL_BOTTOM.value],

        # left wall
        [(-offset, mid_height), (bwidth, height), CollisionType.WALL_LEFT.value],

        # right wall
        [(width+offset, mid_height), (bwidth, height), CollisionType.WALL_RIGHT.value]
    ]
    for pos, size, coltype in rects:
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.position = pos

        shape = pymunk.Poly.create_box(body, size)
        shape.elasticity = 0.9
        shape.friction = 0.5
        shape.color = (128, 8, 8, 100)
        space.add(body, shape)
        shape.collision_type=coltype

'''
=====================
   SEPAK BOLA FUNC
=====================
'''
def isTeamA(id):
    return id < 6 and id > 0

def isTeamB(id):
    return id > 6

def goal_a_handler(arbiter, space, data):
    global score_data, game_phase, last_ball_toucher_id, second_last_toucher
    if(game_phase==GamePhase.Normal):
        score_data['B']+=1
        fitness_recorder['B']+=1200
        fitness_recorder['A']-=2000
        # print('A -20| B + 12')
        game_phase=GamePhase.JUST_GOAL

        if(isTeamB(last_ball_toucher_id)):
            # eyo dia ngegolin
            fitness_recorder[last_ball_toucher_id]+=3000.0
            # print(last_ball_toucher_id, 'score the goal for tim B dia')

    return True

def goal_b_handler(arbiter, space, data):
    global score_data, game_phase, last_ball_toucher_id, second_last_toucher
    if(game_phase==GamePhase.Normal):
        score_data['A']+=1
        fitness_recorder['A']+=1200
        fitness_recorder['B']-=2000
        # print('A + 12| B -20 ')
        game_phase=GamePhase.JUST_GOAL

        if(isTeamA(last_ball_toucher_id)):
            # bruh tim A ngegol ke B? mantap
            fitness_recorder[last_ball_toucher_id]+=3000.0

    return True

def ball_touch_handler(collision_type_toucher, arbiter, space, data):
    global fitness_recorder, last_ball_toucher_id, second_last_toucher, ronde_time, solo_touch_ball_counter
    
    if(not fitness_recorder.__contains__(collision_type_toucher)):
        fitness_recorder[collision_type_toucher]=0
    
    # print(collision_type_toucher, 'touch the ball')
    # fitness_recorder[collision_type_toucher]
    solo_touch_ball_counter+=1
    solo_touch_ball_counter = min(max_touch, solo_touch_ball_counter)
    if(solo_touch_ball_counter < max_touch):
        # print('reset')
        ronde_time = time.perf_counter()

    # check if someone lose the ball
    if(last_ball_toucher_id==0):
        # skip, gak ada lose ball
        pass

    # ok semua ke cek, now return
    if(last_ball_toucher_id==collision_type_toucher):
        # ga ada beda, dari pada second sama last sama
        return True
    
    # ok beda orang, ganti
    second_last_toucher=last_ball_toucher_id
    last_ball_toucher_id=collision_type_toucher
    return True

# make partial func
team_a1_ball_handler = partial(ball_touch_handler, CollisionType.A_P1.value)
team_a2_ball_handler = partial(ball_touch_handler, CollisionType.A_P2.value)
team_a3_ball_handler = partial(ball_touch_handler, CollisionType.A_P3.value)

team_b1_ball_handler = partial(ball_touch_handler, CollisionType.B_P1.value)
team_b2_ball_handler = partial(ball_touch_handler, CollisionType.B_P2.value)
team_b3_ball_handler = partial(ball_touch_handler, CollisionType.B_P3.value)

'''
==============
  GAME UTIL
==============
'''

def reset_objects(objs):
    for obj in objs:
        obj.reset()

def reset_score():
    global score_data
    score_data['A']=0
    score_data['B']=0

def kick_player(player):
    player.body._set_position((-10,-10))

def get_player_team_goal(team_A, team_B, goal_a, goal_b, asA):
    if(asA):
        player = team_A[0]
        self_team=team_A
        opo_team=team_B
        self_goal=goal_a
        opo_goal=goal_b
    else:
        player = team_B[0]
        self_team=team_B
        opo_team=team_A
        self_goal=goal_b
        opo_goal=goal_a
    
    return player, self_team, opo_team, self_goal, opo_goal

'''
=======================
  GAME TERMINATION UTL
=======================
'''
def out_of_bound_check(objs, width, height):
    existOutOfBound=False
    for obj in objs:
        px, py = obj.body.position
        # print(px, py)
        if(px < -10 or py < -10 or px > width or py > height):
            # endgame_fitness() keluar juga ga dikasi reward
            existOutOfBound=True
            print(obj.body.velocity)
            print('out of bound with tolerance')
            break
    
    return existOutOfBound

def wall_collision_handler(offset_id_wall, offset_id_toucher, arbiter, space, data):
    global isHitWall
    isHitWall[offset_id_wall+offset_id_toucher]=1
    return True

# make partial func for wall
top_wall_hit_handler    = partial(wall_collision_handler, 0)
bottom_wall_hit_handler = partial(wall_collision_handler, 6)
left_wall_hit_handler   = partial(wall_collision_handler, 12)
right_wall_hit_handler  = partial(wall_collision_handler, 18)

# make partial func for collision each player
team_a1_twall_handler = partial(top_wall_hit_handler, 0)
team_a2_twall_handler = partial(top_wall_hit_handler, 1)
team_a3_twall_handler = partial(top_wall_hit_handler, 2)
team_b1_twall_handler = partial(top_wall_hit_handler, 3)
team_b2_twall_handler = partial(top_wall_hit_handler, 4)
team_b3_twall_handler = partial(top_wall_hit_handler, 5)

team_a1_bwall_handler = partial(bottom_wall_hit_handler, 0)
team_a2_bwall_handler = partial(bottom_wall_hit_handler, 1)
team_a3_bwall_handler = partial(bottom_wall_hit_handler, 2)
team_b1_bwall_handler = partial(bottom_wall_hit_handler, 3)
team_b2_bwall_handler = partial(bottom_wall_hit_handler, 4)
team_b3_bwall_handler = partial(bottom_wall_hit_handler, 5)

team_a1_lwall_handler = partial(left_wall_hit_handler, 0)
team_a2_lwall_handler = partial(left_wall_hit_handler, 1)
team_a3_lwall_handler = partial(left_wall_hit_handler, 2)
team_b1_lwall_handler = partial(left_wall_hit_handler, 3)
team_b2_lwall_handler = partial(left_wall_hit_handler, 4)
team_b3_lwall_handler = partial(left_wall_hit_handler, 5)

team_a1_rwall_handler = partial(right_wall_hit_handler, 0)
team_a2_rwall_handler = partial(right_wall_hit_handler, 1)
team_a3_rwall_handler = partial(right_wall_hit_handler, 2)
team_b1_rwall_handler = partial(right_wall_hit_handler, 3)
team_b2_rwall_handler = partial(right_wall_hit_handler, 4)
team_b3_rwall_handler = partial(right_wall_hit_handler, 5)

# player id udah include sama tim, 0-5
def check_hitting_wall(player_id, player:Player):
    global isHitWall
    dirX, dirY = player.direction
    topoff, botoff, leftoff, rightoff = 0,6,12,18

    # top wall
    if(isHitWall[topoff+player_id]==1 and dirY==-1 and dirX==0):
        # nyentuh dan nabrak
        return True
    
    # bottom wall
    if(isHitWall[botoff+player_id]==1 and dirY==1 and dirX==0):
        return True

    # left wall
    if(isHitWall[leftoff+player_id]==1 and dirY==0 and dirX==-1):
        return True

    # right wall
    if(isHitWall[rightoff+player_id]==1 and dirY==0 and dirX==1):
        return True
    
    return False

def check_velocity(velocity, threshold):
    vx, vy = velocity
    if(abs(vx)+abs(vy) > threshold):
        return True
    return False

def check_force(force, threshold):
    fx, fy = force
    total_mag = calculate_distance((0,0), (fx, fy))
    if(total_mag > threshold):
        return True
    return False


def checkAllStandStill(players, ball, doWallCheck):
    existMovement=False
    vel_threshold = 1e-6

    for obj, index in players:            
        existMovement = check_velocity(obj.body.velocity, vel_threshold)
        if(existMovement):
            # cek apa gerak tapi nabrak tembok
            isHittingWall = check_hitting_wall(index, obj)
            if(isHittingWall):
                existMovement=False

        # kalau lewat 2 2 nya ok ada gerakan        
        if(existMovement):break
    
    ### END OF FOR LOOP ###

    # kalau player gak gerak, cek bola
    if(not existMovement):
        ball_vel_good = check_velocity(ball.body.velocity, vel_threshold)
        existMovement=ball_vel_good

    return existMovement


'''
==================
   AI INPUT UTIL
=================
'''

def get_ball_pos_vel(ball, constant, norm_vel_div):
    ball_datas = []
    x,y = ball.body.position
    x = -1 + (x * constant)
    y = -1 + (y  * constant)

    vx, vy = ball.body.velocity/norm_vel_div
    ball_datas.extend([x,y, vx, vy])
    return ball_datas

def get_player_pos_vel(body, constant, norm_vel_div):
    x,y = body.position
    x = -1 + (x * constant)
    y = -1 + (y  * constant) # yes ttp pakek max x

    vx, vy = body.velocity/norm_vel_div
    return [x,y, vx, vy]


def get_team_pos_vel(team, skip_id, min_dim, norm_vel_div):
    team_mate_pos_vel = []
    constant = 2/min_dim
    for i, player in enumerate(team):
        if(i == skip_id):
            continue
        
        x,y,vx,vy = get_player_pos_vel(player.body, constant, norm_vel_div)
        team_mate_pos_vel.extend([x,y,vx,vy])
    
    return team_mate_pos_vel
    

def get_boundary_distance(position, max_x, max_y, constant):
    # top wall -> sama dgn y koor
    # ---
    
    # left wall -> sama dgn x koor
    # ---

    # bottom wall
    d_bottom = max_y - position[1]
    d_bottom *= constant

    # right wall
    d_right = max_x - position[0]
    d_right *= constant
    return [d_bottom, d_right]

def get_position_distance(src_pos, dst_pos, constant):
    dx = dst_pos[0]-src_pos[0]
    dy = dst_pos[1]-src_pos[1]
    
    dx*=constant
    dy*=constant
    return [dx, dy]

def make_data_masuk_solo(self_team, opo_team, self_goal, opo_goal, ball, id_self, width, height, min_dim, norm_div, constant):
    player = self_team[id_self]
    # self team posv
    self_pos_vel            = get_player_pos_vel(player.body, constant, norm_div)

    # ball posv dis
    ball_data               = get_ball_pos_vel(ball, constant, norm_div)
    ball_distance           = get_position_distance(player.body.position, ball.body.position, constant)

    # wall dis
    wall_data               = get_boundary_distance(player.body.position, width, height, constant)

    # goals dis
    opponent_goal_data      = get_position_distance(player.body.position, opo_goal[0].body.position, constant)
    opponent_goal_tiang_l   = get_position_distance(player.body.position, opo_goal[1].body.position, constant)
    opponent_goal_tiang_r   = get_position_distance(player.body.position, opo_goal[2].body.position, constant)

    # ball to goal
    opponent_goal_data_ball      = get_position_distance(ball.body.position, opo_goal[0].body.position, constant)
    opponent_goal_tiang_l_ball   = get_position_distance(ball.body.position, opo_goal[1].body.position, constant)
    opponent_goal_tiang_r_ball   = get_position_distance(ball.body.position, opo_goal[2].body.position, constant)
    
    bias=0.5

    the_input = [*self_pos_vel, *ball_data, *ball_distance, *wall_data, 
    *opponent_goal_data, *opponent_goal_tiang_l, *opponent_goal_tiang_r,
    *opponent_goal_data_ball, *opponent_goal_tiang_l_ball, *opponent_goal_tiang_r_ball, bias]
    return the_input

'''
================
 AI FITNESS UTIL
================
'''
def initialize_fitness(genome):
    if(genome.fitness == None):
        genome.fitness=0.0

def endgame_fitness():
    global fitness_recorder, score_data
    if(score_data['A']>score_data['B']):
        fitness_recorder['A']+=5000
        fitness_recorder['B']-=5000
        # print('A win')
    elif(score_data['A']<score_data['B']):
        fitness_recorder['A']-=5000
        fitness_recorder['B']+=5000
        # print('B win')
    else:
        # draw
        fitness_recorder['A']+=250
        fitness_recorder['B']+=250
        # print('Got Draw')

# FITNESS BALLZkalo mendekati bola
def calculate_ball_fitness(player, ball):
    final_distance_ball = calculate_distance(player.body.position, ball.body.position)
    max_fitness = calculate_distance((0,0), (WIDTH, HEIGHT))
    fitness = 1 - final_distance_ball/max_fitness
    fitness *=17
    # fitness = max_fitness - final_distance_ball
    # print(max_fitness, final_distance_ball
    # fitness /= 1000 # (karena main 6 ronde) # ku kecilin lgi
    return fitness

def calculate_ball_goal_fitness(opo_goal, ball):
    final_distance_goal = calculate_distance(opo_goal.body.position, ball.body.position)
    max_fitness = calculate_distance((0,0), (WIDTH, HEIGHT))
    fitness = 1 - final_distance_goal/max_fitness
    fitness *=500
    return fitness

'''
=================
  AI OUTPUT UTIL
=================
'''
def cap_magnitude(val, max_val, min_val):
    val = max(min_val, min(max_val, val))
    return val

# get vx vy
def process_output(output, genome, player):
    addVx = output[0] - output[1]
    addVy = output[2] - output[3]
    player.change_velocity(addVx, addVy)

def solve_players(players):
    for player in players:
        player.solve()


### ==== MAIN FUNCTION ==== ###

def game(window, width, height, genomes, config, doRandom, asA):
    global game_phase, score_data, last_ball_toucher_id, second_last_toucher, fitness_recorder, ronde_time, solo_touch_ball_counter
    '''
    =============================
      PYGAME-PYMUNK LOOP SETUP
    =============================
    '''
    isRun = True
    clock = pygame.time.Clock()
    fps = 120
    step=5
    dt = 1/(step*fps)

    '''
    ======================================
           SPAWN GAME'S OBJECTS
    ======================================
    '''
    # BORDER FOR BOUNCE
    wall_width=50
    create_boundaries(space, width, height, wall_width)
    wall_width=4
    
    # GAME'S BALL
    ball = Ball(space, (width/2, height/2))
    ball.shape.collision_type=CollisionType.BALL.value
     
    # GOALS variable
    height_goal = 175
    width_goal=6
    width_tiang=48
    height_tiang=width_goal
    goal_a = [
        # vertical sensor
        RectObject(space, (wall_width+width_goal/2, height/2), (width_goal, height_goal), 1, 0.4, 500, isDynamic=False, color=(225, 225, 225, 100)),
        
        # tiang bawah
        RectObject(space, (wall_width+width_tiang/2, height/2+height_goal/2+height_tiang/2), (width_tiang, height_tiang), 1, 0.4, 500, isDynamic=False, color=(225, 225, 225, 100)),

        # tiang atas
        RectObject(space, (wall_width+width_tiang/2, height/2-height_goal/2-height_tiang/2), (width_tiang, height_tiang), 1, 0.4, 500, isDynamic=False, color=(225, 225, 225, 100))
    ]

    goal_a[0].shape.collision_type=CollisionType.GOAL_A.value
    # print(ball.shape.collision_type, goal_a[0].shape.collision_type)
    goal_a_sensor = space.add_collision_handler(ball.shape.collision_type, goal_a[0].shape.collision_type)
    goal_a_sensor.begin=goal_a_handler

    offsetb=-6
    goal_b = [
        # vertical sensor
        RectObject(space, (width-wall_width-width_goal/2+offsetb, height/2), (width_goal, height_goal), 1, 0.4, 500, isDynamic=False, color=(225, 225, 225, 100)),
        
        # tiang bawah
        RectObject(space, (width-wall_width-width_tiang/2+offsetb, height/2+height_goal/2+height_tiang/2), (width_tiang, height_tiang), 1, 0.4, 500, isDynamic=False, color=(225, 225, 225, 100)),

        # tiang atas
        RectObject(space, (width-wall_width-width_tiang/2+offsetb, height/2-height_goal/2-height_tiang/2), (width_tiang, height_tiang), 1, 0.4, 500, isDynamic=False, color=(225, 225, 225, 100))
    ]

    goal_b[0].shape.collision_type=CollisionType.GOAL_B.value
    # print(ball.shape.collision_type, goal_b[0].shape.collision_type)
    goal_b_sensor = space.add_collision_handler(ball.shape.collision_type, goal_b[0].shape.collision_type)
    goal_b_sensor.begin=goal_b_handler


    ## === TEAM A === LEFT IS THE RIGHT SIDE!
    COLOR_A = (200, 100, 0, 100)
    team_A = [
        # keeper (ceritanya)
        Player(space, (width/8, height/2), COLOR_A),
    ]
    team_A[0].shape.collision_type=CollisionType.A_P1.value

    team_A_sensors = [
        # collision type, function
        [[ball.shape.collision_type, team_a1_ball_handler], [CollisionType.WALL_TOP.value, team_a1_twall_handler], 
        [CollisionType.WALL_BOTTOM.value, team_a1_bwall_handler], [CollisionType.WALL_LEFT.value, team_a1_lwall_handler],
        [CollisionType.WALL_RIGHT.value, team_a1_rwall_handler]],
    ]
    # add collision handler to space
    for i, player_collision_stuff in enumerate(team_A_sensors):
        for coltype, function in player_collision_stuff:
            temporary = space.add_collision_handler(coltype, team_A[i].shape.collision_type)
            temporary.begin = function

    ### === TEAM B === ###
    COLOR_B = (0, 100, 200, 100)
    team_B = [
        # keeper (ceritanya)
        Player(space, (width/8*7, height/2), COLOR_B),
    ]
    team_B[0].shape.collision_type=CollisionType.B_P1.value

    team_B_sensors = [
        # collision type, function
        [[ball.shape.collision_type, team_b1_ball_handler], [CollisionType.WALL_TOP.value, team_b1_twall_handler], 
        [CollisionType.WALL_BOTTOM.value, team_b1_bwall_handler], [CollisionType.WALL_LEFT.value, team_b1_lwall_handler],
        [CollisionType.WALL_RIGHT.value, team_b1_rwall_handler]],
    ]

    for i, player_collision_stuff in enumerate(team_B_sensors):
        for coltype, function in player_collision_stuff:
            temporary = space.add_collision_handler(coltype, team_B[i].shape.collision_type)
            temporary.begin = function

    if(doRandom):
        objs = [*team_A, *team_B]
        for obj in objs:
            rx = random.uniform(100, width-100)
            ry = random.uniform(100, height-100)
            obj.body._set_position((rx, ry))

    # kick player
    if(asA):
        need_kick = [team_B[0]]
    else:
        need_kick = [team_A[0]]
    
    for player in need_kick:
        kick_player(player)

    '''
    ====================
       Making 1 models
    ====================
    '''

    team_net = [
        (neat.nn.RecurrentNetwork.create(genomes[0][1], config), genomes[0]),
    ]

    # initlaize fitness
    for genomeid, genome in genomes:
        initialize_fitness(genome)


    '''
    ========================
            MAIN LOOP
    ========================
    '''
    start_time_after_goal=None
    wait_after_goal=0.0
    max_ronde_time =3.0 # reset

    # reset global var
    score_data = {'A':0,'B':0}
    game_phase = GamePhase.Normal
    second_last_toucher=0
    last_ball_toucher_id=0
    fitness_recorder = {'A':0, 'B':0, 'mendekat':0} # team fitness and individu fitness too
    solo_touch_ball_counter=0

    # get player, self goal, opo goal, team, etc
    net, genome = team_net[0]
    player, self_team, opo_team, self_goal, opo_goal = get_player_team_goal(team_A, team_B, goal_a, goal_b, asA)
    player_solve = [player]
    
    index = 0 if asA else 3
    player_cek = [[player, index]]

    # fit fit kalo mendekat dapet boolean 1 menjauh no point, karna spawn bisa deket bisa jauh, gak ku normalize juga, boolean aja
    prev_distance_ball = calculate_distance(player.body.position, ball.body.position)

    forceQuit=False
    ronde_time = time.perf_counter()
    while isRun:
        doVisualize=False
        for event in pygame.event.get():
            if(event.type== pygame.QUIT):
                forceQuit=True
                isRun=False
                print('force quit')
                break
        
        keys = pygame.key.get_pressed()
        if(keys[pygame.K_SPACE]):
            doVisualize=True
        
        existMovement=False

        # gerakin player
        the_input = make_data_masuk_solo(self_team, opo_team, self_goal, opo_goal, ball, 0, width, height, min_dim, norm_div, constant)
        # output probability action
        output = net.activate(the_input)
        process_output(output, genome, player)
        
        # IMPORTANT! solve the player movement
        solve_players(player_cek)

        # update world and graphics
        for _ in range(step):
            space.step(dt)
        
        if(doVisualize):
            draw(window, [ball, *team_A, *team_B, *goal_a, *goal_b], score_data, space, draw_options, True)
            pygame.display.update()
            # clock.tick(fps)

        # update fitness
        cur_distance_ball = calculate_distance(player.body.position, ball.body.position)
        if(cur_distance_ball < prev_distance_ball and abs(cur_distance_ball-prev_distance_ball) > 50):
            fitness_recorder['mendekat']+=1
            prev_distance_ball=cur_distance_ball

        # check termination
        if(game_phase==GamePhase.JUST_GOAL):

            if(start_time_after_goal is None):
                start_time_after_goal=time.perf_counter()
            
            # jika melebihi 3 detik setelah goal (yes pakek if because if training.. uhh..., mengding gpp stpi skip 1.0)
            if(time.perf_counter()-start_time_after_goal >= wait_after_goal):
                # end ronde
                endgame_fitness()
                isRun=False
                print('get to 1 goal stop')
                break
        
        # same, check termination
        existMovement=checkAllStandStill(player_cek, ball, True)
        if(not existMovement and game_phase != GamePhase.KICKOFF):
            # lsg break
            # endgame_fitness() no move ga dikasi reward
            isRun=False
            # punish!!!!!!!!!!
            fitness_recorder['A']-=500
            fitness_recorder['B']-=500
            # print('no move')
            # ga usah di punish
        else:
            game_phase=GamePhase.Normal

        # cek apakah out o bound
        objs = [ball, player]
        isOutOfBound = out_of_bound_check(objs, width, height)
        if(isOutOfBound):
            isRun=False
            # punish
            fitness_recorder['A'] -=1000
            fitness_recorder['B'] -=1000


        if (time.perf_counter()-ronde_time) > max_ronde_time:
            endgame_fitness() # kasi, sapa tau draw beneran
            isRun=False
            # punish
            fitness_recorder['A'] -= 1000
            fitness_recorder['B'] -= 1000
            print(player.direction, player.body.position)
            print('time out! PUNISH TO THE HELL kalo kalah')
            break
    ### === END OF WHILE LOOP === ###

    # calculate sisa fitness tim A & B + individu
    
    if(asA):
        genomes[0][1].fitness += fitness_recorder['A'] + fitness_recorder.get(CollisionType.A_P1.value, 0.0)
    else:
        genomes[0][1].fitness += fitness_recorder['B'] + fitness_recorder.get(CollisionType.B_P1.value, 0.0)

    # GOALZ
    fitness_goalz = calculate_ball_goal_fitness(opo_goal[0], ball)
    genomes[0][1].fitness += fitness_goalz

    # mendekat
    genomes[0][1].fitness += min(fitness_recorder['mendekat'], 1000)

    # remove object from space? or just remove space
    for obj in space.bodies:
        space.remove(obj)
    for obj in space.shapes:
        space.remove(obj)
    for obj in space.constraints:
        space.remove(obj)
    # print('done', total_ronde)
    # pygame.quit()
    return forceQuit

def set_fitness_val(genomes, val=0.0):
    for gid, genome in genomes:
        genome.fitness= val

def create_team(genomes, id):
    if(id + 3 <= len(genomes)):
        return genomes[id:id+3], id+3
    else:
        print('nanggung..., skip aja males mikir')
        return None, len(genomes)

def make_teams(genomes):
    teams = []
    id = 0
    while id < len(genomes):
        team, new_id = create_team(genomes, id)
        if(team):
            teams.append(team)
        id=new_id
    return teams

def eval_genomes(genomes, config):
    set_fitness_val(genomes)
    total_repeat = 3
    for id_genome in range(len(genomes)):
        for _ in range(total_repeat):
            fq = game(window, WIDTH, HEIGHT, [genomes[id_genome]], config, True, True)
            fq = game(window, WIDTH, HEIGHT, [genomes[id_genome]], config, True, False)
            if(fq):break



def run(config_file):
    # Load configuration.
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)

    # Create the population, which is the top-level object for a NEAT run.
    p = neat.Population(config)

    # # Add a stdout reporter to show progress in the terminal.

    # Run for up to 300 generations.
    import pickle
    # p = pickle.load(open('pop_vel.pkl', 'rb'))
    # p = neat.Checkpointer.restore_checkpoint('neat-checkpoint-508')
    # p.config=config
     
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    p.add_reporter(neat.Checkpointer(30))
    try:
        winner = p.run(eval_genomes, 1000)
        with open('winner_vel_fit.pkl', 'wb') as mfile:
            pickle.dump(winner, mfile)
            mfile.close()
            print('FINISHED')
    except KeyboardInterrupt:
        print('voila')

    visualize.plot_stats(p.reporters.reporters[1], ylog=False, view=True)
    visualize.plot_species(p.reporters.reporters[1], view=True)



    with open('pop_vel_fit.pkl', 'wb') as mfile:
        pickle.dump(p, mfile)
        mfile.close()
        print('save population')



if __name__ == '__main__':
    # Determine path to configuration file. This path manipulation is
    # here so that the script will run successfully regardless of the
    # current working directory.
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, './neatUtils/config-neat-vel-fit')
    run(config_path)
    pygame.quit()