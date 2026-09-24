import os
import json
import time
import random
import argparse
import sys
import gc

import pygame

from lunaengine.core import LunaEngine, Scene
from lunaengine.backend import OpenGLRenderer
from lunaengine.core.audio import AudioManager
from lunaengine.graphics import Animation, SpriteSheet, CameraMode
from lunaengine.ui import *

parser = argparse.ArgumentParser()
parser.add_argument('--debug', action='store_true', help='Enable debug mode')
parser.add_argument('--fullscreen', action='store_true', help='Run in fullscreen')
parser.add_argument('--noaudio', action='store_true', help='Disable audio')

username_arg = None
for i, arg in enumerate(sys.argv):
    if arg.startswith('--username:'):
        username_arg = arg.split(':', 1)[1]
        sys.argv.pop(i)
        break
args = parser.parse_args()

assets_path = os.path.dirname(__file__) + '/assets'


class Data:
    asteroids: list
    health_bar: list
    spaceship_explosion = None
    spaceship = None
    leaderboard: dict
    started: float
    background: pygame.SurfaceType
    current_username: str = ""
    bullet_sprite: pygame.SurfaceType|None = None
    size_fix: pygame.Vector2
    asteroid_pool: list = []
    score_text_surface: pygame.SurfaceType = None


data = Data()


class Bullet:
    __slots__ = ('position', 'speed', 'rect')
    def __init__(self, position):
        self.position = pygame.math.Vector2(position)
        self.speed = 750 * data.size_fix.x
        self.rect = pygame.Rect(position[0], position[1], 8, 4)

    def update(self, dt):
        self.position.x += self.speed * dt
        self.rect.x = self.position.x
        self.rect.y = self.position.y

    def render(self, renderer: OpenGLRenderer):
        renderer.blit(data.bullet_sprite, self.position, use_cache=True)


class MainMenu(Scene):
    def on_enter(self, previous_scene=None):
        self.engine.set_global_theme(ThemeType.DEEP_SPACE)
        self.update_leaderboard()
        return super().on_enter(previous_scene)

    def on_exit(self, next_scene=None):
        return super().on_exit(next_scene)

    def __init__(self, engine):
        super().__init__(engine)
        self.create_ui()

    def create_ui(self):
        self.add_ui_element(
            TextLabel(320 * data.size_fix.x, 100 * data.size_fix.y, "Naves", 102,
                      (255, 255, 255), font_name=os.path.abspath(f"{assets_path}/SpaceMono.ttf"),
                      pivot=(0.5, 0))
        )

        self.play_button = Button(320 * data.size_fix.x, 300 * data.size_fix.y,
                                  300 * data.size_fix.x, 90 * data.size_fix.y,
                                  "PLAY", 40, None, (0.5, 0.5))
        self.play_button.set_on_click(self.play_clicked)
        self.add_ui_element(self.play_button)

        self.exit_button = Button(320 * data.size_fix.x, 400 * data.size_fix.y,
                                  285 * data.size_fix.x, 75 * data.size_fix.y,
                                  "EXIT", 36, None, (0.5, 0.5))
        self.exit_button.set_on_click(self.exit_clicked)
        self.add_ui_element(self.exit_button)

        self.add_ui_element(
            TextLabel(320 * data.size_fix.x, 500 * data.size_fix.y,
                      "Leaderboard name here:", 24, (255, 255, 255),
                      font_name=None, pivot=(0.5, 0))
        )
        self.username_textbox = TextBox(320 * data.size_fix.x, 532 * data.size_fix.y,
                                        300 * data.size_fix.x, 35 * data.size_fix.y,
                                        "", 24, None, (0.5, 0))
        self.add_ui_element(self.username_textbox)
        self.add_ui_element(
            TextLabel(320 * data.size_fix.x, 570 * data.size_fix.y,
                      "* Only letters and numbers allowed",
                      16, (190, 60, 90), None, pivot=(0.5, 0))
        )

        self.add_ui_element(
            TextLabel(int(640 * data.size_fix.x), 15 * data.size_fix.y,
                      "LEADERBOARD", 30, (255, 255, 255), font_name=None, pivot=(0, 0))
        )
        self.leaderboard_scroll = ScrollingFrame(
            self.engine.width - int(20 * data.size_fix.x), int(40 * data.size_fix.y),
            int(360 * data.size_fix.x), int(500 * data.size_fix.x),
            int(360 * data.size_fix.x), int(900 * data.size_fix.y), (1.0, 0)
        )
        self.add_ui_element(self.leaderboard_scroll)

    def update_leaderboard(self):
        self.leaderboard_scroll.children.clear()
        for index, user in enumerate(
                sorted(data.leaderboard['scores'], key=lambda x: x['score'], reverse=True)):
            self.leaderboard_scroll.add_child(
                TextLabel((25 * data.size_fix.x), ((index * 50) + 15) * data.size_fix.y,
                          f"{index + 1} - {user['name']} - {user['score']}", 48,
                          (255, 255, 255), font_name=None, pivot=(0, 0))
            )

    def play_clicked(self):
        if len(self.username_textbox.text) > 1:
            data.current_username = self.username_textbox.text
            self.engine.set_scene("Game")

    def exit_clicked(self):
        self.engine.shutdown()
        exit(0)

    def update(self, dt):
        return super().update(dt)

    def render(self, renderer):
        pass


class Player:
    max_health: int = 5
    _health: int = 5
    score: int = 0
    name: str
    state: str = 'moving'
    position: pygame.math.Vector2 = pygame.math.Vector2(0, 0)

    _moving_bboxes = None
    _explosion_bboxes = None

    last_shoot = None
    shoot_cooldown: float = 0.75
    rect: pygame.rect.RectType
    explosion_start_time: float = 0
    invulnerable: bool = False
    invulnerable_start: float = 0
    invulnerable_duration: float = 1.0
    visible: bool = True
    flash_timer: float = 0

    @property
    def health(self):
        return self._health

    @health.setter
    def health(self, value):
        if value < self._health and not self.invulnerable and self.state != 'explosion':
            self._health = value
            self.invulnerable = True
            self.invulnerable_start = time.time()
        elif value >= self._health:
            self._health = value

    def __init__(self, name):
        self.name = name
        self.animations = {
            'moving': data.spaceship,
            'explosion': data.spaceship_explosion
        }
        self.position.xy = (120, 336)
        self.rect = self.animations[self.state].frames[0].get_bounding_rect()
        self.rect.center = self.position.xy

        self._moving_bboxes = [f.get_bounding_rect() for f in data.spaceship.frames]
        self._explosion_bboxes = [f.get_bounding_rect() for f in data.spaceship_explosion.frames]

    def update(self, dt):
        if self.state == 'explosion' and time.time() - self.explosion_start_time > 1.5:
            return

        self.rect.center = self.position.xy

        if self.invulnerable:
            current_time = time.time()
            if current_time - self.invulnerable_start >= self.invulnerable_duration:
                self.invulnerable = False
                self.visible = True
            else:
                self.flash_timer += dt
                if self.flash_timer >= 0.1:
                    self.visible = not self.visible
                    self.flash_timer = 0

    def render(self, renderer):
        if not self.visible and self.invulnerable:
            return

        anim = self.animations[self.state]
        frame_index = anim.current_frame_index
        if self.state == 'moving':
            frame_rect = self._moving_bboxes[frame_index]
        else:
            frame_rect = self._explosion_bboxes[frame_index]
        current_frame = anim.frames[frame_index]
        render_position = (self.rect.centerx - frame_rect.width / 2,
                           self.rect.top + 5 - frame_rect.height / 2)
        renderer.blit(current_frame, render_position, use_cache=True)

    def explode(self):
        self.state = 'explosion'
        self.explosion_start_time = time.time()
        self.animations['explosion'].reset()

    def get_bullet_spawn_position(self) -> tuple:
        return self.rect.right, self.rect.centery


class Game(Scene):
    player: Player
    max_asteroids: int = 5
    asteroids: list = []
    asteroid_speed: float = 0.9
    game_over: bool = False
    bullets: list = []

    last_score: float
    _gc_enabled: bool = False

    def __init__(self, engine):
        super().__init__(engine)

        if not args.noaudio:
            self.audio_manager.load_sound("explosion", f"{assets_path}/explosion.wav")
            self.audio_manager.load_sound("shoot", f"{assets_path}/laserShoot.wav")
            self.audio_manager.load_sound("bgm", f"{assets_path}/music.mp3", 'music')

        self.parallax_x = 0
        self.parallax_sample = self.create_parallax_layer(0.94)
        self.setup_camera()

        self.overlay = pygame.Surface((self.engine.width, self.engine.height), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 180))
        self.overlay = self.overlay.convert_alpha()

        tile_w = self.parallax_sample.get_width()
        tile_h = self.parallax_sample.get_height()
        self.parallax_tile = pygame.Surface((tile_w * 2, tile_h))
        self.parallax_tile.blit(self.parallax_sample, (0, 0))
        self.parallax_tile.blit(self.parallax_sample, (tile_w, 0))
        self.parallax_tile = self.parallax_tile.convert()

        # Start with a slight offset to avoid blank initial frame
        self.parallax_x = -tile_w // 2

        # Score display as a pre-rendered surface (no UI element)
        self.score_surface = None
        self.last_score_display = -1
        self.font_path = f"{assets_path}/SpaceMono.ttf"

    def setup_camera(self):
        self.camera.position = pygame.math.Vector2(self.engine.width / 2, self.engine.height / 2)
        self.camera.mode = CameraMode.FIXED

    def create_parallax_layer(self, brightness_factor=1.0):
        layer = data.background.copy()
        if brightness_factor != 1.0:
            overlay = pygame.Surface(layer.get_size(), pygame.SRCALPHA)
            brightness_value = int(255 * brightness_factor)
            overlay.fill((brightness_value, brightness_value, brightness_value, 100))
            layer.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return layer.convert()

    def render_parallax(self, renderer):
        renderer.blit(self.parallax_tile, (self.parallax_x % self.parallax_tile.get_width(), 0), use_cache=True)

    def on_enter(self, previous_scene=None):
        # Disable garbage collection to prevent periodic pauses
        self._gc_enabled = gc.isenabled()
        gc.disable()

        self.player = Player(data.current_username)
        self.clear_ui_elements()

        if not args.noaudio:
            self.audio_manager.play_music("bgm", loop=True, volume=0.7, fade_in=1.0)

        self.camera.set_target(self.player.rect)

        self.create_all_asteroids()
        self.last_score = time.time()
        self.last_score_display = -1  # force update on first frame

        return super().on_enter(previous_scene)

    def on_exit(self, next_scene=None):
        if self._gc_enabled:
            gc.enable()

        self.player = None
        self.clear_ui_elements()
        self.asteroids.clear()
        self.bullets.clear()
        self.game_over = False
        return super().on_exit(next_scene)

    def input_handler(self, dt):
        if self.game_over:
            return

        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.player.position.y -= (400 * data.size_fix.y) * dt
            if self.player.position.y < 72:
                self.player.position.y = 72
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.player.position.y += (400 * data.size_fix.y) * dt
            if self.player.position.y > self.engine.height * 0.8:
                self.player.position.y = self.engine.height * 0.8

        if (keys[pygame.K_SPACE] or self.engine.input_state.mouse_buttons_pressed.left) and \
                time.time() - self.player.last_shoot > self.player.shoot_cooldown:
            self.player.last_shoot = time.time()
            self.bullets.append(Bullet(self.player.get_bullet_spawn_position()))
            if not args.noaudio:
                self.audio_manager.play("shoot", volume=1.0)

    def create_asteroid(self):
        sprite, bbox = random.choice(data.asteroid_pool)
        y = random.randint(80, self.engine.height - (80 + bbox.height))
        asteroid_rect = pygame.Rect(self.engine.width + 20 + bbox.x,
                                    y + bbox.y,
                                    bbox.width, bbox.height)
        self.asteroids.append((asteroid_rect, sprite, bbox))

    def create_all_asteroids(self):
        for _ in range(self.max_asteroids):
            self.create_asteroid()

    def update_bullets(self, dt):
        for bullet in self.bullets[:]:
            bullet.update(dt)
            if bullet.position.x > self.engine.width:
                self.bullets.remove(bullet)
                continue
            for item in self.asteroids[:]:
                asteroid_rect, sprite, _ = item
                if bullet.rect.colliderect(asteroid_rect):
                    self.asteroids.remove(item)
                    self.bullets.remove(bullet)
                    self.create_asteroid()
                    self.change_score(50)
                    if not args.noaudio:
                        self.audio_manager.play("explosion", volume=1.0)
                    break

    def update_asteroids(self, dt):
        if self.game_over: return
        player_rect = self.player.rect
        asteroids = self.asteroids
        for item in asteroids[:]:
            asteroid_rect, sprite, _ = item
            asteroid_rect.x -= ((293 * self.asteroid_speed) * data.size_fix.x) * dt
            if asteroid_rect.colliderect(player_rect) and not self.player.invulnerable and \
                    self.player.state != 'explosion':
                self.player.health -= 1
                if not args.noaudio:
                    self.audio_manager.play("explosion", volume=1.0)
                self.asteroids.remove(item)
                self.create_asteroid()
                if self.player.health <= 0 and not self.game_over:
                    self.game_over = True
                    self.player.explode()
                    if not args.noaudio:
                        self.audio_manager.stop_all()
                        self.audio_manager.play("explosion", volume=1.0)
                break
            if asteroid_rect.right < 0:
                self.asteroids.remove(item)
                self.create_asteroid()
        if len(asteroids) < self.max_asteroids:
            self.create_asteroid()

    def render_asteroids(self, renderer):
        blit = renderer.blit
        for asteroid_rect, sprite, bbox in self.asteroids:
            blit(sprite, (asteroid_rect.x - bbox.x, asteroid_rect.y - bbox.y), use_cache=True)

    def render_bullets(self, renderer):
        for bullet in self.bullets:
            bullet.render(renderer)

    def render_aim_line(self, renderer):
        start_pos = (self.player.rect.centerx, self.player.rect.centery)
        for i in range(5):
            segment_length = 20 * data.size_fix.x
            gap_length = 10 * data.size_fix.x
            segment_start = start_pos[0] + i * (segment_length + gap_length)
            segment_end = segment_start + segment_length
            if segment_start < self.engine.width:
                renderer.draw_line(segment_start, start_pos[1],
                                   min(segment_end, self.engine.width),
                                   start_pos[1], (0, 190, 255, 100), 2)

    def render_debug(self, renderer):
        pass

    def update(self, dt):
        if self.player.last_shoot is None:
            self.player.last_shoot = time.time()

        self.input_handler(dt)
        self.player.update(dt)
        self.update_bullets(dt)
        self.update_asteroids(dt)

        self.parallax_x -= (202 * self.asteroid_speed) * data.size_fix.x * dt

        if time.time() - self.last_score > 1 and not self.game_over:
            self.change_score(10)
            self.last_score = time.time()

        if self.game_over and self.player.state == 'explosion' and \
                time.time() - self.player.explosion_start_time > 1.5:
            self.save_score()
            self.engine.set_scene("GameOver")

        super().update(dt)

    def change_score(self, value: int):
        if self.player.health > 0:
            self.player.score += value
            self.asteroid_speed = 0.9 + (self.player.score / 1000)
            self.max_asteroids = 5 + int(self.player.score / 2000)
            self.last_score_display = -1  # force re-render

    def save_score(self):
        data.leaderboard['scores'].append({
            'name': data.current_username,
            'score': int(self.player.score)
        })
        with open(f"{os.path.dirname(__file__)}/leaderboard.json", "w") as f:
            json.dump(data.leaderboard, f)

    def render(self, renderer):
        frame_start = time.perf_counter()

        renderer.fill_screen((30, 15, 50))
        self.render_parallax(renderer)

        t0 = time.perf_counter()
        self.render_asteroids(renderer)
        t1 = time.perf_counter()
        self.render_bullets(renderer)
        t2 = time.perf_counter()
        self.render_aim_line(renderer)
        t3 = time.perf_counter()
        self.player.render(renderer)
        t4 = time.perf_counter()

        # Score rendering – only recreate if score changed
        if self.last_score_display != self.player.score:
            font = FontManager.get_font(self.font_path, 24)
            text = f"Score: {int(self.player.score)}"
            self.score_surface = font.render(text, True, (255, 255, 255))
            self.score_surface = self.score_surface.convert_alpha()
            self.last_score_display = self.player.score
        if self.score_surface:
            renderer.blit(self.score_surface, (self.engine.width - self.score_surface.get_width() - 10, 15), use_cache=True)

        t5 = time.perf_counter()

        hp_index = max(0, self.player.health)
        renderer.blit(data.health_bar[hp_index], (10 * data.size_fix.x, 10 * data.size_fix.y), use_cache=True)
        t6 = time.perf_counter()

        if args.debug:
            self.render_debug(renderer)

        if self.game_over:
            renderer.blit(self.overlay, (0, 0), use_cache=True)
            renderer.draw_text('GAME OVER', self.engine.width//2, self.engine.height//2, (255, 100, 100), FontManager.get_font(None, 72), pivot=(0.5, 0.5))
            renderer.draw_text(f'Final Score: {int(self.player.score)}', self.engine.width//2, self.engine.height//2 + (20 * data.size_fix.y), (255, 100, 100), FontManager.get_font(None, 48), pivot=(0.5, 0.5))

        frame_end = time.perf_counter()
        total_ms = (frame_end - frame_start) * 1000

        if total_ms > 20:
            print(f"🔴 SLOW FRAME: {total_ms:.1f}ms")
            print(f"  Asteroids: {(t1-t0)*1000:.2f}ms ({len(self.asteroids)})")
            print(f"  Bullets:   {(t2-t1)*1000:.2f}ms ({len(self.bullets)})")
            print(f"  Aim line:  {(t3-t2)*1000:.2f}ms")
            print(f"  Player:    {(t4-t3)*1000:.2f}ms")
            print(f"  Score:     {(t5-t4)*1000:.2f}ms")
            print(f"  Health:    {(t6-t5)*1000:.2f}ms")


class GameOver(Scene):
    def on_enter(self, previous_scene=None):
        self.engine.set_global_theme(ThemeType.DEEP_SPACE.value)
        self.create_ui()
        return super().on_enter(previous_scene)

    def create_ui(self):
        self.add_ui_element(
            TextLabel(320 * data.size_fix.x, 100 * data.size_fix.y,
                      "GAME OVER", 74, (255, 50, 50), font_name=None, pivot=(0.5, 0))
        )

        self.menu_button = Button(320 * data.size_fix.x, 300 * data.size_fix.y,
                                  300 * data.size_fix.x, 90 * data.size_fix.y,
                                  "MAIN MENU", 40, None, (0.5, 0.5))
        self.menu_button.set_on_click(self.menu_clicked)
        self.add_ui_element(self.menu_button)

        self.leaderboard_scroll = ScrollingFrame(
            self.engine.width - int(40 * data.size_fix.x), int(40 * data.size_fix.y),
            int(360 * data.size_fix.x), int(640 * data.size_fix.y),
            int(360 * data.size_fix.x), int(900 * data.size_fix.y), (1, 0)
        )
        self.update_leaderboard()
        self.add_ui_element(self.leaderboard_scroll)

    def update_leaderboard(self):
        self.leaderboard_scroll.children.clear()
        for index, user in enumerate(
                sorted(data.leaderboard['scores'], key=lambda x: x['score'], reverse=True)):
            self.leaderboard_scroll.add_child(
                TextLabel(25 * data.size_fix.x, ((index * 50) + 15) * data.size_fix.y,
                          f"{index + 1} - {user['name']} - {user['score']}", 48,
                          (255, 255, 255), font_name=None, pivot=(0, 0))
            )

    def menu_clicked(self):
        self.engine.set_scene("MainMenu")

    def update(self, dt):
        return super().update(dt)

    def render(self, renderer):
        pass


def main():
    fullscreen = args.fullscreen
    data.started = time.time()

    engine = LunaEngine("Naves", width=1024, height=768, fullscreen=fullscreen, debug=args.debug)
    pygame.display.set_icon(pygame.image.load(f"{assets_path}/icon.png"))
    engine.initialize()

    display = pygame.display.get_surface()
    data.size_fix = pygame.Vector2(engine.width / 1024, engine.height / 768)

    # Load assets
    base_asteroids = SpriteSheet(f"{assets_path}/Asteroids.png").get_sprites_at_regions([
        (0, 0, 32, 32), (32, 0, 32, 32), (64, 0, 32, 32), (96, 0, 32, 32), (128, 0, 32, 32),
        (0, 32, 32, 32), (32, 32, 32, 32), (64, 32, 32, 32), (96, 32, 32, 32), (128, 32, 32, 32),
        (0, 64, 32, 32), (32, 64, 32, 32), (64, 64, 32, 32), (96, 64, 32, 32), (128, 64, 32, 32),
    ])

    # Pre‑generate asteroid pool
    asteroid_pool = []
    scale_factor = 2.5 * data.size_fix.x
    for base in base_asteroids:
        size = base.get_size()
        scaled = pygame.transform.scale(base,
                                        (int(size[0] * scale_factor),
                                         int(size[1] * scale_factor)))
        scaled = scaled.convert_alpha(display)
        bbox = scaled.get_bounding_rect()
        asteroid_pool.append((scaled, bbox))
    data.asteroid_pool = asteroid_pool

    # Health bar
    health_bar_orig = SpriteSheet(f"{assets_path}/Health-bar.png").get_sprites_at_regions([
        pygame.Rect(640, 0, 128, 32), pygame.Rect(512, 0, 128, 32),
        pygame.Rect(384, 0, 128, 32), pygame.Rect(256, 0, 128, 32),
        pygame.Rect(128, 0, 128, 32), pygame.Rect(0, 0, 128, 32)
    ])

    data.health_bar = []
    for img in health_bar_orig:
        scaled = pygame.transform.scale(img, (int(192 * data.size_fix.x), int(48 * data.size_fix.y)))
        data.health_bar.append(scaled.convert_alpha(display))

    # Spaceship animations
    data.spaceship = Animation(
        spritesheet_file=f'{assets_path}/Spaceship.png', size=(32, 32),
        start_pos=(0, 0), frame_count=5,
        scale=(2.5 * data.size_fix.x, 2.5 * data.size_fix.x),
        duration=0.75, loop=True
    )
    data.spaceship_explosion = Animation(
        spritesheet_file=f'{assets_path}/Spaceship-explosion.png', size=(32, 32),
        start_pos=(0, 0), frame_count=12,
        scale=(2.5 * data.size_fix.x, 2.5 * data.size_fix.x),
        duration=0.7, loop=False
    )

    data.background = pygame.transform.scale(
        pygame.image.load(os.path.abspath(f"{assets_path}/background.jpg")).convert(),
        (engine.width, engine.height)
    )

    bullet_surface = pygame.Surface((8, 4), pygame.SRCALPHA)
    pygame.draw.ellipse(bullet_surface, (255, 255, 0), (0, 0, 8, 4))
    data.bullet_sprite = bullet_surface.convert_alpha(display)

    if not os.path.exists(f"{os.path.dirname(__file__)}/leaderboard.json"):
        with open(f"{os.path.dirname(__file__)}/leaderboard.json", "w") as f:
            f.write('{"scores": []}')
    with open(f"{os.path.dirname(__file__)}/leaderboard.json") as f:
        data.leaderboard = json.load(f)

    engine.add_scene("MainMenu", MainMenu)
    engine.add_scene("Game", Game)
    engine.add_scene("GameOver", GameOver)
    engine.set_scene("MainMenu")

    engine.run()


if __name__ == "__main__":
    main()