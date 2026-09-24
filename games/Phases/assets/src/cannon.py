# cannon.py
from lunaengine.core import LunaEngine
import pygame as pg
import math

class CannonBullet:
    def __init__(self, engine, pos, direction, scene, speed=250):
        self.engine = engine
        self.scene = scene
        self.image = pg.Surface((int(12*engine.ratio.x), int(12*engine.ratio.y)))
        self.image.fill((200, 200, 30))
        self.rect = self.image.get_rect(center=pos)
        self.speed = speed
        rad = math.radians(direction - 90)
        self.vx = speed * math.cos(rad)
        self.vy = speed * math.sin(rad)
        
        
        self.scene.bullets.append(self)

    def update(self, dt:float):
        self.rect.x += self.vx * dt
        self.rect.y += self.vy * dt
        
    def render(self, renderer, offset=(0, 0)):
        x = self.rect.x - offset[0]
        y = self.rect.y - offset[1]
        renderer.blit(self.image, (x, y))
        

class Cannon:
    def __init__(self, engine, x, y, direction, sprite=None, tile_size=32):
        self.engine = engine
        self.pos = (x, y)
        self.direction = direction
        self.interval = 90
        self.timer = 0

        if sprite:
            self.base_image = sprite
        else:
            self.base_image = pg.Surface((tile_size, tile_size))
            self.base_image.fill((0, 0, 255))

        size = int(tile_size * 0.8)
        self.image = pg.transform.scale(self.base_image, (size, size))
        self.rect = self.image.get_rect(center=self.pos)

    def update(self, dt:float):
        self.timer += 1
        if self.timer >= self.interval:
            self.timer = 0
            bullet = CannonBullet(self.engine, self.pos, self.direction, self.engine.current_scene)

    def render(self, renderer, offset=(0, 0)):
        if self.direction in [90, -90]:
            rotation = self.direction + 90
        elif self.direction in [0, 180, -180]:
            rotation = self.direction - 90
        rotated = pg.transform.rotate(self.image, rotation)
        new_rect = rotated.get_rect(center=self.rect.center)
        x = new_rect.x - offset[0]
        y = new_rect.y - offset[1]
        renderer.blit(rotated, (x, y))