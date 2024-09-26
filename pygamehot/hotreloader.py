# ivanbelenky 2024
import importlib.util
import os
import ast
import traceback
import logging
import importlib
from pathlib import Path
from enum import Enum
from collections import defaultdict
from time import sleep

import pygame
from pygame.locals import *

FPS = 60
CHECK_SUFFIXES = (".py")
FPC = 60 # frames per check

class GameNotFound(Exception): pass
class InvalidFileDep(Exception): pass

class Commands(Enum):
    QUIT = 0

logger = logging.getLogger(__name__)
logging.basicConfig(format='[%(levelname)s]: %(message)s - %(asctime)s', level=logging.INFO)


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
        if not hasattr(self, "screen"):
            self.screen_from_settings(self._screen_settings)
        self.clock = pygame.time.Clock()

    def screen_from_settings(self, settings):
        self.screen = pygame.display.set_mode((settings['width'], settings['height']))
        pygame.display.set_caption(settings['caption'])

    def update(self): raise NotImplementedError("run method not implemented")

    @classmethod
    def from_instance(cls, instance):
        new_instance = cls()
        new_instance.screen = instance.screen
        return new_instance
    

def rewind(method):
    def wrapper(self, *args, **kwargs):
        self.fp.seek(0)
        r = method(self, *args, **kwargs)
        self.fp.seek(0)
        return r
    return wrapper


class FileDep:
    def __init__(self, name, path):
        self.name, self.path = name, path
        self.last_modified = os.path.getmtime(path)
        self.fp = open(path, "r")
        self.validate()
        
    def close(self): return self.fp.close()
    def __del__(self): self.close()

    def changed(self): 
        dt = os.path.getmtime(self.path)
        changed = self.last_modified != dt
        if changed: self.last_modified = dt
        return changed

    @rewind
    def hash(self) -> str: return hex(hash(self.fp.read()))
    @rewind
    def read(self) -> str: return self.fp.read()
    @rewind
    def validate(self):
        try: compile(self.fp.read(), self.path, "exec")
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

    
def setup_game(entry_point: FileDep, game_class=None):
    logger.info(f"Setting up game from {entry_point.path}")
    game_module, game_cls_name = _get_game(entry_point)
    game_code = compile(game_module, "<game>: ", "exec")
    exec(game_code, locals())
    game_class: HotGame = locals()[game_cls_name]
    game: HotGame = game_class()
    return game


def get_file_deps(entry_point: FileDep) -> list[FileDep]:
    files = [entry_point.fp]
    file_deps = [entry_point]
    seen = set()
    while files:
        f = files.pop()
        tree = ast.parse(f.read())
        imports = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
        specs = []
        for i in imports:
            if isinstance(i, ast.Import):
                for name in i.names:
                    if not name.name: continue
                    specs.append(importlib.util.find_spec(name.name))
            if isinstance(i, ast.ImportFrom):
                if i.module: 
                    specs.append(importlib.util.find_spec(i.module))
        for spec in specs:
            if spec is None: continue
            path = Path(spec.origin)
            if path.exists() and path.suffix in CHECK_SUFFIXES and path not in seen:
                seen.add(path)
                dep = FileDep(spec.name, path)
                file_deps.append(dep)
                files.append(dep.fp)
    return file_deps
    

def run_game(game_fp: str | Path):
    pygame.init()
    entry_point = FileDep("game", game_fp)
    game = setup_game(entry_point)
    game.start_game()

    deps = get_file_deps(entry_point)

    c = 0
    while True:
        failed = False
        game.clock.tick(FPS)
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

        except Exception as e:
            logger.error(e)
            logger.exception(traceback.format_exc())
            failed = True
            while not any(dep.changed() for dep in deps): 
                sleep(2)

        if ((c % FPC == 0) and any(dep.changed() for dep in deps)) or failed:
            game_ready = False
            while not game_ready:
                try: 
                    game = setup_game(entry_point, game.__class__.__name__)
                    deps = get_file_deps(entry_point)
                    game_ready = True
                    logger.info("RELOADING GAME")
                except Exception as e:
                    logger.error(e)
                    logger.exception(traceback.format_exc())
                    logger.info("Waiting for file changes...")
                    while not any(dep.changed() for dep in deps): 
                        sleep(2)
            game.start_game()
            game.clock.tick(FPS)
            c = 0
        c %= FPC