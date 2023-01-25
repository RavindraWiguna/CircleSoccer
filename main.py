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

def isTeamA(id):
    return id < 6

def isTeamB(id):
    return not isTeamA(id)

def goal_a_handler(arbiter, space, data):
    global score_data, game_phase, last_ball_toucher_id, second_last_toucher
    if(game_phase==GamePhase.Normal):
        score_data['B']+=1
        fitness_recorder['B']+=12
        fitness_recorder['A']-=20
        print('A -20| B + 12')
        game_phase=GamePhase.JUST_GOAL

        if(isTeamB(last_ball_toucher_id)):
            # eyo dia ngegolin
            fitness_recorder[last_ball_toucher_id]+=30.0
            print(last_ball_toucher_id, 'score the goal for tim B dia')
            if(isTeamB(second_last_toucher)):
                # hoo ngassist
                fitness_recorder[second_last_toucher]+=15.0
                print(second_last_toucher, 'is the assist for tim B dia')
        else:
            # bruh tim A ngegol ke A? bunuh diri
            fitness_recorder[last_ball_toucher_id]-=50.0
            print('A dummy dumb dumb', last_ball_toucher_id, 'just make own goal for tim B')

    return True

def goal_b_handler(arbiter, space, data):
    global score_data, game_phase, last_ball_toucher_id, second_last_toucher
    if(game_phase==GamePhase.Normal):
        score_data['A']+=1
        fitness_recorder['A']+=12
        fitness_recorder['B']-=20
        print('A + 12| B -20 ')
        game_phase=GamePhase.JUST_GOAL

        if(isTeamB(last_ball_toucher_id)):
            # eyo dia bunuh diri b skor ke b
            fitness_recorder[last_ball_toucher_id]-=50.0
            print('tim B owngoal,', last_ball_toucher_id)
            
        else:
            # bruh tim A ngegol ke B? mantap
            fitness_recorder[last_ball_toucher_id]+=30.0
            print('messii of tim A', last_ball_toucher_id)
            if(isTeamA(second_last_toucher)):
                # hoo ngassist
                fitness_recorder[second_last_toucher]+=15.0
                print('assit ma men A', second_last_toucher)

    return True

def ball_touch_handler(id_toucher, arbiter, space, data):
    global fitness_recorder, last_ball_toucher_id, second_last_toucher
    
    if(not fitness_recorder.__contains__(id_toucher)):
        fitness_recorder[id_toucher]=0
    
    print(id_toucher, 'touch the ball')
    fitness_recorder[id_toucher]+=1

    # check if someone lose the ball
    if(last_ball_toucher_id==0):
        # skip, gak ada lose ball
        pass

    # touching the ball again, dribling, more point i guess
    elif(last_ball_toucher_id==id_toucher):
        fitness_recorder[id_toucher]+=3
        print(id_toucher, 'dribble')

    
    # ok last ball beda with id toucher, and both > 6, meaning both are team B, or in other word same team
    elif(isTeamA(last_ball_toucher_id) and isTeamA(id_toucher)):
        fitness_recorder[last_ball_toucher_id]+=7
        fitness_recorder[id_toucher]+=6
        print('A ngoper', last_ball_toucher_id, 'to', id_toucher)

    
    # same but with team b
    elif(isTeamB(last_ball_toucher_id) and isTeamB(id_toucher)):
        fitness_recorder[last_ball_toucher_id]+=7
        fitness_recorder[id_toucher]+=6
        print('B ngoper', last_ball_toucher_id, 'to', id_toucher)


    # team b direbut tim a
    elif(isTeamB(last_ball_toucher_id) and isTeamA(id_toucher)):
        fitness_recorder[id_toucher]+=2
        fitness_recorder[last_ball_toucher_id]-=1
        print('B lostball A', last_ball_toucher_id, 'to', id_toucher)


    # team a direbut tema 
    elif(isTeamA(last_ball_toucher_id) and isTeamB(id_toucher)):
        fitness_recorder[id_toucher]+=2
        fitness_recorder[last_ball_toucher_id]-=1
        print('A lostball B', last_ball_toucher_id, 'to', id_toucher)


    # ok semua ke cek, now return
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


def reset_objects(objs):
    for obj in objs:
        obj.reset()

def reset_score():
    global score_data
    score_data['A']=0
    score_data['B']=0

def get_ball_pos_vel(ball, min_dim, norm_vel_div):
    ball_datas = []
    x,y = ball.body.position
    x = -1 + x/min_dim * 2
    y = -1 + y/min_dim * 2 # yes ttp pakek max x

    vx, vy = ball.body.velocity
    vx /= norm_vel_div
    vy /= norm_vel_div
    ball_datas.extend([x,y, vx, vy])
    return ball_datas


def get_team_pos_vel(team, skip_id, min_dim, norm_vel_div):
    team_mate_pos_vel = []
    constant = 2/min_dim
    for i, player in enumerate(team):
        if(i==skip_id):
            continue
        
        x,y = player.body.position
        x = -1 + (x * constant)
        y = -1 + (y  * constant) # yes ttp pakek max x

        vx, vy = player.body.velocity/norm_vel_div
        team_mate_pos_vel.extend([x,y, vx, vy])
    
    return team_mate_pos_vel
    

def get_boundary_distance(position, max_x, max_y, min_dim):
    # top wall -> sama dgn y koor
    # ---
    
    # left wall -> sama dgn x koor
    # ---

    constant = 2/min_dim
    # bottom wall
    d_bottom = max_y - position[1]
    d_bottom *= constant

    # right wall
    d_right = max_x - position[0]
    d_right *= constant
    return [d_bottom, d_right]

def get_jarak_goal(position, goal_pos, min_dim):
    dx = goal_pos[0]-position[0]
    dy = goal_pos[1]-position[1]
    
    constant = 2/min_dim
    dx*=constant
    dy*=constant
    return [dx, dy]

def initialize_fitness(genome):
    if(genome.fitness == None):
        genome.fitness=0.0

def endgame_fitness():
    global fitness_recorder, score_data
    if(score_data['A']>score_data['B']):
        fitness_recorder['A']+=100
        fitness_recorder['B']-=100
        print('A win')
    elif(score_data['A']<score_data['B']):
        fitness_recorder['A']-=100
        fitness_recorder['B']+=100
        print('B win')
    else:
        # draw
        fitness_recorder['A']+=25
        fitness_recorder['B']+=25
        print('Got Draw')

### ==== MAIN FUNCTION ==== ###

def game(window, width, height, genomes, config, doRandom=False):
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
        
        # left wing 
        Player(space, (width/8*3, height/4), COLOR_A),

        # right wing
        Player(space, (width/8*3, height/4*3), COLOR_A),
    ]
    team_A[0].shape.collision_type=CollisionType.A_P1.value
    team_A[1].shape.collision_type=CollisionType.A_P2.value
    team_A[2].shape.collision_type=CollisionType.A_P3.value

    ball_sensor_A1          = space.add_collision_handler(ball.shape.collision_type, team_A[0].shape.collision_type)
    ball_sensor_A2          = space.add_collision_handler(ball.shape.collision_type, team_A[1].shape.collision_type)
    ball_sensor_A3          = space.add_collision_handler(ball.shape.collision_type, team_A[2].shape.collision_type)
    ball_sensor_A1.begin    = team_a1_handler
    ball_sensor_A2.begin    = team_a2_handler
    ball_sensor_A3.begin     = team_a2_handler

    COLOR_B = (0, 100, 200, 100)
    team_B = [
        # keeper (ceritanya)
        Player(space, (width/8*7, height/2), COLOR_B),
        
        # left wing 
        Player(space, (width/8*5, height/4), COLOR_B),

        # right wing
        Player(space, (width/8*5, height/4*3), COLOR_B),
    ]
    team_B[0].shape.collision_type=CollisionType.B_P1.value
    team_B[1].shape.collision_type=CollisionType.B_P2.value
    team_B[2].shape.collision_type=CollisionType.B_P3.value

    ball_sensor_B1          = space.add_collision_handler(ball.shape.collision_type, team_B[0].shape.collision_type)
    ball_sensor_B2          = space.add_collision_handler(ball.shape.collision_type, team_B[1].shape.collision_type)
    ball_sensor_B3          = space.add_collision_handler(ball.shape.collision_type, team_B[2].shape.collision_type)
    ball_sensor_B1.begin    = team_b1_handler
    ball_sensor_B2.begin    = team_b2_handler
    ball_sensor_B3.begin     = team_b2_handler

    if(doRandom):
        objs = [ball, *team_A, *team_B]
        for obj in objs:
            rx = random.uniform(30, width-30)
            ry = random.uniform(30, height-30)
            obj.body._set_position((rx, ry))


    '''
    ====================
       Making 6 models
    ====================
    '''
    # print(genomes[0])
    # ternyata genomes[id] -> genome1d, genome
    # team_A_net = [
    #     (neat.nn.FeedForwardNetwork.create(genomes[0][1], config), genomes[0]),
    #     (neat.nn.FeedForwardNetwork.create(genomes[1][1], config), genomes[1]),
    #     (neat.nn.FeedForwardNetwork.create(genomes[2][1], config), genomes[2]),
    # ]

    # team_B_net = [
    #     (neat.nn.FeedForwardNetwork.create(genomes[3][1], config), genomes[3]),
    #     (neat.nn.FeedForwardNetwork.create(genomes[4][1], config), genomes[4]),
    #     (neat.nn.FeedForwardNetwork.create(genomes[5][1], config), genomes[5]),
    # ]

    team_A_net = [
        (neat.nn.RecurrentNetwork.create(genomes[0][1], config), genomes[0]),
        (neat.nn.RecurrentNetwork.create(genomes[1][1], config), genomes[1]),
        (neat.nn.RecurrentNetwork.create(genomes[2][1], config), genomes[2]),
    ]

    team_B_net = [
        (neat.nn.RecurrentNetwork.create(genomes[3][1], config), genomes[3]),
        (neat.nn.RecurrentNetwork.create(genomes[4][1], config), genomes[4]),
        (neat.nn.RecurrentNetwork.create(genomes[5][1], config), genomes[5]),
    ]


    # initlaize fitness
    for genomeid, genome in genomes:
        initialize_fitness(genome)

    max_force = 18000

    '''
    ========================
            MAIN LOOP
    ========================
    '''
    min_dim = min(width, height)
    norm_div = min_dim/2
    start_time_after_goal=None
    wait_after_goal=0.0
    max_ronde_time = 15.0

    # reset global var
    score_data = {'A':0,'B':0}
    game_phase = GamePhase.Normal
    second_last_toucher=0
    last_ball_toucher_id=0
    fitness_recorder = {'A':0, 'B':0} # team fitness and individu fitness too

    forceQuit=False
    total_ronde=1
    ronde_time = time.perf_counter()
    while isRun:
        for event in pygame.event.get():
            if(event.type== pygame.QUIT):
                forceQuit=True
                isRun=False
                print('force quit')
                break
        
        existMovement=False
        # gerakin tim a
        for id, (net, genome) in enumerate(team_A_net):
            player = team_A[id]

            self_team_data = get_team_pos_vel(team_A, id, min_dim, norm_div)
            opponent_data = get_team_pos_vel(team_B, -1, min_dim, norm_div)
            ball_data = get_ball_pos_vel(ball, min_dim, norm_div)
            wall_data = get_boundary_distance(player.body.position, width, height, min_dim)
            own_goal_data = get_jarak_goal(player.body.position, goal_a[0].body.position, min_dim)
            own_goal_tiang_l = get_jarak_goal(player.body.position, goal_a[1].body.position, min_dim)
            own_goal_tiang_r = get_jarak_goal(player.body.position, goal_a[2].body.position, min_dim)
            opponent_goal_data = get_jarak_goal(player.body.position, goal_b[0].body.position, min_dim)
            opponent_goal_tiang_l = get_jarak_goal(player.body.position, goal_b[1].body.position, min_dim)
            opponent_goal_tiang_r = get_jarak_goal(player.body.position, goal_b[2].body.position, min_dim)

            input = [*self_team_data, *opponent_data, *ball_data, 
                     *wall_data, *own_goal_data, *own_goal_tiang_r, 
                     *own_goal_tiang_l, *opponent_goal_data, *opponent_goal_tiang_l,
                     *opponent_goal_tiang_r]

            # output FX and FY
            output = net.activate(input)
            
            if(abs(output[0]) < 1e-5 and abs(output[1]) < 1e-5):
                genome[1].fitness -=0.1

            fx, fy = output[0]*3060, output[1]*3060 # di multiply karena butuh big force and kasian networknya gedein sendiri
            fx = min(max_force, fx)
            fy = min(max_force, fy)
            player._apply_force((fx, fy))

        # gerakin tim b
        for id, (net, genome) in enumerate(team_B_net):
            player = team_B[id]

            self_team_data = get_team_pos_vel(team_B, id, min_dim, norm_div)
            opponent_data = get_team_pos_vel(team_B, -1, min_dim, norm_div)
            ball_data = get_ball_pos_vel(ball, min_dim, norm_div)
            wall_data = get_boundary_distance(player.body.position, width, height, min_dim)
            own_goal_data = get_jarak_goal(player.body.position, goal_b[0].body.position, min_dim)
            own_goal_tiang_l = get_jarak_goal(player.body.position, goal_b[1].body.position, min_dim)
            own_goal_tiang_r = get_jarak_goal(player.body.position, goal_b[2].body.position, min_dim)
            opponent_goal_data = get_jarak_goal(player.body.position, goal_a[0].body.position, min_dim)
            opponent_goal_tiang_l = get_jarak_goal(player.body.position, goal_a[1].body.position, min_dim)
            opponent_goal_tiang_r = get_jarak_goal(player.body.position, goal_a[2].body.position, min_dim)

            input = [*self_team_data, *opponent_data, *ball_data, 
                     *wall_data, *own_goal_data, *own_goal_tiang_r, 
                     *own_goal_tiang_l, *opponent_goal_data, *opponent_goal_tiang_l,
                     *opponent_goal_tiang_r]

            # output FX and FY
            output = net.activate(input)

            if(abs(output[0]) < 1e-5 and abs(output[1]) < 1e-5):
                genome[1].fitness -=0.1

            fx, fy = output[0]*3060, output[1]*3060 # di multiply karena butuh big force and kasian networknya gedein sendiri
            fx = min(max_force, fx)
            fy = min(max_force, fy)
            player._apply_force((fx, fy))

        # update world and graphics
        # for _ in range(step):
        space.step(dt)
        draw(window, [ball, *team_A, *team_B, *goal_a, *goal_b], score_data)
        pygame.display.update()
        # clock.tick(fps)

        if(game_phase==GamePhase.JUST_GOAL):
            # kalo udah 5 - 0 skip atau udah 10 detik from last goal
            # if(max(score_data.values())==5):
            #     endgame_fitness() # calculate end game finess
            #     # end ronde
            #     isRun=False
            #     print('get to 5')
            #     break

            if(start_time_after_goal is None):
                start_time_after_goal=time.perf_counter()
            
            # jika melebihi 3 detik setelah goal (yes pakek if because if training.. uhh..., mengding gpp stpi skip 1.0)
            if(time.perf_counter()-start_time_after_goal >= wait_after_goal):
                # restart ronde # NOPE, END RONDE, KARNA NEXT RONDE PASTI NGULANG
                # print('D:')
                # total_ronde+=1
                # reset_objects([ball, *team_A, *team_B])
                # game_phase=GamePhase.KICKOFF
                # start_time_after_goal=None
                # ronde_time=time.perf_counter()
                # end ronde
                isRun=False
                print('get to 1 goal stop')
                break
        
        # cek apakah ada movement
        objs = [ball, *team_A, *team_B]
        for obj in objs:
            vx, vy = obj.body.velocity
            if(abs(vx)+abs(vy) > 1e-7):
                existMovement=True
                # print(obj.body.velocity)
                break
        
        # cek apakah out o bound
        objs = [ball, *team_A, *team_B]
        for obj in objs:
            px, py = obj.body.position
            # print(px, py)
            if(px < 0 or py < 0 or px > width or py > height):
                isRun=False
                print('out of bound')
                break

        if(not existMovement and game_phase != GamePhase.KICKOFF):
            # lsg break
            isRun=False
            print('no move')
        else:
            game_phase=GamePhase.Normal

        if (time.perf_counter()-ronde_time) > max_ronde_time:
            endgame_fitness()
            isRun=False
            print('time out')
            break


    
    # calculate sisa fitness tim A & B + individu
    genomes[0][1].fitness += fitness_recorder['A'] + fitness_recorder.get(CollisionType.A_P1.value, 0.0)
    genomes[1][1].fitness += fitness_recorder['A'] + fitness_recorder.get(CollisionType.A_P2.value, 0.0)
    genomes[2][1].fitness += fitness_recorder['A'] + fitness_recorder.get(CollisionType.A_P3.value, 0.0)

    genomes[3][1].fitness += fitness_recorder['B'] + fitness_recorder.get(CollisionType.B_P1.value, 0.0)
    genomes[4][1].fitness += fitness_recorder['B'] + fitness_recorder.get(CollisionType.B_P2.value,0.0)
    genomes[5][1].fitness += fitness_recorder['B'] + fitness_recorder.get(CollisionType.B_P3.value,0.0)
    

    # remove object from space? or just remove space
    for obj in space.bodies:
        space.remove(obj)
    for obj in space.shapes:
        space.remove(obj)
    for obj in space.constraints:
        space.remove(obj)
    print('done', total_ronde)
    # pygame.quit()
    return forceQuit


def eval_genomes(genomes, config):
    for id_genome in range(0, len(genomes), 6):
        if(id_genome+6 > len(genomes)):
            six_players = genomes[id_genome:len(genomes)]
            kurang = 6-len(six_players)
            sisa = genomes[0:kurang]
            print(sisa[0][1].fitness)
            six_players.extend(sisa)
            fq = game(window, WIDTH, HEIGHT, six_players, config)
            if(fq):
                break
            
            six_players = six_players[::-1] # reverse it for reverse role
            fq = game(window, WIDTH, HEIGHT, six_players, config, True)
            if(fq):
                break
            # uh bagi sisa kita rata-ratain terus kali 2 a.k.a bagi 2 (/4 *2)
            for genomeid, genome in sisa:
                genome.fitness /= 2
        else:
            six_players = genomes[id_genome:id_genome+6]
            fq = game(window, WIDTH, HEIGHT, six_players, config)
            if(fq):
                break
            six_players = six_players[::-1] # reverse it for reverse role
            
            fq = game(window, WIDTH, HEIGHT, six_players, config, True)
            if(fq):
                break

def run(config_file):
    # Load configuration.
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)

    # Create the population, which is the top-level object for a NEAT run.
    p = neat.Population(config)

    # Add a stdout reporter to show progress in the terminal.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    p.add_reporter(neat.Checkpointer(20))

    # Run for up to 300 generations.
    winner = p.run(eval_genomes, 300)

    # Display the winning genome.
    print('\nBest genome:\n{!s}'.format(winner))

    # # Show output of the most fit genome against training data.
    # print('\nOutput:')
    # winner_net = neat.nn.FeedForwardNetwork.create(winner, config)
    # for xi, xo in zip(xor_inputs, xor_outputs):
    #     output = winner_net.activate(xi)
    #     print("input {!r}, expected output {!r}, got {!r}".format(xi, xo, output))

    # node_names = {-1: 'A', -2: 'B', 0: 'A XOR B'}
    # visualize.draw_net(config, winner, True, node_names=node_names)
    # visualize.draw_net(config, winner, True, node_names=node_names, prune_unused=True)
    visualize.plot_stats(stats, ylog=False, view=True)
    visualize.plot_species(stats, view=True)

    # p = neat.Checkpointer.restore_checkpoint('neat-checkpoint-50')
    # p.run(eval_genomes, 10)
    import pickle
    with open('winner.pkl', 'wb') as mfile:
        pickle.dump(winner, mfile)
        mfile.close()
        print('FINISHED')



if __name__ == '__main__':
    # run(window, WIDTH, HEIGHT)
    # Determine path to configuration file. This path manipulation is
    # here so that the script will run successfully regardless of the
    # current working directory.
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, './neatUtils/config-neat')
    run(config_path)