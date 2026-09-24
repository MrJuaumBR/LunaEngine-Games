# main.py – TankSiege
# Full game with smart AI, waves, upgrades, leaderboard, life regen, and compact HUD.

import sys
import os
import random
import json
import math
import time
from datetime import datetime
from pathlib import Path
from argparse import ArgumentParser

import pygame

from lunaengine.core import LunaEngine, Scene
from lunaengine.ui import *
from lunaengine.graphics import CameraMode
from lunaengine.backend import OpenGLRenderer

# ------------------------- Argument Parsing -------------------------
argparser = ArgumentParser()
argparser.add_argument('--debug', action='store_true', default=False)
argparser.add_argument('--fullscreen', action='store_true', default=False)
argparser.add_argument('--username', type=str, default='Player', help='Username for leaderboard')

# ------------------------- Leaderboard Manager -------------------------
class LeaderboardManager:
    def __init__(self, file_name='leaderboard.json'):
        self.file_path = Path(os.path.abspath(os.path.dirname(__file__))) / file_name
        self.data = self._load()
        self.current_username = "Player"

    def _load(self):
        if self.file_path.exists():
            with open(self.file_path, 'r') as f:
                return json.load(f)
        return {"scores": []}

    def save(self):
        with open(self.file_path, 'w') as f:
            json.dump(self.data, f, indent=2)

    def add_score(self, name, wave, score):
        self.data["scores"].append({
            "name": name,
            "wave": wave,
            "score": score,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        self.data["scores"].sort(key=lambda x: x["score"], reverse=True)
        self.data["scores"] = self.data["scores"][:10]
        self.save()

    def get_top(self, count=10):
        return self.data["scores"][:count]

LDM = LeaderboardManager()

# ------------------------- Bullet -------------------------
class Bullet:
    def __init__(self, x, y, angle, speed, damage, owner, color=(255, 255, 0)):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.damage = damage
        self.owner = owner
        self.radius = 4
        self.rect = pygame.Rect(x - self.radius, y - self.radius, self.radius*2, self.radius*2)
        self.color = color
        self.alive = True

    def update(self, dt):
        self.x += self.speed * math.cos(self.angle) * dt
        self.y += self.speed * math.sin(self.angle) * dt
        self.rect.center = (self.x, self.y)
        if self.x < -50 or self.x > 1500 or self.y < -50 or self.y > 1500:
            self.alive = False

    def render(self, renderer, camera):
        pos = camera.world_to_screen((self.x, self.y))
        renderer.draw_circle(pos.x, pos.y, self.radius, self.color)

# ------------------------- Enemy Tank (AI) -------------------------
class EnemyTank:
    def __init__(self, x, y, personality='chaser'):
        self.x = x
        self.y = y
        self.radius = 20
        self.rect = pygame.Rect(x - self.radius, y - self.radius, self.radius*2, self.radius*2)
        self.speed = 100
        self.health = 30
        self.max_health = 30
        self.damage = 10
        self.shoot_cooldown = 1.5
        self.shoot_timer = random.uniform(0, 1.5)
        self.personality = personality
        self.angle = 0
        self.alive = True
        self.evade_cooldown = 0
        self.dodge_angle = 0
        self.speed_temp = self.speed

        if personality == 'sniper':
            self.speed = 80
            self.shoot_cooldown = 2.0
            self.damage = 20
            self.radius = 18
            self.health = 20
            self.max_health = 20
        elif personality == 'flanker':
            self.speed = 130
            self.shoot_cooldown = 1.2
            self.damage = 12
            self.radius = 18
            self.health = 25
            self.max_health = 25
        elif personality == 'tank':
            self.speed = 70
            self.health = 60
            self.max_health = 60
            self.shoot_cooldown = 1.8
            self.damage = 15
            self.radius = 25

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.alive = False

    def update(self, dt, player, all_bullets):
        if not self.alive:
            return

        # ---- Evasion (less perfect) ----
        if self.evade_cooldown > 0:
            self.evade_cooldown -= dt
        else:
            threat = None
            for b in all_bullets:
                if b.owner == 'player':
                    dx = self.x - b.x
                    dy = self.y - b.y
                    dist = math.hypot(dx, dy)
                    if dist < 150:
                        future_x = b.x + b.speed * math.cos(b.angle) * 0.15
                        future_y = b.y + b.speed * math.sin(b.angle) * 0.15
                        if math.hypot(future_x - self.x, future_y - self.y) < self.radius + 15:
                            bullet_to_enemy_angle = math.atan2(dy, dx)
                            angle_diff = bullet_to_enemy_angle - b.angle
                            while angle_diff > math.pi:
                                angle_diff -= 2*math.pi
                            while angle_diff < -math.pi:
                                angle_diff += 2*math.pi
                            if abs(angle_diff) < 1.0:
                                threat = b
                                break
            if threat:
                bullet_angle = threat.angle
                offset = random.uniform(-0.3, 0.3)
                side = 1 if random.random() > 0.5 else -1
                self.dodge_angle = bullet_angle + math.pi/2 * side + offset
                self.evade_cooldown = 1.5
                self.speed_temp = self.speed * 1.2
            else:
                self.speed_temp = self.speed

        # ---- Movement ----
        dx = player.x - self.x
        dy = player.y - self.y
        dist_to_player = math.hypot(dx, dy)

        if self.evade_cooldown > 0:
            move_angle = self.dodge_angle
        else:
            if self.personality == 'sniper':
                if dist_to_player < 300:
                    move_angle = math.atan2(-dy, -dx)
                elif dist_to_player > 400:
                    move_angle = math.atan2(dy, dx)
                else:
                    move_angle = math.atan2(dy, dx)
            elif self.personality == 'flanker':
                player_angle = player.angle
                angle_to_player = math.atan2(dy, dx)
                angle_diff = angle_to_player - player_angle
                while angle_diff > math.pi:
                    angle_diff -= 2*math.pi
                while angle_diff < -math.pi:
                    angle_diff += 2*math.pi
                if abs(angle_diff) < 0.5:
                    move_angle = angle_to_player + math.pi/2 * (1 if random.random() > 0.5 else -1)
                else:
                    move_angle = angle_to_player
            else:
                move_angle = math.atan2(dy, dx)

        speed_actual = self.speed_temp if hasattr(self, 'speed_temp') else self.speed
        self.x += speed_actual * math.cos(move_angle) * dt
        self.y += speed_actual * math.sin(move_angle) * dt
        self.rect.center = (self.x, self.y)
        self.angle = move_angle

        # ---- Shooting ----
        self.shoot_timer -= dt
        if self.shoot_timer <= 0:
            predict_time = 0.4
            future_x = player.x + player.vx * predict_time
            future_y = player.y + player.vy * predict_time
            shoot_angle = math.atan2(future_y - self.y, future_x - self.x)
            shoot_angle += random.uniform(-0.25, 0.25)
            bullet = Bullet(self.x, self.y, shoot_angle, 300, self.damage, 'enemy', color=(255, 100, 100))
            all_bullets.append(bullet)
            self.shoot_timer = self.shoot_cooldown

    def render(self, renderer, camera):
        if not self.alive:
            return
        pos = camera.world_to_screen((self.x, self.y))
        color = (200, 50, 50) if self.personality == 'chaser' else \
                (50, 200, 50) if self.personality == 'sniper' else \
                (50, 50, 200) if self.personality == 'flanker' else \
                (150, 150, 50)
        renderer.draw_circle(pos.x, pos.y, self.radius, color)
        end_x = pos.x + self.radius * math.cos(self.angle)
        end_y = pos.y + self.radius * math.sin(self.angle)
        renderer.draw_line(pos.x, pos.y, end_x, end_y, (200, 200, 200), 3)
        health_width = 30
        health_height = 4
        health_ratio = self.health / self.max_health
        bar_x = pos.x - health_width/2
        bar_y = pos.y - self.radius - 8
        renderer.draw_rect(bar_x, bar_y, health_width, health_height, (50, 50, 50))
        renderer.draw_rect(bar_x, bar_y, health_width * health_ratio, health_height,
                           (0, 255, 0) if health_ratio > 0.3 else (255, 0, 0))

# ------------------------- Player Tank -------------------------
class PlayerTank:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 20
        self.rect = pygame.Rect(x - self.radius, y - self.radius, self.radius*2, self.radius*2)
        self.speed = 200
        self.max_health = 100
        self.health = 100
        self.damage = 15
        self.fire_rate = 1.0
        self.bullet_speed = 400          # new
        self.shoot_timer = 0
        self.angle = 0
        self.vx = 0
        self.vy = 0
        self.alive = True
        self.can_take_damage = True

        # Regen stats
        self.regen_time = 8.0            # seconds without damage before regen starts
        self.regen_rate = 5.0            # HP per second
        self.last_damage_time = 0.0

        # Upgrade stats
        self.level = 1
        self.xp = 0
        self.xp_to_next = 50

    def take_damage(self, amount):
        if not self.can_take_damage:
            return
        self.health -= amount
        self.last_damage_time = time.time()   # reset regen timer
        if self.health <= 0:
            self.alive = False

    def update(self, dt, keys, mouse_pos, all_bullets, camera):
        if not self.alive:
            return

        # ---- Movement ----
        dx = 0
        dy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = 1

        if dx != 0 or dy != 0:
            length = math.hypot(dx, dy)
            dx /= length
            dy /= length
        self.vx = dx * self.speed
        self.vy = dy * self.speed
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rect.center = (self.x, self.y)

        # ---- Aim ----
        mouse_world = camera.screen_to_world(mouse_pos)
        self.angle = math.atan2(mouse_world[1] - self.y, mouse_world[0] - self.x)

        # ---- Shooting ----
        self.shoot_timer -= dt
        if pygame.mouse.get_pressed()[0] and self.shoot_timer <= 0:
            bullet = Bullet(self.x, self.y, self.angle, self.bullet_speed, self.damage, 'player', color=(100, 255, 100))
            all_bullets.append(bullet)
            self.shoot_timer = self.fire_rate

        # ---- Life Regeneration ----
        if self.health < self.max_health:
            time_since_damage = time.time() - self.last_damage_time
            if time_since_damage >= self.regen_time:
                # Heal over time
                heal_amount = self.regen_rate * dt
                self.health = min(self.health + heal_amount, self.max_health)

    def render(self, renderer, camera):
        if not self.alive:
            return
        pos = camera.world_to_screen((self.x, self.y))
        renderer.draw_circle(pos.x, pos.y, self.radius, (100, 200, 255))
        end_x = pos.x + self.radius * math.cos(self.angle)
        end_y = pos.y + self.radius * math.sin(self.angle)
        renderer.draw_line(pos.x, pos.y, end_x, end_y, (200, 200, 200), 4)
        health_width = 40
        health_height = 6
        health_ratio = self.health / self.max_health
        bar_x = pos.x - health_width/2
        bar_y = pos.y - self.radius - 12
        renderer.draw_rect(bar_x, bar_y, health_width, health_height, (50, 50, 50))
        renderer.draw_rect(bar_x, bar_y, health_width * health_ratio, health_height,
                           (0, 255, 0) if health_ratio > 0.3 else (255, 0, 0))

# ------------------------- Game Scene -------------------------
class GameScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.player = None
        self.enemies = []
        self.bullets = []
        self.wave = 0
        self.enemies_per_wave = 3
        self.wave_timer = 0
        self.wave_delay = 3.0
        self.spawn_timer = 0
        self.enemies_spawned = 0
        self.game_over = False
        self.score = 0
        self.start_time = 0
        self.boss_active = False
        self.wave_in_progress = False

        # ---- Camera ----
        self.camera.mode = CameraMode.FOLLOW

        # ---- Top‑left UI (Wave & Score) ----
        self.wave_label = TextLabel(10, 10, "Wave: 0", 28, font_name='russoone')
        self.add_ui_element(self.wave_label)
        self.score_label = TextLabel(10, 50, "Score: 0", 24, font_name='russoone')
        self.add_ui_element(self.score_label)

        # ---- Bottom‑left compact HUD ----
        # Health bar background
        self.hp_bg_label = TextLabel(10, self.engine.height - 50, "HP", 20, font_name='russoone')
        self.add_ui_element(self.hp_bg_label)
        # We'll draw the health bar manually in render, but we need a label for HP value
        self.hp_text_label = TextLabel(60, self.engine.height - 50, "100/100 (100%)", 20, font_name='russoone')
        self.add_ui_element(self.hp_text_label)

        self.level_label = TextLabel(10, self.engine.height - 80, "Lv.1", 20, font_name='russoone')
        self.add_ui_element(self.level_label)
        self.xp_label = TextLabel(70, self.engine.height - 80, "0/50 XP", 20, font_name='russoone')
        self.add_ui_element(self.xp_label)

        # Regen info (optional)
        self.regen_label = TextLabel(10, self.engine.height - 110, "Regen: 8s", 16, font_name='russoone')
        self.add_ui_element(self.regen_label)

        # ---- Upgrade Frame (smaller, 3 columns) ----
        self.upgrade_frame = UiFrame(15*self.engine.ratio.x, self.engine.height - 160*self.engine.ratio.y,
                                     240 * self.engine.ratio.x, 320 * self.engine.ratio.y, pivot=(0,1))
        self.upgrade_frame.visible = False
        self.add_ui_element(self.upgrade_frame)

        self.upgrade_title = TextLabel(120*self.engine.ratio.x, 5*self.engine.ratio.y, "LEVEL UP!", 40, font_name='russoone', pivot=(0.5,0))
        self.upgrade_frame.add_child(self.upgrade_title)

        # Buttons in a 3‑column grid (7 buttons, last two maybe merged or we leave placeholders)
        btn_w, btn_h = 70, 40
        spacing = 10
        col1_x = 5
        col2_x = 5 + btn_w + spacing
        col3_x = col2_x + btn_w + spacing
        row1_y = 60
        row2_y = row1_y + btn_h + spacing
        row3_y = row2_y + btn_h + spacing

        # Row 1: Damage, Speed, Health
        self.btn_damage = Button(col1_x, row1_y, btn_w, btn_h, "+DMG", 18, font_name='russoone', pivot=(0,0))
        self.btn_damage.set_on_click(lambda: self.apply_upgrade('damage'))
        self.upgrade_frame.add_child(self.btn_damage)

        self.btn_speed = Button(col2_x, row1_y, btn_w, btn_h, "+SPD", 18, font_name='russoone', pivot=(0,0))
        self.btn_speed.set_on_click(lambda: self.apply_upgrade('speed'))
        self.upgrade_frame.add_child(self.btn_speed)

        self.btn_health = Button(col3_x, row1_y, btn_w, btn_h, "+HP", 18, font_name='russoone', pivot=(0,0))
        self.btn_health.set_on_click(lambda: self.apply_upgrade('health'))
        self.upgrade_frame.add_child(self.btn_health)

        # Row 2: Fire Rate, Bullet Speed, Regen Time
        self.btn_fire = Button(col1_x, row2_y, btn_w, btn_h, "+FIRE", 18, font_name='russoone', pivot=(0,0))
        self.btn_fire.set_on_click(lambda: self.apply_upgrade('fire'))
        self.upgrade_frame.add_child(self.btn_fire)

        self.btn_bullet_speed = Button(col2_x, row2_y, btn_w, btn_h, "+BSPD", 18, font_name='russoone', pivot=(0,0))
        self.btn_bullet_speed.set_on_click(lambda: self.apply_upgrade('bullet_speed'))
        self.upgrade_frame.add_child(self.btn_bullet_speed)

        self.btn_regen_time = Button(col3_x, row2_y, btn_w, btn_h, "-REGT", 18, font_name='russoone', pivot=(0,0))
        self.btn_regen_time.set_on_click(lambda: self.apply_upgrade('regen_time'))
        self.upgrade_frame.add_child(self.btn_regen_time)

        # Row 3: Regen Rate, plus maybe a "Skip" button? We'll put Regen Rate and a dummy or skip
        self.btn_regen_rate = Button(col1_x, row3_y, btn_w, btn_h, "+REGR", 18, font_name='russoone', pivot=(0,0))
        self.btn_regen_rate.set_on_click(lambda: self.apply_upgrade('regen_rate'))
        self.upgrade_frame.add_child(self.btn_regen_rate)

        # Skip button (to close without upgrade – but we can just let player choose any)
        self.btn_skip = Button(col2_x, row3_y, btn_w*2 + spacing, btn_h, "SKIP", 18, font_name='russoone', pivot=(0,0))
        self.btn_skip.set_on_click(lambda: self.skip_upgrade())
        self.upgrade_frame.add_child(self.btn_skip)

        self.upgrade_pending = False

        # ---- Game Over overlay ----
        self.game_over_label = TextLabel(self.engine.width//2, self.engine.height//2 - 40,
                                         "GAME OVER", 72, (255,50,50), font_name='russoone', pivot=(0.5,0.5))
        self.game_over_label.visible = False
        self.add_ui_element(self.game_over_label)

        self.retry_btn = Button(self.engine.width//2, self.engine.height//2 + 60,
                                200, 60, "Retry", 40, font_name='russoone', pivot=(0.5,0.5))
        self.retry_btn.set_on_click(self.retry)
        self.retry_btn.visible = False
        self.add_ui_element(self.retry_btn)

        self.menu_btn = Button(self.engine.width//2, self.engine.height//2 + 140,
                               200, 60, "Menu", 40, font_name='russoone', pivot=(0.5,0.5))
        self.menu_btn.set_on_click(lambda: self.engine.set_scene("main"))
        self.menu_btn.visible = False
        self.add_ui_element(self.menu_btn)

        self.engine.add_function_to_live_inspector(
            "Level Up",
            lambda: (self.player.__setattr__('xp', self.player.xp_to_next), self.check_level_up()),
            [], 'Force a level up',
        )
        self.engine.add_function_to_live_inspector(
            "Invincibility",
            lambda invencible: (self.player.__setattr__('can_take_damage', not invencible())),
            [('invencible', bool)], 'Invincibility',
        )
        self.engine.add_function_to_live_inspector(
            "Suicide",
            lambda: self.player.take_damage(self.player.max_health + 1000),
            [], 'Suicide',
        )
        self.engine.add_function_to_live_inspector(
            "Upgrade Damage",
            lambda i: (self.__setattr__('upgrade_pending', True), self.apply_upgrade('damage', times=i)),
            [("times", int)], 'Upgrade Damage',
        )
        self.engine.add_function_to_live_inspector(
            "Upgrade Speed",
            lambda i: (self.__setattr__('upgrade_pending', True), self.apply_upgrade('speed', times=i)),
            [("times", int)], 'Upgrade Speed',
        )
        self.engine.add_function_to_live_inspector(
            "Upgrade Health",
            lambda i: (self.__setattr__('upgrade_pending', True), self.apply_upgrade('health', times=i)),
            [("times", int)], 'Upgrade Health',
        )
        self.engine.add_function_to_live_inspector(
            "Upgrade Fire Rate",
            lambda i: (self.__setattr__('upgrade_pending', True), self.apply_upgrade('fire', times=i)),
            [("times", int)], 'Upgrade Fire Rate',
        )
        self.engine.add_function_to_live_inspector(
            "Upgrade Bullet Speed",
            lambda i: (self.__setattr__('upgrade_pending', True), self.apply_upgrade('bullet_speed', times=i)),
            [("times", int)], 'Upgrade Bullet Speed',
        )
        self.engine.add_function_to_live_inspector(
            "Upgrade Regen Time",
            lambda i: (self.__setattr__('upgrade_pending', True), self.apply_upgrade('regen_time', times=i)),
            [("times", int)], 'Upgrade Regen Time',
        )
        self.engine.add_function_to_live_inspector(
            "Upgrade Regen Rate",
            lambda i: (self.__setattr__('upgrade_pending', True), self.apply_upgrade('regen_rate', times=i)),
            [("times", int)], 'Upgrade Regen Rate',
        )

    def on_enter(self, previous_scene_name=None):
        self.player = PlayerTank(400, 300)
        self.enemies.clear()
        self.bullets.clear()
        self.wave = 0
        self.enemies_per_wave = 2
        self.wave_timer = 2.0
        self.spawn_timer = 0
        self.enemies_spawned = 0
        self.game_over = False
        self.boss_active = False
        self.wave_in_progress = False
        self.score = 0
        self.start_time = time.time()
        self.upgrade_pending = False
        self.upgrade_frame.visible = False
        self.game_over_label.visible = False
        self.retry_btn.visible = False
        self.menu_btn.visible = False

        self.camera.set_target(self.player)
        self.camera.position = pygame.Vector2(
            self.player.x - self.engine.width // 2,
            self.player.y - self.engine.height // 2
        )

    def retry(self):
        self.engine.set_scene("game")

    def apply_upgrade(self, choice, times=1):
        if not self.upgrade_pending:
            return
        if choice == 'damage':
            self.player.damage += 5 * times
        elif choice == 'speed':
            self.player.speed += 20 * times
        elif choice == 'health':
            self.player.max_health += 25 * times
            self.player.health = min(self.player.health + 25, self.player.max_health)
        elif choice == 'fire':
            self.player.fire_rate *= (0.85 ** times)
        elif choice == 'bullet_speed':
            self.player.bullet_speed += 50 * times
        elif choice == 'regen_time':
            self.player.regen_time = max(1.0, self.player.regen_time - 0.5 * times)
        elif choice == 'regen_rate':
            self.player.regen_rate += 2 * times
        self.upgrade_pending = False
        self.upgrade_frame.visible = False

    def skip_upgrade(self):
        self.upgrade_pending = False
        self.upgrade_frame.visible = False

    def show_upgrade_choice(self):
        self.upgrade_pending = True
        self.upgrade_frame.visible = True

    def start_wave(self):
        self.wave += 1
        self.enemies_per_wave = min(2 + (self.wave - 1) * 1, 12)
        self.enemies_spawned = 0
        self.wave_in_progress = True
        self.spawn_timer = 0
        self.wave_label.set_text(f"Wave: {self.wave}")

        if self.wave % 5 == 0:
            self.boss_active = True
            boss = EnemyTank(100, 100, personality='tank')
            boss.health *= 2
            boss.max_health = boss.health
            boss.radius *= 1.5
            boss.damage *= 2
            boss.shoot_cooldown *= 0.7
            self.enemies.append(boss)
            self.enemies_spawned += 1

    def spawn_enemy(self):
        side = random.choice(['top','bottom','left','right'])
        margin = 50
        if side == 'top':
            x = random.randint(0, 1000)
            y = -margin
        elif side == 'bottom':
            x = random.randint(0, 1000)
            y = 800 + margin
        elif side == 'left':
            x = -margin
            y = random.randint(0, 800)
        else:
            x = 1000 + margin
            y = random.randint(0, 800)
        personality = random.choices(['chaser','sniper','flanker','tank'],
                                     weights=[40,20,30,10])[0]
        enemy = EnemyTank(x, y, personality)
        self.enemies.append(enemy)

    def update(self, dt):
        if self.game_over:
            return

        # Player input
        keys = pygame.key.get_pressed()
        mouse_pos = self.engine.input_state.mouse_pos
        self.player.update(dt, keys, mouse_pos, self.bullets, self.camera)

        if not self.player.alive:
            self.game_over = True
            self.game_over_label.visible = True
            self.retry_btn.visible = True
            self.menu_btn.visible = True
            LDM.add_score(LDM.current_username, self.wave, self.score)
            super().update(dt)
            return

        # Enemies
        for enemy in self.enemies[:]:
            enemy.update(dt, self.player, self.bullets)
            if not enemy.alive:
                self.enemies.remove(enemy)
                self.score += 10 * (1 + self.wave // 5)
                if random.random() < 0.15:
                    self.player.health = min(self.player.health + 10, self.player.max_health)

        # Bullets
        for bullet in self.bullets[:]:
            bullet.update(dt)
            if not bullet.alive:
                self.bullets.remove(bullet)
                continue
            if bullet.owner == 'player':
                for enemy in self.enemies[:]:
                    if math.hypot(bullet.x - enemy.x, bullet.y - enemy.y) < enemy.radius + bullet.radius:
                        enemy.take_damage(bullet.damage)
                        if not enemy.alive:
                            self.enemies.remove(enemy)
                            self.score += 10 * (1 + self.wave // 5)
                            xp_gain = 5 + self.wave
                            self.player.xp += xp_gain
                            self.check_level_up()
                            if random.random() < 0.15:
                                self.player.health = min(self.player.health + 10, self.player.max_health)
                        self.bullets.remove(bullet)
                        break
            elif bullet.owner == 'enemy':
                if math.hypot(bullet.x - self.player.x, bullet.y - self.player.y) < self.player.radius + bullet.radius:
                    self.player.take_damage(bullet.damage)
                    self.bullets.remove(bullet)
                    if not self.player.alive:
                        self.game_over = True
                        self.game_over_label.visible = True
                        self.retry_btn.visible = True
                        self.menu_btn.visible = True
                        LDM.add_score(LDM.current_username, self.wave, self.score)

        # Wave management
        if self.wave_in_progress:
            if self.enemies_spawned < self.enemies_per_wave:
                self.spawn_timer -= dt
                if self.spawn_timer <= 0:
                    self.spawn_enemy()
                    self.enemies_spawned += 1
                    self.spawn_timer = 0.8
            else:
                if len(self.enemies) == 0:
                    self.wave_in_progress = False
                    self.wave_timer = self.wave_delay
                    self.player.xp += 20 + self.wave * 5
                    self.check_level_up()
        else:
            self.wave_timer -= dt
            if self.wave_timer <= 0:
                self.start_wave()

        # Update UI
        self.score_label.set_text(f"Score: {self.score}")
        self.hp_text_label.set_text(f"{int(self.player.health)}/{int(self.player.max_health)} ({int((self.player.health / self.player.max_health) * 100)}%)")
        self.level_label.set_text(f"Lv.{self.player.level}")
        self.xp_label.set_text(f"{self.player.xp}/{self.player.xp_to_next} XP")
        self.regen_label.set_text(f"Regen: {self.player.regen_time:.1f}s")

        super().update(dt)

    def check_level_up(self):
        while self.player.xp >= self.player.xp_to_next:
            self.player.xp -= self.player.xp_to_next
            self.player.level += 1
            self.player.xp_to_next = int(self.player.xp_to_next * 1.4) + 10
            self.show_upgrade_choice()

    def render(self, renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))

        # ---- Grid ----
        grid_color = (50, 60, 80)
        step = 100
        for x in range(-100, 1100, step):
            start = self.camera.world_to_screen((x, -100))
            end = self.camera.world_to_screen((x, 900))
            renderer.draw_line(start.x, start.y, end.x, end.y, grid_color)
        for y in range(-100, 900, step):
            start = self.camera.world_to_screen((-100, y))
            end = self.camera.world_to_screen((1100, y))
            renderer.draw_line(start.x, start.y, end.x, end.y, grid_color)

        # ---- Bullets ----
        for b in self.bullets:
            b.render(renderer, self.camera)

        # ---- Enemies ----
        for e in self.enemies:
            e.render(renderer, self.camera)

        # ---- Player ----
        self.player.render(renderer, self.camera)

        # ---- Draw custom health bar at bottom-left ----
        bar_x = 10
        bar_y = self.engine.height - 45
        bar_width = 120
        bar_height = 24
        # background
        renderer.draw_rect(bar_x, bar_y, bar_width, bar_height, (40, 40, 40))
        # fill
        hp_ratio = self.player.health / self.player.max_health
        fill_width = int(bar_width * hp_ratio)
        color = (0, 255, 0) if hp_ratio > 0.3 else (255, 0, 0)
        renderer.draw_rect(bar_x, bar_y, fill_width, bar_height, color)
        # border
        renderer.draw_rect(bar_x, bar_y, bar_width, bar_height, (100, 100, 100), fill=False)

        # ---- Also draw XP bar below HP ----
        xp_bar_x = bar_x
        xp_bar_y = bar_y + bar_height + 4
        xp_bar_width = bar_width
        xp_bar_height = 8
        renderer.draw_rect(xp_bar_x, xp_bar_y, xp_bar_width, xp_bar_height, (40, 40, 40))
        xp_ratio = self.player.xp / self.player.xp_to_next if self.player.xp_to_next > 0 else 0
        renderer.draw_rect(xp_bar_x, xp_bar_y, int(xp_bar_width * xp_ratio), xp_bar_height, (100, 200, 255))

        # ---- UI drawn by super ----
        super().render(renderer)

# ------------------------- Main Menu -------------------------
class MainMenu(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.username = "Player"
        self.setup_ui()

    def setup_ui(self):
        self.add_ui_element(TextLabel(self.engine.width//2, 60, "Tank Siege", 80,
                                      font_name='russoone', pivot=(0.5,0)))

        play_btn = Button(self.engine.width//2, 200, 250, 70, "Play", 50,
                          font_name='russoone', pivot=(0.5,0))
        play_btn.set_on_click(self.play)
        self.add_ui_element(play_btn)

        exit_btn = Button(self.engine.width//2, 290, 200, 60, "Exit", 40,
                          font_name='russoone', pivot=(0.5,0))
        exit_btn.set_on_click(lambda: setattr(self.engine, 'running', False))
        self.add_ui_element(exit_btn)

        self.add_ui_element(TextLabel(self.engine.width//2, 370, "Username:", 30,
                                      font_name='russoone', pivot=(0.5,0)))
        self.username_box = TextBox(self.engine.width//2, 410, 200, 40,
                                    LDM.current_username, 28, font_name='russoone', pivot=(0.5,0))
        self.add_ui_element(self.username_box)

        self.add_ui_element(TextLabel(self.engine.width//2, 480, "Leaderboard", 40,
                                      font_name='russoone', pivot=(0.5,0)))

        self.leader_frame = ScrollingFrame(self.engine.width//2, 530,
                                           500, 200, 480, 400, pivot=(0.5,0))
        self.add_ui_element(self.leader_frame)
        self.update_leaderboard()

    def update_leaderboard(self):
        self.leader_frame.clear_children()
        scores = LDM.get_top(10)
        if not scores:
            no_score = TextLabel(240, 20, "No scores yet!", 24,
                                 font_name='russoone', pivot=(0.5,0))
            self.leader_frame.add_child(no_score)
        else:
            for i, entry in enumerate(scores):
                text = f"#{i+1} {entry['name']} - Wave {entry['wave']} - Score {entry['score']}"
                label = TextLabel(20, 20 + i*35, text, 22, font_name='russoone', pivot=(0,0))
                self.leader_frame.add_child(label)

    def play(self):
        name = self.username_box.text.strip()
        if name:
            LDM.current_username = name
        else:
            LDM.current_username = "Player"
        self.engine.set_scene("game")

    def on_enter(self, previous_scene_name=None):
        self.update_leaderboard()

    def render(self, renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))

# ------------------------- Main -------------------------
def main():
    args = argparser.parse_args(sys.argv[1:])

    if args.username:
        LDM.current_username = args.username

    engine = LunaEngine("TankSiege", 1024, 768,
                        fullscreen=args.fullscreen,
                        debug=args.debug)

    root = Path(os.path.abspath(os.path.dirname(__file__)))
    engine.atlas.add_folder("root", root)
    engine.atlas.add_folder("assets", root / "assets")

    font_path = engine.atlas.get_item("assets").path / "RussoOne.ttf"
    if font_path.exists():
        engine.atlas.add_font("russoone", font_path)
    else:
        engine.atlas.add_font("russoone", None)

    icon_path = engine.atlas.get_item("assets").path / "icon.png"
    if icon_path.exists():
        engine.set_icon(str(icon_path))

    engine.update_ratio(1024, 768)
    engine.set_global_theme(ThemeType.BUILDER)
    engine.set_dark_mode(False)

    engine.add_scene("main", MainMenu)
    engine.add_scene("game", GameScene)

    engine.set_scene("main")
    engine.run()

if __name__ == "__main__":
    main()