import pygame
import pymunk
import pymunk.pygame_util

from enums import GamePhase

# Initialize the pygame
pygame.init()

class CircleSoccer:
    SCORE_FONT = pygame.font.SysFont('magneto', 40)
    bg = pygame.image.load('assets/images/bg.png')

    def __init__(self, window, width, height) -> None:
        self.window = window
        self.width = width
        self.height = height

        # pymunk space setup
        space = pymunk.Space()
        static_body = space.static_body
        draw_options = pymunk.pygame_util.DrawOptions(window)

        # game data var
        self.game_phase = GamePhase.Normal
        self.score = {'A':0, 'B':0}

        # buat ballz


        pass
