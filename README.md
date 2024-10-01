# PyGameHot

PyGameHot is a hot-reloading utility for `Pygame`

<!-- add a disclaimer that this is still in the early stages of development 
-->

:warning: **Disclaimer:** ~I did not use pygame at all, I spent more time on building this utility than the library itself :D~ I spent a couple of hours on pygame, take this with a grain of salt, this is a simple wrapper on a runnable HotGame class. Pretty simple and naive loop consiting of `check deps --> compile --> show errors if any --> configure game --> run game --> repeat`

## Features

- Hot-reloading of game code
- minimal-easy base class to wrap games & game loops
- copy-paste 1 file 
- deep file dependencies


## Usage

**You can copy and paste the contents of [this](https://github.com/ivanbelenky/pygame-hot/blob/main/pygamehot/hotreloader.py) file and import `HotGame` as needed.**

## Installation


```bash
git clone https://github.com/ivanbelenky/pygame-hot.git
cd pygame-hot
poetry init
poetry install
```

## `HotGame`

```python
import pygame
from pygamehot import HotGame, run_game

class MyGame(HotGame):
    class Config:
        width = 800
        height = 600
        caption = "Game!"

    def __init__(self): ...
    def update(self, events): ...

if __name__ == "__main__":
    run_game(__file__)
```

