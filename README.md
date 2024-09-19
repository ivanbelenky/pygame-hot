# PyGameHot

PyGameHot is a hot-reloading utility for `Pygame`

<!-- add a disclaimer that this is still in the early stages of development 
-->

:warning: **Disclaimer:** I did not use pygame at all, I spent more time on building this utility than the library itself :D 

## Features

- Hot-reloading of game code
- Easy-to-use base class for game development

## Installation

You can copy and paste the contents of [this](https://github.com/ivanbelenky/pygame-hot/blob/main/pygamehot/hotreloader.py) file and import `HotGame` as needed. 

```bash
git clone https://github.com/ivanbelenky/pygame-hot.git
cd pygame-hot
poetry init
poetry install
```

## `HotGame`

```python

class MyGame(HotGame):
    class Config:
        width = 800
        height = 600
        caption = "Game!"

    def __init__(self): ...
    def update(self, events): ...
```

