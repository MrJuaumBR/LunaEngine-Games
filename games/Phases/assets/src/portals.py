# portals.py
from lunaengine.core import LunaEngine
import pygame as pg
from typing import Tuple

class Portal:
    def __init__(self, engine, pos: Tuple[int,int], target: Tuple[int,int],
                 entrance_sprite=None, exit_sprite=None, tile_size=32):
        self.engine = engine
        self.pos = pos
        self.target = target
        self.tile_size = tile_size

        # Use provided sprites or fallback
        self.image = pg.transform.scale(entrance_sprite, (int(tile_size*0.8*engine.ratio.x), int(tile_size*0.8*engine.ratio.y)))
        self.rect = self.image.get_rect(center=pos)

        # Store exit sprite for later (if needed)
        self.exit_sprite = pg.transform.scale(exit_sprite, (int(tile_size*0.8*engine.ratio.x), int(tile_size*0.8*engine.ratio.y)))
        self.exit_rect = self.exit_sprite.get_rect(center=target)

    def render(self, renderer, offset=(0,0)):
        x = self.rect.x - offset[0]
        y = self.rect.y - offset[1]
        renderer.blit(self.image, (x, y))
        
        tx = self.exit_rect.x - offset[0]
        ty = self.exit_rect.y - offset[1]
        if self.exit_sprite:
            renderer.blit(self.exit_sprite, (tx, ty))

    def detect_player_collision(self, player_rect):
        return self.rect.colliderect(player_rect)