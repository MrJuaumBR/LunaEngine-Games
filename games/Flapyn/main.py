from lunaengine.core import LunaEngine, Scene
from lunaengine.ui import *
from lunaengine.backend import OpenGLRenderer
from lunaengine.graphics import SpriteSheet, Animation
import pygame as pg

import argparse, sys, os, json, datetime, random, time, math
from pathlib import Path

# ------------------------- Command line args -------------------------
parser = argparse.ArgumentParser()
parser.add_argument('--debug', action='store_true', help='Enable debug mode')
parser.add_argument('--fullscreen', action='store_true', help='Run in fullscreen')

# ------------------------- Leaderboard Manager -------------------------
class LeaderboardManager:
    def __init__(self, file_name: str = 'leaderboard.json'):
        self.file_name = Path(os.path.abspath(os.path.dirname(__file__))) / file_name
        self.data: dict = {}
        self.current_name:str = ''
        self.get_data()

    def get_data(self):
        if not self.file_name.exists():
            with open(self.file_name, 'w+') as f:
                json.dump({'scores': []}, f)
            self.data = {'scores': []}
        else:
            with open(self.file_name, 'r') as f:
                self.data = json.load(f)

    def save(self):
        with open(self.file_name, 'w') as f:
            json.dump(self.data, f)
            
    def set_username(self, username: str):
        self.current_name = username

    def add_score(self, score):
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        scores: list = self.data.get('scores', [])
        scores.append({'name': str(self.current_name), 'score': score, 'date': date})
        self.data['scores'] = scores

LDM = LeaderboardManager()

# ------------------------- Main Menu Scene -------------------------
class MainMenu(Scene):
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)

        def create_test_leader(username: str):
            from random import randint
            LDM.current_name = username
            LDM.add_score(randint(0, 10000))
            LDM.save()
            return False

        self.engine.add_function_to_live_inspector(
            'Create Random Leader', create_test_leader,
            [('user', str)], 'Create a random user for leaderboard'
        )

        self.setup_ui()

    def play(self):
        if self.nameinput_textbox.text == '' or LDM.current_name == '' or LDM.current_name == None:
            return
        self.engine.set_scene("game")   

    def setup_ui(self):
        self.add_ui_element(TextLabel(
            self.engine.width // 2, 100 * self.engine.ratio.y,
            'Flapyn', 72, (200, 170, 100), 'orbitron', pivot=(0.5, 0)
        ))

        play_button = Button(
            self.engine.width // 2, 250 * self.engine.ratio.y,
            200 * self.engine.ratio.x, 65 * self.engine.ratio.y,
            'Play', 50, 'orbitron', pivot=(0.5, 0)
        )
        play_button.set_on_click(self.play)
        self.add_ui_element(play_button)
        
        self.nameinput_textbox = TextBox(self.engine.width // 2 + 180 * self.engine.ratio.x, 275 * self.engine.ratio.y,
            120 * self.engine.ratio.x, 22 * self.engine.ratio.y, '', 20*self.engine.ratio.med, 'orbitron', pivot=(0.5, 0))
        self.nameinput_textbox.set_on_text_changed(LDM.set_username)
        self.add_ui_element(self.nameinput_textbox)

        exit_button = Button(
            self.engine.width // 2, 350 * self.engine.ratio.y,
            200 * self.engine.ratio.x, 50 * self.engine.ratio.y,
            'Quit', 50, 'orbitron', pivot=(0.5, 0)
        )
        exit_button.set_on_click(self.engine.shutdown)
        self.add_ui_element(exit_button)

        self.leaderboard_scrollingframe = ScrollingFrame(
            self.engine.width - 15 * self.engine.ratio.x,
            self.engine.height - 15 * self.engine.ratio.y,
            350 * self.engine.ratio.x, 400 * self.engine.ratio.y,
            350 * self.engine.ratio.x, 600 * self.engine.ratio.y,
            pivot=(1, 1)
        )
        self.score_table = Table(
            5 * self.engine.ratio.x, 5 * self.engine.ratio.y,
            320 * self.engine.ratio.x, 590 * self.engine.ratio.y,
            ['Name', 'Score', 'Date'], [], row_height=26 * self.engine.ratio.med
        )
        self.leaderboard_scrollingframe.add_child(self.score_table)
        self.add_ui_element(self.leaderboard_scrollingframe)

        self.order_by_dropdown = Dropdown(
            self.engine.width - 30 * self.engine.ratio.x,
            self.engine.height - 420 * self.engine.ratio.y,
            90 * self.engine.ratio.x, 26 * self.engine.ratio.y,
            ['Score', 'Date'], 22, 'orbitron', pivot=(1, 1)
        )
        self.order_by_dropdown.set_on_selection_changed(self.reload_leaderboard)
        self.add_ui_element(self.order_by_dropdown)

        self.reload_leaderboard()

    def reload_leaderboard(self, index: int = 0, _: str = ''):
        self.score_table.clear()
        scores: list = LDM.data.get('scores', [])
        if index == 0:
            scores.sort(key=lambda x: x['score'], reverse=True)
        elif index == 1:
            scores.sort(key=lambda x: x['date'], reverse=True)

        for score in scores:
            self.score_table.add_row([score['name'], str(score['score']), score['date']])
            
    def on_enter(self, previous_scene: str | None = None) -> None:
        self.reload_leaderboard()

    def render(self, renderer: OpenGLRenderer):
        renderer.fill_screen(ThemeManager.get_color('background'))

# ------------------------- Game Scene -------------------------
class Game(Scene):
    # --- Difficulty Tuning ---
    GRAVITY = 0.5
    FLAP_FORCE = -6.0
    PIPE_SPEED = 4
    PIPE_GAP = 180
    PIPE_WIDTH = 52
    PIPE_SPAWN_INTERVAL = 300
    BIRD_SIZE = 34
    CLOUD_SPEED = 0.5

    def __init__(self, engine):
        super().__init__(engine)

        

        pipes_ss = SpriteSheet(self.engine.atlas.get_item('pipes').path)
        # These return pygame.Surface objects
        self.pipe_sprites = {
            'bottom_pipe': pipes_ss.get_sprite_at_rect((0, 0, 32, 32)),
            'bottom_point': pipes_ss.get_sprite_at_rect((32, 0, 32, 32)),
            'top_point': pipes_ss.get_sprite_at_rect((64, 0, 32, 32)),
            'top_pipe': pipes_ss.get_sprite_at_rect((96, 0, 32, 32)),
        }

        self.clouds_ss = SpriteSheet(self.engine.atlas.get_item('clouds').path)
        self.cloud_sprites = self.clouds_ss.get_sprites_at_regions([
            (0, 0, 64, 32), (64, 0, 64, 32), (128, 0, 64, 32), (192, 0, 64, 32)
        ])
        
        self.bird_anim = Animation(self.engine.atlas.get_item('bird').path, (32, 32), (0,0), 4, scale=(self.engine.ratio.x, self.engine.ratio.y), duration=2)

        # ---------- Audio ----------
        self.audio_manager.load_sound(
            'music',
            self.engine.atlas.get_item("sounds").path / 'music.mp3',
            'music'
        )
        try:
            self.audio_manager.load_sound(
                'flap',
                self.engine.atlas.get_item("sounds").path / 'flap.wav',
                'sfx'
            )
            self.audio_manager.load_sound(
                'hit',
                self.engine.atlas.get_item("sounds").path / 'hit.wav',
                'sfx'
            )
        except:
            pass

        self.score = 0

        # ---------- UI ----------
        self.setup_ui()
        
        # ---------- Game state ----------
        self.reset_game()

    def reset_game(self):
        self.bird_x = 200
        self.bird_y = self.engine.height // 2
        self.bird_vel_y = 0
        self.bird_rotation = 0

        self.pipes = []
        self.score = 0
        self.game_over = False
        self.pipe_timer = 0
        self.cloud_offset = 0

        self.score_label.set_text(f'Score: {self.score}')
        self.game_over_ui.visible = False

    def setup_ui(self):
        self.score_label = TextLabel(
            self.engine.width // 2, 10 * self.engine.ratio.y,
            'Score: 0', 32, (200, 170, 100),
            'orbitron', pivot=(0.5, 0)
        )
        self.add_ui_element(self.score_label)

        self.game_over_ui = UiFrame(0, 0, self.engine.width, self.engine.height)
        self.game_over_ui.visible = False
        self.game_over_ui.set_background_color((0,0,0,150))

        self.game_over_ui.add_child(TextLabel(
            self.engine.width//2, self.engine.height//2 - 40 * self.engine.ratio.y,
            'Game Over', 48 * self.engine.ratio.med, font_name='orbitron', pivot=(0.5, 0.5)
        ))
        self.final_score_label = TextLabel(
            self.engine.width//2, self.engine.height//2 + 20 * self.engine.ratio.y,
            f'Final Score: {self.score}', 48 * self.engine.ratio.med, font_name='orbitron', pivot=(0.5, 0.5)
        )
        self.game_over_ui.add_child(self.final_score_label)

        restart_btn = Button(
            self.engine.width // 2, self.engine.height // 2 + 80 * self.engine.ratio.y,
            200, 60, 'Restart', 32, 'orbitron', pivot=(0.5, 0.5)
        )
        restart_btn.set_on_click(self.restart_game)
        self.game_over_ui.add_child(restart_btn)
        
        mainmenu_btn = Button(
            self.engine.width // 2, self.engine.height // 2 + 160 * self.engine.ratio.y,
            200, 60, 'Main Menu', 32, 'orbitron', pivot=(0.5, 0.5)
        )
        mainmenu_btn.set_on_click(lambda: self.engine.set_scene('main'))
        self.game_over_ui.add_child(mainmenu_btn)

        self.add_ui_element(self.game_over_ui)

    def restart_game(self):
        self.reset_game()
        self.pipe_timer = 0

    # ------------------------- Scene Lifecycle -------------------------
    def on_enter(self, previous_scene):
        self.audio_manager.play_music('music', echo=0.5, chorus=1)
        self.reset_game()

    def on_exit(self, next_scene):
        self.audio_manager.stop_all()

    def is_flapping(self) -> bool:
        keys = pg.key.get_pressed()
        return keys[pg.K_SPACE] or keys[pg.K_UP] or self.engine.input_state.mouse_buttons_pressed.left

    # ------------------------- Game Update -------------------------
    def update(self, dt):
        if self.game_over:
            return

        if self.is_flapping():
            self.bird_vel_y = self.FLAP_FORCE
            
        self.bird_vel_y += self.GRAVITY
        self.bird_y += self.bird_vel_y
        
        target_rot = max(-30, min(30, self.bird_vel_y * 3))
        self.bird_rotation += (target_rot - self.bird_rotation) * 0.1
        
        self.pipe_timer += self.PIPE_SPEED
        if self.pipe_timer > self.PIPE_SPAWN_INTERVAL:
            self.pipe_timer = 0
            min_gap = self.PIPE_GAP // 2 + 20
            max_gap = self.engine.height - self.PIPE_GAP // 2 - 20
            gap_y = random.randint(int(min_gap), int(max_gap))
            self.pipes.append({
                'x': self.engine.width + 50,
                'gap_y': gap_y,
                'scored': False
            })
            
        for pipe in self.pipes:
            pipe['x'] -= self.PIPE_SPEED
        # Remove off-screen pipes
        self.pipes = [p for p in self.pipes if p['x'] > -self.PIPE_WIDTH - 50]
        
        self.cloud_offset += self.CLOUD_SPEED
        if self.cloud_offset > self.engine.width:
            self.cloud_offset -= self.engine.width
        
        self.bird_anim.update()    
        if self.bird_y + self.BIRD_SIZE // 2 > self.engine.height:
            self.die()
            return
        
        if self.bird_y - self.BIRD_SIZE // 2 < 0:
            self.bird_y = self.BIRD_SIZE // 2
            self.bird_vel_y = 0
            
        # Pipe collisions
        for pipe in self.pipes:
            top_rect = self.get_pipe_rect(pipe, 'top')
            bottom_rect = self.get_pipe_rect(pipe, 'bottom')
            if self.rects_collide(self.bird_rect, top_rect) or self.rects_collide(self.bird_rect, bottom_rect):
                self.die()
                return
            
        for pipe in self.pipes:
            if not pipe['scored']:
                # Bird passes the pipe's left edge
                if self.bird_x + self.BIRD_SIZE // 2 > pipe['x'] + self.PIPE_WIDTH // 2:
                    pipe['scored'] = True
                    self.score += 1
                    self.score_label.set_text(f'Score: {self.score}')
        
    def get_pipe_rect(self, pipe, which):
        gap_y = pipe['gap_y']
        x = pipe['x'] - self.PIPE_WIDTH // 2
        if which == 'top':
            y = 0
            h = gap_y - self.PIPE_GAP // 2
        else:  # bottom
            y = gap_y + self.PIPE_GAP // 2
            h = self.engine.height - y
        return (x, y, int(self.PIPE_WIDTH * 0.9), int(h * 0.99))

    @staticmethod
    def rects_collide(a, b):
        return (a[0] < b[0] + b[2] and a[0] + a[2] > b[0] and
                a[1] < b[1] + b[3] and a[1] + a[3] > b[1])

    def die(self):
        if self.game_over:
            return
        self.game_over = True
        # self.audio_manager.play('hit')
        LDM.add_score(self.score)
        LDM.save()
        self.final_score_label.set_text(f'Final Score: {self.score}')
        self.game_over_ui.visible = True

    # ------------------------- Rendering -------------------------
    def render(self, renderer: OpenGLRenderer):
        # Background sky
        renderer.fill_screen((150, 170, 225))

        # Draw clouds
        for i, cloud in enumerate(self.cloud_sprites):
            x = (i * 300 + 50) % self.engine.width
            y = 50 + i * 30
            scaled = pg.transform.scale(cloud, (int(64 * 1.5 * self.engine.ratio.x), int(32 * 1.5 * self.engine.ratio.y)))
            renderer.blit(scaled, (int(x), int(y)))

        # Draw pipes
        for pipe in self.pipes:
            gap_y = pipe['gap_y']
            x = pipe['x']
            top_height = gap_y - self.PIPE_GAP // 2
            if top_height > 0:
                self.draw_pipe_segment(renderer, x, 0, self.PIPE_WIDTH, top_height, 'top')
                if self.engine.debug_enabled:
                    renderer.draw_rect(x, 0, self.PIPE_WIDTH, top_height, (255, 0, 0,128))
            bottom_y = gap_y + self.PIPE_GAP // 2
            bottom_height = self.engine.height - bottom_y
            if bottom_height > 0:
                self.draw_pipe_segment(renderer, x, bottom_y, self.PIPE_WIDTH, bottom_height, 'bottom')
                if self.engine.debug_enabled:
                    renderer.draw_rect(x, bottom_y, self.PIPE_WIDTH, bottom_height, (255, 0, 0, 128))

        # Draw bird (with rotation)
        bird_surf = self.bird_anim.get_current_frame()
        rotated = pg.transform.rotate(bird_surf, self.bird_rotation)
        self.bird_rect = rotated.get_rect(center=(self.bird_x, self.bird_y))
        renderer.blit(rotated, self.bird_rect)
        if self.engine.debug_enabled:
            renderer.draw_rect(self.bird_x - self.BIRD_SIZE // 2, self.bird_y - self.BIRD_SIZE // 2,
                               self.BIRD_SIZE, self.BIRD_SIZE, (0, 255, 0, 128))

    def draw_pipe_segment(self, renderer, x, y, w, h, orientation):
        """Draw a pipe segment by tiling the body sprite."""
        if orientation == 'top':
            body = self.pipe_sprites['top_pipe']
            cap = self.pipe_sprites['top_point']
        else:
            body = self.pipe_sprites['bottom_pipe']
            cap = self.pipe_sprites['bottom_point']

        body_scaled = pg.transform.scale(body, (int(w), int(h)))
        renderer.blit(body_scaled, (int(x), int(y)))

        # Draw cap at the end
        if orientation == 'top':
            cap_y = y + h - 32
        else:
            cap_y = y
        cap_scaled = pg.transform.scale(cap, (int(w), 32))
        renderer.blit(cap_scaled, (int(x), int(cap_y)))

# ------------------------- Main Application -------------------------
def main():
    args = parser.parse_args(sys.argv[1:])

    engine = LunaEngine("Flapyn", 1280, 720, fullscreen=args.fullscreen, debug=args.debug)
    root_path = Path(os.path.abspath(os.path.dirname(__file__)))
    engine.set_global_theme(ThemeType.CLOUDS)

    engine.atlas.add_folder("root", root_path)
    engine.atlas.add_folder("assets", root_path / "assets")
    engine.atlas.add_folder("textures", root_path / "assets" / "textures")
    engine.atlas.add_folder("fonts", root_path / "assets" / "fonts")
    engine.atlas.add_folder("sounds", root_path / "assets" / "sounds")

    # Fonts
    engine.atlas.add_font("dotgothic", engine.atlas.get_item("fonts").path / 'DotGothic16.ttf')
    engine.atlas.add_font("orbitron", engine.atlas.get_item("fonts").path / 'Orbitron.ttf')

    # Textures
    engine.atlas.add_texture("pipes", engine.atlas.get_item("textures").path / 'pipes.png')
    engine.atlas.add_texture("clouds", engine.atlas.get_item("textures").path / 'clouds.png')
    engine.atlas.add_texture("bird", engine.atlas.get_item("textures").path / 'bird.png')

    engine.set_icon(str(engine.atlas.get_item("textures").path / 'icon.png'))
    engine.updateRatio(1280, 720)

    engine.add_scene("main", MainMenu)
    engine.add_scene("game", Game)
    engine.set_scene("main")

    engine.run()

if __name__ == '__main__':
    main()