# ivanbelenky 2024
import os
import ast
import time
import traceback
import logging
from pathlib import Path
from enum import Enum
from collections import defaultdict

import pygame
from pygame.locals import *

FPS = 200

class GameNotFound(Exception): pass
class InvalidFileDep(Exception): pass

class Commands(Enum):
    QUIT = 0

logger = logging.getLogger(__name__)
logging.basicConfig(format='[%(levelname)s]: %(message)s - %(asctime)s', level=logging.INFO)

clock = pygame.time.Clock()

class HotGameMeta(type):
    def __new__(cls, name, bases, attrs):
        config = attrs.pop('Config', dict())
        new_class = super().__new__(cls, name, bases, attrs)
        new_class._screen_settings = {
            'width': getattr(config, "width", 800), 
            'height': getattr(config, "height", 600), 
            'caption': getattr(config, "caption", "Game")
        }
        return new_class


class HotGame(metaclass=HotGameMeta):    
    def __init__(self):
        self.pressed_keys = defaultdict(lambda: False)
    
    def update_pressed_keys(self, events):
        for event in events:
            if event.type == KEYDOWN: self.pressed_keys[event.key] = True
            elif event.type == KEYUP: self.pressed_keys[event.key] = False

    def start_game(self):
        pygame.init()
        if not hasattr(self, "screen"):
            self.screen_from_settings(self._screen_settings)

    def screen_from_settings(self, settings):
        self.screen = pygame.display.set_mode((settings['width'], settings['height']))
        pygame.display.set_caption(settings['caption'])

    def update(self): raise NotImplementedError("run method not implemented")

    @classmethod
    def from_instance(cls, instance):
        new_instance = cls()
        new_instance.screen = instance.screen
        return new_instance
    

class FileDep:
    def __init__(self, name, path):
        self.same, self.path = name, path
        self.last_modified = os.path.getmtime(path)
        self.validate()
        self.fp = open(path, "r")

    def hash(self) -> str: return hex(hash(open(self.path, "r").read()))
    def close(self): return open(self.path, "r").close()
    def __del__(self): self.close()

    def changed(self): 
        dt = int(os.path.getmtime(self.path))
        changed = self.last_modified != dt
        if changed: self.last_modified = dt
        return changed

    def read(self) -> str: 
        self.fp.seek(0) # panic check
        content = self.fp.read()
        self.fp.seek(0)
        return content

    def validate(self):
        try: compile(open(self.path, "r").read(), self.path, "exec")
        except Exception as e: raise InvalidFileDep(e)


def _get_game(code: str | FileDep) -> ast.Module:
    if isinstance(code, FileDep): code = code.read()
    game_module = ast.parse(code)
    game_defined = False
    for node in game_module.body:
        if isinstance(node, ast.ClassDef):
            if any(b.id == HotGame.__name__ for b in node.bases):
                game_defined, game_cls_name = True, node.name
                break
    if not game_defined:
        raise GameNotFound("No class inheriting from HotGame found.")
    return game_module, game_cls_name

    
def setup_game(entry_point: FileDep):
    logger.info(f"Setting up game from {entry_point.path}")
    game_module, game_cls_name = _get_game(entry_point)
    game_code = compile(game_module, "<game>: ", "exec")
    exec(game_code, locals())
    game_class: HotGame = locals()[game_cls_name]
    game: HotGame = game_class()
    return game


def run_game(game_fp: str | Path):    
    entry_point = FileDep("game", game_fp)
    game = setup_game(entry_point)
    game.start_game()

    # TODO: add all file dependencies
    deps = [entry_point]
    c = 0
    while True:
        clock.tick(FPS)
        c += 1
        try:
            events = pygame.event.get()
            game.update_pressed_keys(events)
            cmd = game.update(events)
            
            
            pygame.display.update()
            
            match cmd:
                case Commands.QUIT:
                    pygame.quit()
                    break

            if (c % FPS == 0) and any(dep.changed() for dep in deps):
                game_ready = False
                while not game_ready:
                    try: 
                        game = setup_game(entry_point)
                        game_ready = True
                        logger.info("RELOADING GAME")
                    except Exception as e:
                        logger.error(e)
                        logger.exception(traceback.format_exc())
                        logger.info("Waiting for file changes...")
                        while not any(dep.changed() for dep in deps): 
                            time.sleep(2)

                game.start_game()
                c = 0
            c %= FPS

        except Exception as e:
            logger.error(e)
            logger.exception(traceback.format_exc())
            pygame.quit()
            break