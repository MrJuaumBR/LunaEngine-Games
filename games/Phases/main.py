# main.py
from lunaengine.core import LunaEngine, Scene, Renderer
from lunaengine.ui import *
import pygame as pg
import argparse, sys, os, json, math, datetime
from pathlib import Path

from assets.src import Player, Cannon, Portal, LEVEL_LOADER

# ------------------------- Leaderboard Manager -------------------------
class LeaderboardManager:
    def __init__(self, file_name='leaderboard.json'):
        self.file_path = Path(os.path.abspath(os.path.dirname(__file__))) / file_name
        self.data = self._load()
        self.current_level = 1
        self.current_name = "Player"

    def _load(self):
        if self.file_path.exists():
            with open(self.file_path) as f:
                return json.load(f)
        return {}

    def save(self):
        with open(self.file_path, 'w') as f:
            json.dump(self.data, f, indent=2)

    def get_level_scores(self, level):
        key = f"level_{level}"
        entries = self.data.get(key, [])
        entries.sort(key=lambda x: (-x["stars"], x["time"]))
        return entries

    def add_score(self, level, name, stars, time):
        key = f"level_{level}"
        entry = {"name": name, "stars": stars, "time": time, "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
        if key not in self.data:
            self.data[key] = []
        self.data[key].append(entry)
        self.data[key].sort(key=lambda x: (-x["stars"], x["time"]))
        self.data[key] = self.data[key][:10]
        self.save()

LDM = LeaderboardManager()

# ------------------------- Game Objects -------------------------
class Goal:
    def __init__(self, engine, pos, sprite=None, tile_size=32):
        self.engine = engine
        if sprite:
            self.image = pg.transform.scale(sprite, (int(tile_size * 0.8), int(tile_size * 0.8)))
        else:
            self.image = pg.Surface((20, 30))
            self.image.fill((0, 255, 255))
        self.rect = self.image.get_rect(center=pos)

    def render(self, renderer, offset=(0, 0)):
        x = self.rect.x - offset[0]
        y = self.rect.y - offset[1]
        renderer.blit(self.image, (x, y))

class Enemy:
    def __init__(self, engine, x, y, etype, range_val=None, points=None,
                 sprite=None, tile_size=32):
        self.engine = engine
        self.x0, self.y0 = x, y
        self.etype = etype
        self.range = range_val or 0
        self.points = points or []
        self.phase = 0
        self.speed = 2
        if sprite:
            self.image = pg.transform.scale(sprite, (int(tile_size * 0.7), int(tile_size * 0.7)))
        else:
            self.image = pg.Surface((20, 20))
            self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect(center=(x, y))

    def update(self, dt):
        self.phase += 0.02 * self.speed
        if self.etype == 'vertical':
            self.rect.centery = self.y0 + self.range * math.sin(self.phase)
        elif self.etype == 'horizontal':
            self.rect.centerx = self.x0 + self.range * math.sin(self.phase)
        elif self.etype == 'patrol' and self.points:
            idx = int((len(self.points) - 1) * (0.5 + 0.5 * math.sin(self.phase)))
            self.rect.center = self.points[idx]

    def render(self, renderer, offset=(0, 0)):
        x = self.rect.x - offset[0]
        y = self.rect.y - offset[1]
        renderer.blit(self.image, (x, y))

# ------------------------- Game Scene -------------------------
class GameScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.level = LDM.current_level
        self.level_data = None
        self.sprites = None
        self.player = None
        self.goal = None
        self.enemies = []
        self.cannons = []
        self.portals = []
        self.bullets = []
        self.all_entities = []
        self.level_complete = False
        self.game_over = False
        self.start_time = 0
        self.tile_size = 0
        self.level_label = None

        # Load spritesheet once
        try:
            objects_sheet = pg.image.load(engine.atlas.get_item('textures').path / 'objects.png').convert_alpha()
            self.sprites = {
                'enemy': objects_sheet.subsurface((0, 0, 32, 32)),
                'cannon': objects_sheet.subsurface((32, 0, 32, 32)),
                'goal': objects_sheet.subsurface((64, 0, 32, 32)),
                'portal_entrance': objects_sheet.subsurface((96, 0, 32, 32)),
                'portal_exit': objects_sheet.subsurface((128, 0, 32, 32)),
            }
        except Exception as e:
            print(f"Could not load objects spritesheet: {e}")
            self.sprites = None

        # UI label (persistent)
        self.level_label = TextLabel(10, 10, f'Level {self.level}', 30, font_name='dotgothic')
        self.add_ui_element(self.level_label)

        # Load the level
        self._load_level()

    def _load_level(self):
        """Load or reload the level data and create all game objects."""
        self.level_data = LEVEL_LOADER.get_level(self.level)
        self.star_times = self.level_data.get("star_times", {"1": 60, "2": 40, "3": 20})
        self.tile_size = self._compute_tile_size()
        self.bullets.clear()
        self.level_complete = False
        self.game_over = False
        self.start_time = pg.time.get_ticks()

        def g2p(gx, gy):
            return LEVEL_LOADER.grid_to_pixel(self.level_data, gx, gy, self.tile_size)

        # --- Player ---
        start = self.level_data["entities"]["player_start"]
        if self.player is None:
            self.player = Player(self.engine, g2p(*start))
            self.player.size = (self.tile_size * 0.8, self.tile_size * 0.8)
        else:
            self.player.pos = list(g2p(*start))
        # Scale player image
        self.player.original_image = pg.transform.scale(self.player.original_image,
                                                        (int(self.player.size[0]), int(self.player.size[1])))
        self.player.image = self.player.original_image.copy()
        self.player.rect = self.player.image.get_rect(center=self.player.pos)
        self.player.collision_rect = self.player.rect.inflate(
            -self.player.rect.width * 0.2, -self.player.rect.height * 0.2
        )

        # --- Goal ---
        goal_grid = self.level_data["entities"]["goal"]
        goal_sprite = self.sprites['goal'] if self.sprites else None
        if self.goal is None:
            self.goal = Goal(self.engine, g2p(*goal_grid), sprite=goal_sprite, tile_size=self.tile_size)
        else:
            self.goal.rect.center = g2p(*goal_grid)

        # --- Enemies ---
        self.enemies.clear()
        enemy_sprite = self.sprites['enemy'] if self.sprites else None
        for e in self.level_data["entities"].get("enemies", []):
            x, y = g2p(e["x"], e["y"])
            enemy = Enemy(self.engine, x, y, e["type"],
                          e.get("range", 0) * self.tile_size,
                          e.get("points", []),
                          sprite=enemy_sprite,
                          tile_size=self.tile_size)
            self.enemies.append(enemy)

        # --- Cannons ---
        self.cannons.clear()
        cannon_sprite = self.sprites['cannon'] if self.sprites else None
        for c in self.level_data["entities"].get("cannons", []):
            pos = g2p(c["x"], c["y"])
            cannon = Cannon(self.engine, pos[0], pos[1], c["dir"],
                            sprite=cannon_sprite,
                            tile_size=self.tile_size)
            self.cannons.append(cannon)

        # --- Portals ---
        self.portals.clear()
        entrance_sprite = self.sprites['portal_entrance'] if self.sprites else None
        exit_sprite = self.sprites['portal_exit'] if self.sprites else None
        for p in self.level_data["entities"].get("portals", []):
            pos = g2p(p["x"], p["y"])
            target = g2p(p["target"][0], p["target"][1])
            portal = Portal(self.engine, pos, target,
                            entrance_sprite=entrance_sprite,
                            exit_sprite=exit_sprite,
                            tile_size=self.tile_size)
            self.portals.append(portal)

        self.all_entities = [self.player, self.goal] + self.enemies
        self.level_label.set_text(f'Level {self.level}')

    def on_enter(self, previous_scene=None):
        """Called when the scene is entered (e.g., after retry or level select)."""
        self.level = LDM.current_level
        self._load_level()

    def _compute_tile_size(self):
        level_w = self.level_data["width"]
        level_h = self.level_data["height"]
        tile_w = self.engine.width // level_w
        tile_h = self.engine.height // level_h
        return min(tile_w, tile_h)

    def check_wall_collision(self, rect):
        x1 = rect.left // self.tile_size
        x2 = (rect.right - 1) // self.tile_size
        y1 = rect.top // self.tile_size
        y2 = (rect.bottom - 1) // self.tile_size
        for gy in range(y1, y2 + 1):
            for gx in range(x1, x2 + 1):
                if LEVEL_LOADER.is_wall(self.level_data, gx, gy):
                    return True
        return False

    def update(self, dt):
        if self.game_over or self.level_complete:
            return

        # ---- Player movement with sliding ----
        keys = pg.key.get_pressed()
        dx = 0
        if keys[pg.K_a] or keys[pg.K_LEFT]:
            dx = -1
        if keys[pg.K_d] or keys[pg.K_RIGHT]:
            dx = 1
        dy = 0
        if keys[pg.K_w] or keys[pg.K_UP]:
            dy = -1
        if keys[pg.K_s] or keys[pg.K_DOWN]:
            dy = 1

        # Move X
        self.player.pos[0] += dx * self.player.speed
        self.player.rect.center = self.player.pos
        self.player.collision_rect.center = self.player.pos
        if self.check_wall_collision(self.player.collision_rect):
            self.player.pos[0] -= dx * self.player.speed
            self.player.rect.center = self.player.pos
            self.player.collision_rect.center = self.player.pos

        # Move Y
        self.player.pos[1] += dy * self.player.speed
        self.player.rect.center = self.player.pos
        self.player.collision_rect.center = self.player.pos
        if self.check_wall_collision(self.player.collision_rect):
            self.player.pos[1] -= dy * self.player.speed
            self.player.rect.center = self.player.pos
            self.player.collision_rect.center = self.player.pos

        # Update player facing (for flip in render)
        if dx < 0:
            self.player.facing_right = False
        elif dx > 0:
            self.player.facing_right = True

        # ---- Enemies ----
        for e in self.enemies:
            e.update(dt)

        # ---- Cannons ----
        for c in self.cannons:
            c.update(dt)

        # Remove off-screen or wall-hit bullets
        new_bullets = []
        for b in self.bullets:
            # Check if bullet is inside screen bounds (with margin)
            if not (b.rect.x < -50 or b.rect.x > self.engine.width + 50 or 
                b.rect.y < -50 or b.rect.y > self.engine.height + 50) and not self.check_wall_collision(b.rect):
                new_bullets.append(b)
                b.update(dt)
        self.bullets = new_bullets

        # ---- Collisions ----
        for e in self.enemies:
            if self.player.collision_rect.colliderect(e.rect):
                self.game_over = True
                self.engine.set_scene("game_over")
                return

        if not self.game_over:
            for b in self.bullets:
                if self.player.collision_rect.colliderect(b.rect):
                    self.game_over = True
                    self.engine.set_scene("game_over")
                    return

        if not self.game_over:
            for p in self.portals:
                if p.detect_player_collision(self.player.collision_rect):
                    self.player.pos = list(p.target)
                    self.player.rect.center = p.target
                    self.player.collision_rect.center = p.target

        if not self.game_over and self.player.collision_rect.colliderect(self.goal.rect):
            self.level_complete = True
            elapsed = (pg.time.get_ticks() - self.start_time) // 1000
            stars = 3
            for s in [3, 2, 1]:
                if elapsed <= self.star_times.get(str(s), 9999):
                    stars = s
                    break
            LDM.add_score(self.level, LDM.current_name, stars, elapsed)
            self.engine.scenes["level_complete"].set_result(stars, elapsed)
            self.engine.set_scene("level_complete")

        # ---- Camera ----
        self.camera.position = (self.player.pos[0] - self.engine.width // 2,
                                self.player.pos[1] - self.engine.height // 2)

    def render(self, renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))
        offset = self.camera.position

        # ---- Tiles ----
        tiles = self.level_data["tiles"]
        ts = self.tile_size
        for y, row in enumerate(tiles):
            for x, tile in enumerate(row):
                if tile == 1:
                    # Solid wall
                    px = x * ts - offset[0]
                    py = y * ts - offset[1]
                    renderer.draw_rect(px, py, ts, ts, (60, 60, 60))
                elif tile == 2:
                    px = x * ts - offset[0]
                    py = y * ts - offset[1]
                    renderer.draw_rect(px, py, ts, ts, (65, 65, 65))

        # ---- Entities ----
        for ent in self.all_entities:
            ent.render(renderer, offset=offset)

        # ---- Bullets ----
        for b in self.bullets:
            b.render(renderer, offset=offset)

        # ---- Cannons & Portals ----
        for c in self.cannons:
            c.render(renderer, offset=offset)
        for p in self.portals:
            p.render(renderer, offset=offset)

    def on_event(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                self.engine.set_scene("level_select")
            if event.key == pg.K_r and self.game_over:
                self.engine.set_scene("game")

# ------------------------- Level Complete Scene -------------------------
class LevelCompleteScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.stars = 0
        self.time = 0
        try:
            stars_sheet = pg.image.load(engine.atlas.get_item('textures').path / 'stars.png').convert_alpha()
            self.full_star = stars_sheet.subsurface((0, 0, 32, 32))
            self.empty_star = stars_sheet.subsurface((32, 0, 32, 32))
            star_size = int(40 * engine.ratio.med)
            self.full_star = pg.transform.scale(self.full_star, (star_size, star_size))
            self.empty_star = pg.transform.scale(self.empty_star, (star_size, star_size))
            self.star_size = star_size
        except Exception as e:
            print(f"Could not load star spritesheet: {e}")
            self.full_star = None
            self.empty_star = None
            self.star_size = 0

        self.setup_ui()

    def set_result(self, stars, time):
        self.stars = stars
        self.time = time
        self.time_label.set_text(f"Time: {time}s")

    def setup_ui(self):
        self.add_ui_element(TextLabel(self.engine.width//2, 100, "Level Complete!", 60,
                                      font_name='dotgothic', pivot=(0.5,0)))
        self.time_label = TextLabel(self.engine.width//2, 200, "Time: 0s", 40,
                                    font_name='dotgothic', pivot=(0.5,0))
        self.add_ui_element(self.time_label)

        next_btn = Button(self.engine.width//2, 300, 200, 60, "Next Level", 30,
                          font_name='dotgothic', pivot=(0.5,0))
        next_btn.set_on_click(self.next_level)
        self.add_ui_element(next_btn)

        menu_btn = Button(self.engine.width//2, 380, 200, 60, "Level Select", 30,
                          font_name='dotgothic', pivot=(0.5,0))
        menu_btn.set_on_click(lambda: self.engine.set_scene("level_select"))
        self.add_ui_element(menu_btn)

    def render(self, renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))
        if self.full_star is not None:
            total_width = self.stars * self.star_size + (3 - self.stars) * self.star_size
            start_x = self.engine.width//2 - total_width//2
            y = 160
            for i in range(3):
                if i < self.stars:
                    surf = self.full_star
                else:
                    surf = self.empty_star
                renderer.blit(surf, (start_x + i * self.star_size, y))

    def next_level(self):
        LDM.current_level += 1
        # Check if next level exists
        try:
            LEVEL_LOADER.get_level(LDM.current_level)
        except:
            LDM.current_level = max(1, LDM.current_level - 1)
            self.engine.set_scene("level_select")
            return
        self.engine.set_scene("game")

# ------------------------- Game Over Scene -------------------------
class GameOverScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.setup_ui()

    def setup_ui(self):
        self.add_ui_element(TextLabel(self.engine.width//2, 100, "Game Over", 60,
                                      font_name='dotgothic', pivot=(0.5,0)))
        restart_btn = Button(self.engine.width//2, 250, 200, 60, "Retry", 30,
                             font_name='dotgothic', pivot=(0.5,0))
        restart_btn.set_on_click(lambda: self.engine.set_scene("game"))
        self.add_ui_element(restart_btn)

        menu_btn = Button(self.engine.width//2, 330, 200, 60, "Level Select", 30,
                          font_name='dotgothic', pivot=(0.5,0))
        menu_btn.set_on_click(lambda: self.engine.set_scene("level_select"))
        self.add_ui_element(menu_btn)

    def render(self, renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))

# ------------------------- Level Select Scene (dynamic) -------------------------
class LevelSelectScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.selected_level = 1
        self.available_levels = self._get_available_levels()
        self.setup_ui()

    def _get_available_levels(self):
        """Scan the levels folder for level_*.json files."""
        levels_folder = Path(__file__).parent / "assets" / "src" / "levels"
        if not levels_folder.exists():
            return list(range(1, 13))  # fallback

        levels = []
        for file in levels_folder.glob("level_*.json"):
            try:
                num = int(file.stem.split("_")[1])
                levels.append(num)
            except:
                continue
        return sorted(levels) if levels else list(range(1, 13))

    def setup_ui(self):
        self.add_ui_element(TextLabel(self.engine.width//2, 40, 'Select Level', 60,
                                      font_name='dotgothic', pivot=(0.5,0)))

        self.levels_frame = ScrollingFrame(60, 100, 650, 500, 650, 700, pivot=(0,0))
        cols = 4
        spacing = 10
        width = 150
        height = 140

        for i in self.available_levels:
            row = (i - 1) // cols
            col = (i - 1) % cols
            x = 10 + col * (width + spacing)
            y = 10 + row * (height + spacing)
            frame = UiFrame(x, y, width, height)

            # Level label
            frame.add_child(TextLabel(width//2, 10, f'Level {i}', 22,
                                      font_name='dotgothic', pivot=(0.5,0)))

            # Select button
            select_btn = Button(width//2, height-10, 100, 30, 'Select', 20,
                                font_name='dotgothic', pivot=(0.5,1))
            select_btn.set_on_click(lambda lvl=i: self.select_level(lvl))
            frame.add_child(select_btn)

            self.levels_frame.add_child(frame)

        self.add_ui_element(self.levels_frame)

        # Right panel
        right_panel = UiFrame(self.engine.width - 10, 100, 450, 500, pivot=(1,0))
        self.info_label = TextLabel(225, 10, f'Level {self.selected_level}', 30,
                                    font_name='dotgothic', pivot=(0.5,0))
        right_panel.add_child(self.info_label)

        self.leaderboard_table = Table(10, 50, 430, 400,
                                       ['Name', 'Stars', 'Time'],
                                       [], row_height=30)
        right_panel.add_child(self.leaderboard_table)

        self.play_btn = Button(225, 470, 150, 50, 'Play', 30,
                               font_name='dotgothic', pivot=(0.5,1))
        self.play_btn.set_on_click(self.start_game)
        right_panel.add_child(self.play_btn)

        self.add_ui_element(right_panel)

        back = Button(60, 20, 100, 40, 'Back', 30, font_name='dotgothic')
        back.set_on_click(lambda: self.engine.set_scene('main'))
        self.add_ui_element(back)

        self.select_level(self.available_levels[0] if self.available_levels else 1)

    def select_level(self, level):
        self.selected_level = level
        self.info_label.set_text(f'Level {level}')
        self.leaderboard_table.clear()
        scores = LDM.get_level_scores(level)
        for entry in scores:
            self.leaderboard_table.add_row([entry['name'], str(entry['stars']), f"{entry['time']}s"])

    def start_game(self):
        LDM.current_level = self.selected_level
        self.engine.set_scene('game')

    def render(self, renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))

# ------------------------- Main Menu -------------------------
class MainMenu(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.setup_ui()

    def setup_ui(self):
        self.add_ui_element(TextLabel(self.engine.width//2, 100, 'Phases', 80,
                                      font_name='dotgothic', pivot=(0.5,0)))
        play = Button(self.engine.width//2, 250, 200, 70, 'Play', 50,
                      font_name='dotgothic', pivot=(0.5,0))
        play.set_on_click(lambda: self.engine.set_scene('level_select'))
        self.add_ui_element(play)

        quit_btn = Button(self.engine.width//2, 350, 200, 60, 'Quit', 50,
                          font_name='dotgothic', pivot=(0.5,0))
        quit_btn.set_on_click(self.engine.shutdown)
        self.add_ui_element(quit_btn)

    def render(self, renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))

# ------------------------- Main -------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--fullscreen', action='store_true')
    args = parser.parse_args()

    engine = LunaEngine("Phases", 1280, 720,
                        fullscreen=args.fullscreen,
                        debug=args.debug)

    engine.set_global_theme(ThemeType.LINUX)
    engine.set_dark_mode(False)
    engine.update_ratio(1280, 720)

    root = Path(os.path.abspath(os.path.dirname(__file__)))
    engine.atlas.add_folder("root", root)
    engine.atlas.add_folder("assets", root / "assets")
    engine.atlas.add_folder("textures", root / "assets" / "textures")
    engine.atlas.add_folder("fonts", root / "assets" / "fonts")
    engine.atlas.add_font("dotgothic", engine.atlas.get_item("fonts").path / 'DotGothic16.ttf')
    engine.set_icon(str(engine.atlas.get_item("textures").path / 'icon.png'))

    engine.add_scene("main", MainMenu)
    engine.add_scene("level_select", LevelSelectScene)
    engine.add_scene("game", GameScene)
    engine.add_scene("game_over", GameOverScene)
    engine.add_scene("level_complete", LevelCompleteScene)

    LDM.current_level = 1
    engine.set_scene("main")
    engine.run()

if __name__ == "__main__":
    main()