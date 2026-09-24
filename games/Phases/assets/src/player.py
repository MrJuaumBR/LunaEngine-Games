# player.py
from lunaengine.core import LunaEngine
import pygame as pg
from typing import Tuple

class Player:
    def __init__(self, engine: LunaEngine, start_pos: Tuple[int, int]):
        self.engine = engine
        self.pos = list(start_pos)
        self.speed = 4
        self.size = (32 * self.engine.ratio.x, 32 * self.engine.ratio.y)
        self.facing_right = True

        try:
            surf = pg.image.load(self.engine.atlas.get_item('textures').path / 'player.png').convert_alpha()
            self.original_image = pg.transform.scale(surf, (int(self.size[0]), int(self.size[1])))
        except:
            self.original_image = pg.Surface((int(self.size[0]), int(self.size[1])))
            self.original_image.fill((0, 255, 0))

        # Start facing right (no flip)
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=self.pos)
        self.collision_rect = self.rect.inflate(-self.rect.width * 0.3, -self.rect.height * 0.3)

    def update(self, dt: float):
        self.input_handle()
        self.rect.center = self.pos
        self.collision_rect.center = self.pos

    def render(self, renderer, offset=(0, 0)):
        # Flip the image before rendering if facing left
        if not self.facing_right:
            # Only flip if the current image isn't already flipped
            # We'll use a flag to avoid re-flipping every frame
            self.image = pg.transform.flip(self.original_image, True, False)
        else:
            self.image = self.original_image.copy()

        x = self.rect.x - offset[0]
        y = self.rect.y - offset[1]
        renderer.blit(self.image, (x, y))

    def input_handle(self):
        keys = pg.key.get_pressed()
        dx = dy = 0
        if keys[pg.K_w] or keys[pg.K_UP]:
            dy = -self.speed
        if keys[pg.K_s] or keys[pg.K_DOWN]:
            dy = self.speed
        if keys[pg.K_a] or keys[pg.K_LEFT]:
            dx = -self.speed
            self.facing_right = False
        if keys[pg.K_d] or keys[pg.K_RIGHT]:
            dx = self.speed
            self.facing_right = True

        self.pos[0] += dx
        self.pos[1] += dy
        self.pos[0] = max(0, min(self.pos[0], self.engine.width))
        self.pos[1] = max(0, min(self.pos[1], self.engine.height))