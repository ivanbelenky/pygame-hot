from pygamehot import run_game

import pygame 
from pygame.locals import *
from pygamehot import HotGame, Commands


class Game(HotGame):
    class Config:
        width = 800
        height = 600
        caption = "Game!"

    def __init__(self):
        super().__init__()
        self.background = (135, 206, 255)
        self.ground_color = (0, 0, 0)

        self.player = pygame.Surface((100, 100))
        self.player.fill((255, 0, 0))
        self.player_x = 300
        self.player_y = 450-3

    def update(self, events) -> None | Commands:
        self.screen.fill(self.background)
        pygame.draw.rect(self.screen, self.ground_color, (0, 500, 800, 100))
        self.screen.blit(self.player, (self.player_x, self.player_y))

        for event in events:
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                return Commands.QUIT
            if event.type == KEYDOWN or event.type == KEYUP:
                displacement = 5
                if event.key in [K_a, K_LEFT]: 
                    self.player_x -= displacement
                if event.key in [K_d, K_RIGHT]: self.player_x += displacement
                


if __name__ == "__main__":
    run_game(__file__)