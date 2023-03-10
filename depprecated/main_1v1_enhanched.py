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

def draw(window, objs, score_data):
    window.blit(bg, (0,0))
    draw_score(window, score_data['A'], score_data['B'])
    for obj in objs:
        obj.draw(window)


### === GAME SPECIFIC FUNCTIONS === ###

def create_boundaries(space, width, height, bwidth):
    # format: cx,cy, w,h
    mid_width = width/2
    mid_height = height/2
    rects = [
        # top wall
        [(mid_width, bwidth/2), (width, bwidth)],
        
        # bottom wall
        [(mid_width, height-bwidth/2), (width, bwidth)],

        # left wall
        [(bwidth/2, mid_height), (bwidth, height)],

        # right wall
        [(width-bwidth/2, mid_height), (bwidth, height)]
    ]
    for pos, size in rects:
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.position = pos

        shape = pymunk.Poly.create_box(body, size)
        shape.elasticity = 0.9
        shape.friction = 0.5
        shape.color = (128, 8, 8, 100)
        space.add(body, shape)

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
        fitness_recorder['B']+=120
        fitness_recorder['A']-=200
        # print('A -20| B + 12')
        game_phase=GamePhase.JUST_GOAL

        if(isTeamB(last_ball_toucher_id)):
            # eyo dia ngegolin
            fitness_recorder[last_ball_toucher_id]+=300.0
            # print(last_ball_toucher_id, 'score the goal for tim B dia')
            if(isTeamB(second_last_toucher)):
                # hoo ngassist
                fitness_recorder[second_last_toucher]+=150.0
                # print(second_last_toucher, 'is the assist for tim B dia')
        else:
            # bruh tim A ngegol ke A? bunuh diri
            fitness_recorder[last_ball_toucher_id]-=500.0
            # print('A dummy dumb dumb', last_ball_toucher_id, 'just make own goal for tim B')

    return True

def goal_b_handler(arbiter, space, data):
    global score_data, game_phase, last_ball_toucher_id, second_last_toucher
    if(game_phase==GamePhase.Normal):
        score_data['A']+=1
        fitness_recorder['A']+=120
        fitness_recorder['B']-=200
        # print('A + 12| B -20 ')
        game_phase=GamePhase.JUST_GOAL

        if(isTeamB(last_ball_toucher_id)):
            # eyo dia bunuh diri b skor ke b
            fitness_recorder[last_ball_toucher_id]-=500.0
            # print('tim B owngoal,', last_ball_toucher_id)
            
        else:
            # bruh tim A ngegol ke B? mantap
            fitness_recorder[last_ball_toucher_id]+=300.0
            # print('messii of tim A', last_ball_toucher_id)
            if(isTeamA(second_last_toucher)):
                # hoo ngassist
                fitness_recorder[second_last_toucher]+=150.0
                # print('assit ma men A', second_last_toucher)

    return True

def ball_touch_handler(id_toucher, arbiter, space, data):
    global fitness_recorder, last_ball_toucher_id, second_last_toucher
    
    if(not fitness_recorder.__contains__(id_toucher)):
        fitness_recorder[id_toucher]=0
    
    # print(id_toucher, 'touch the ball')
    fitness_recorder[id_toucher]+=10

    # check if someone lose the ball
    if(last_ball_toucher_id==0):
        # skip, gak ada lose ball
        pass

    # touching the ball again, dribling, more point i guess
    elif(last_ball_toucher_id==id_toucher):
        fitness_recorder[id_toucher]+=30
        # print(id_toucher, 'dribble')

    
    # ok last ball beda with id toucher, and both > 6, meaning both are team B, or in other word same team
    elif(isTeamA(last_ball_toucher_id) and isTeamA(id_toucher)):
        fitness_recorder[last_ball_toucher_id]+=70
        fitness_recorder[id_toucher]+=60
        # print('A ngoper', last_ball_toucher_id, 'to', id_toucher)

    
    # same but with team b
    elif(isTeamB(last_ball_toucher_id) and isTeamB(id_toucher)):
        fitness_recorder[last_ball_toucher_id]+=70
        fitness_recorder[id_toucher]+=60
        # print('B ngoper', last_ball_toucher_id, 'to', id_toucher)


    # team b direbut tim a
    elif(isTeamB(last_ball_toucher_id) and isTeamA(id_toucher)):
        fitness_recorder[id_toucher]+=20
        fitness_recorder[last_ball_toucher_id]-=10
        # print('B lostball A', last_ball_toucher_id, 'to', id_toucher)


    # team a direbut tema 
    elif(isTeamA(last_ball_toucher_id) and isTeamB(id_toucher)):
        fitness_recorder[id_toucher]+=20
        fitness_recorder[last_ball_toucher_id]-=10
        # print('A lostball B', last_ball_toucher_id, 'to', id_toucher)


    # ok semua ke cek, now return
    if(last_ball_toucher_id==id_toucher):
        # ga ada beda, dari pada second sama last sama
        return True
    
    # ok beda orang, ganti
    second_last_toucher=last_ball_toucher_id
    last_ball_toucher_id=id_toucher
    return True

# make partial func
team_a1_handler = partial(ball_touch_handler, CollisionType.A_P1.value)
team_a2_handler = partial(ball_touch_handler, CollisionType.A_P2.value)
team_a3_handler = partial(ball_touch_handler, CollisionType.A_P3.value)

team_b1_handler = partial(ball_touch_handler, CollisionType.B_P1.value)
team_b2_handler = partial(ball_touch_handler, CollisionType.B_P2.value)
team_b3_handler = partial(ball_touch_handler, CollisionType.B_P3.value)

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
            print('out of bound with tolerance')
            break
    
    return existOutOfBound

# kalau tembok atas 1, bawah = 2, kiri = 4, kanan = 8, gak kena = 0 (semua bit mati) 
# ( tapi ya gak mungkin semua bit nyala, atas bawah nyala impos)
def detect_kena_tembok(position):
    '''
    bahaya kalo ganti width length but for now gud
    '''
    x, y = position
    
    sensor = 0
    # tembok ci- i mean atas-bawah:
    if(y < 30.0):
        # atas
        sensor +=1
    elif(y > 730):
        # bawah
        sensor +=2
    
    # tembok kiri kanan
    if(x < 35):
        # di kiri gawang or tembok kiri
        sensor += 4
    elif(x > 1238):
        # kanan, gawang or tembok kanan
        sensor +=8
    
    return sensor

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


def existMovementCheck(players, ball, doWallCheck):
    existMovement=False
    force_threshold = 3060
    vel_threshold = 1e-7
    for obj in players:
        # sensor tell kena tembok or no using bit stuff
        sensor=0
        if(doWallCheck):
            sensor=detect_kena_tembok(obj.body.position)
        
        # gak kena tembok atau gak dicek
        if(sensor==0):
            # print('no nabrak')
            # assume gak kena tembok, then check force
            existMovement = check_force(obj.body.force, force_threshold)
            if(existMovement): break
            
            else:
                # print('GA NABRAK TAPI GA ADA FORCE CEK VELOCITY')
                existMovement = check_velocity(obj.body.velocity, vel_threshold)
                if(existMovement):break

        
        else:
            # print('nabrak')
            # sensor != 0, berarti kenak at least 1 tembok
            # cek velo kalo nabrak tembok
            existMovement = check_velocity(obj.body.velocity, vel_threshold)
            if(existMovement):break
    
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

def make_data_masuk(self_team, opo_team, self_goal, opo_goal, ball, id_self, width, height, min_dim, norm_div, constant, type_game):
    player = self_team[id_self]
    # self team posv
    self_pos_vel            = get_player_pos_vel(player.body, constant, norm_div)
    
    if(type_game=='3v3'):
        self_team_data      = get_team_pos_vel(self_team, id_self, min_dim, norm_div)
    elif(type_game=='1v1' or type_game=='solo'):
        self_team_data      = [0.0, 0.0, 0.0, 0.0]*2 # pos x pos y, vx, vy

    # oponent posv
    if(type_game=='3v3'):
        opponent_data       = get_team_pos_vel(opo_team, -1, min_dim, norm_div)
    elif(type_game=='1v1'):
        opponent_data       = get_player_pos_vel(opo_team[0].body, constant, norm_div)
        opponent_data.extend([0.0, 0.0, 0.0, 0.0]*2)
    elif(type_game=='solo'):
        opponent_data = [0]*12

    # ball posv dis
    ball_data               = get_ball_pos_vel(ball, constant, norm_div)
    ball_distance           = get_position_distance(player.body.position, ball.body.position, constant)

    # wall dis
    wall_data               = get_boundary_distance(player.body.position, width, height, constant)

    # goals dis
    own_goal_data           = get_position_distance(player.body.position, self_goal[0].body.position, constant)
    own_goal_tiang_l        = get_position_distance(player.body.position, self_goal[1].body.position, constant)
    own_goal_tiang_r        = get_position_distance(player.body.position, self_goal[2].body.position, constant)
    opponent_goal_data      = get_position_distance(player.body.position, opo_goal[0].body.position, constant)
    opponent_goal_tiang_l   = get_position_distance(player.body.position, opo_goal[1].body.position, constant)
    opponent_goal_tiang_r   = get_position_distance(player.body.position, opo_goal[2].body.position, constant)
    
    the_input = [*self_pos_vel, *self_team_data, *opponent_data, *ball_data, *ball_distance,
            *wall_data, *own_goal_data, *own_goal_tiang_r, 
            *own_goal_tiang_l, *opponent_goal_data, *opponent_goal_tiang_l,
            *opponent_goal_tiang_r]
    

    # print(self_pos_vel, 'selfposvel')
    # print(self_team_data, 'timpv')
    # print(opponent_data, 'opopv')
    # print(ball_data, 'bdat')
    # print(ball_distance, 'bdis')
    # print(wall_data, 'walldat')
    # print(own_goal_data, 'ogdat')
    # print(own_goal_tiang_l, 'ogtldat')
    # print(own_goal_tiang_r, 'ogtrdat')
    # print(opponent_goal_data, 'opgdat')
    # print(opponent_goal_tiang_l, 'opgtldat')
    # print(opponent_goal_tiang_r, 'opgtrdat')
    # print(the_input)
    # raise NameError('ehe')
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
        fitness_recorder['A']+=1000
        fitness_recorder['B']-=1000
        # print('A win')
    elif(score_data['A']<score_data['B']):
        fitness_recorder['A']-=1000
        fitness_recorder['B']+=1000
        # print('B win')
    else:
        # draw
        fitness_recorder['A']+=250
        fitness_recorder['B']+=250
        # print('Got Draw')

# FITNESS BALLZ
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
    fitness *=17
    return fitness

'''
=================
  AI OUTPUT UTIL
=================
'''
def cap_magnitude(val, max_val, min_val):
    val = max(min_val, min(max_val, val))
    return val

# get fx, fy
def process_output(output, genome, multiplier):
    cumul_fx = output[0] - output[1] # (x positive  - (x negative) ) -> if x- > x+, then cumul fx < 0 
    cumul_fy = output[2] - output[3] # same

    cumul_fx*=multiplier
    cumul_fy*=multiplier

    cumul_fx = cap_magnitude(cumul_fx, 18000, -18000)
    cumul_fy = cap_magnitude(cumul_fy, 18000, -18000)

    # punish for doing nothing
    if(abs(cumul_fx) < 1e-5 and abs(cumul_fy) < 1e-5):
        genome[1].fitness -=0.1

    return cumul_fx, cumul_fy

### ==== MAIN FUNCTION ==== ###

def game(window, width, height, genomes, config, doRandom, asA):
    global game_phase, score_data, last_ball_toucher_id, second_last_toucher, fitness_recorder
    '''
    =============================
      PYGAME-PYMUNK LOOP SETUP
    =============================
    '''
    isRun = True
    clock = pygame.time.Clock()
    fps = 120
    step=1
    dt = 1/(step*fps)

    '''
    ======================================
           SPAWN GAME'S OBJECTS
    ======================================
    '''
    # BORDER FOR BOUNCE
    wall_width=4
    create_boundaries(space, width, height, wall_width)
    
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

    ball_sensor_A1          = space.add_collision_handler(ball.shape.collision_type, team_A[0].shape.collision_type)
    ball_sensor_A1.begin    = team_a1_handler

    COLOR_B = (0, 100, 200, 100)
    team_B = [
        # keeper (ceritanya)
        Player(space, (width/8*7, height/2), COLOR_B),
    ]
    team_B[0].shape.collision_type=CollisionType.B_P1.value

    ball_sensor_B1          = space.add_collision_handler(ball.shape.collision_type, team_B[0].shape.collision_type)
    ball_sensor_B1.begin    = team_b1_handler

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
    max_ronde_time = 5.0

    # reset global var
    score_data = {'A':0,'B':0}
    game_phase = GamePhase.Normal
    second_last_toucher=0
    last_ball_toucher_id=0
    fitness_recorder = {'A':0, 'B':0} # team fitness and individu fitness too

    # get player, self goal, opo goal, team, etc
    net, genome = team_net[0]
    player, self_team, opo_team, self_goal, opo_goal = get_player_team_goal(team_A, team_B, goal_a, goal_b, asA)

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
        the_input = make_data_masuk(self_team, opo_team, self_goal, opo_goal, ball, 0, width, height, min_dim, norm_div, constant, 'solo')
        # output FX and FY
        output = net.activate(the_input)
        fx, fy = process_output(output, genome, multiplier=3060)
        player._apply_force((fx, fy)) # di cap di sini

        # cek apakah ada movement (sebelum step, karena step ngereset force)
        player_cek = [player]
        existMovement=existMovementCheck(player_cek, ball, True)

        # update world and graphics
        # for _ in range(step):
        space.step(dt)
        if(doVisualize):
            draw(window, [ball, *team_A, *team_B, *goal_a, *goal_b], score_data)
            pygame.display.update()
            # clock.tick(fps)

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
        
        
        if(not existMovement and game_phase != GamePhase.KICKOFF):
            # lsg break
            # endgame_fitness() no move ga dikasi reward
            isRun=False
            # punish!!!!!!!!!!
            fitness_recorder['A']-=2500
            fitness_recorder['B']-=2500
            # print('no move')

            # cek apa nabrak tembok pas selesai, if yes punish lil bit
            sensor = detect_kena_tembok(player.body.position)
            # kalo kenak kurangi
            boolval = sensor > 0
            notboolval = not boolval
            fitness_recorder['A'] -= boolval * 500
            fitness_recorder['B'] -= boolval* 500
            # kalo gak kena kasi gud
            fitness_recorder['A'] += notboolval * 250
            fitness_recorder['B'] += notboolval * 250

        else:
            game_phase=GamePhase.Normal

        # cek apakah out o bound
        objs = [ball]
        if(asA):
            objs.append(team_A[0])
        else:
            objs.append(team_B[0])
        
        isOutOfBound = out_of_bound_check(objs, width, height)
        if(isOutOfBound):
            isRun=False


        if (time.perf_counter()-ronde_time) > max_ronde_time:
            endgame_fitness() # kasi, sapa tau draw beneran
            isRun=False
            # punish
            fitness_recorder['A'] -= 5000
            fitness_recorder['B'] -= 5000
            print('time out! PUNISH TO THE HELL kalo kalah')
            break

    # calculate sisa fitness tim A & B + individu
    
    if(asA):
        genomes[0][1].fitness += fitness_recorder['A'] + fitness_recorder.get(CollisionType.A_P1.value, 0.0)
    else:
        genomes[0][1].fitness += fitness_recorder['B'] + fitness_recorder.get(CollisionType.B_P1.value, 0.0)

    # BALLZ
    fitness_ballz = calculate_ball_fitness(player, ball)
    genomes[0][1].fitness +=fitness_ballz
    # print('ballfit', fitness_ballz)

    # GOALZ
    fitness_goalz = calculate_ball_goal_fitness(opo_goal[0], ball)
    genomes[0][1].fitness += fitness_goalz


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
    # p = neat.Population(config)

    # get previous population
    # print('Restoring...')
    import pickle
    # p = pickle.load(open('pop.pkl', 'rb'))
    p = neat.Checkpointer.restore_checkpoint('neat-checkpoint-223-force')
    p.config=config
    print(p.config==config)
    print(p.config)

    # Add a stdout reporter to show progress in the terminal.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    p.add_reporter(neat.Checkpointer(30))

    # Run for up to 300 generations.
    try:
        winner = p.run(eval_genomes, 1000)
        with open('winner1.pkl', 'wb') as mfile:
            pickle.dump(winner, mfile)
            mfile.close()
            print('FINISHED')
    except KeyboardInterrupt:
        print('voila')
    # Display the winning genome.
    # print('\nBest genome:\n{!s}'.format(winner))

    # # Show output of the most fit genome against training data.
    # print('\nOutput:')
    # winner_net = neat.nn.FeedForwardNetwork.create(winner, config)
    # for xi, xo in zip(xor_the_inputs, xor_outputs):
    #     output = winner_net.activate(xi)
    #     print("input {!r}, expected output {!r}, got {!r}".format(xi, xo, output))

    # node_names = {-1: 'A', -2: 'B', 0: 'A XOR B'}
    # visualize.draw_net(config, winner, True, node_names=node_names)
    # visualize.draw_net(config, winner, True, node_names=node_names, prune_unused=True)
    visualize.plot_stats(stats, ylog=False, view=True)
    visualize.plot_species(stats, view=True)



    with open('pop1.pkl', 'wb') as mfile:
        pickle.dump(p, mfile)
        mfile.close()
        print('save population')



if __name__ == '__main__':
    # Determine path to configuration file. This path manipulation is
    # here so that the script will run successfully regardless of the
    # current working directory.
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, './neatUtils/config-neat-new')
    run(config_path)
    pygame.quit()