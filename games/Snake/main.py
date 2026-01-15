import sys
import os
import random
import json
from datetime import datetime

from lunaengine.core import Scene, LunaEngine, Renderer
from lunaengine.ui import *
import pygame

class Leaderboard:
    def __init__(self, filename="snake_leaderboard.json"):
        self.filename = filename
        self.scores = self.load_scores()
        
    def load_scores(self):
        try:
            if os.path.exists(f'{os.path.dirname(__file__)}/'+self.filename):
                with open(f'{os.path.dirname(__file__)}/'+self.filename, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return []
    
    def save_scores(self):
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.scores, f, indent=2)
        except Exception:
            pass
    
    def add_score(self, name, score):
        self.scores.append({
            "name": name,
            "score": score,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        self.scores.sort(key=lambda x: x["score"], reverse=True)
        self.save_scores()
    
    def get_top_scores(self, count=10):
        return self.scores[:count]

class ResponsiveUI:
    @staticmethod
    def get_ratio(engine):
        return pygame.math.Vector2(engine.width/1024, engine.height/720)
    
    @staticmethod
    def scale_position(x, y, ratio):
        return (int(x * ratio.x), int(y * ratio.y))
    
    @staticmethod
    def scale_size(width, height, ratio):
        return (int(width * ratio.x), int(height * ratio.y))
    
    @staticmethod
    def scale_font_size(base_size, ratio):
        avg_ratio = (ratio.x + ratio.y) / 2
        return int(base_size * avg_ratio)

class MainMenuScene(Scene):
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        self.leaderboard = Leaderboard()
        self.snake_color = (0, 255, 0)
        self.ratio = ResponsiveUI.get_ratio(engine)
        
    def on_enter(self, previous_scene=None):
        self.clear_ui_elements()
        self.setup_ui()
        ThemeManager.set_current_theme(ThemeType.EMERALD)
        self.engine._update_all_ui_themes(ThemeManager.get_current_theme())
        return super().on_enter(previous_scene)
    
    def setup_ui(self):
        title_x, title_y = ResponsiveUI.scale_position(512, 80, self.ratio)
        title_font = ResponsiveUI.scale_font_size(72, self.ratio)
        Ui_TitleLabel = TextLabel(title_x, title_y, "SNAKE GAME", title_font, 
                                root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        self.add_ui_element(Ui_TitleLabel)
        
        play_x, play_y = ResponsiveUI.scale_position(512, 200, self.ratio)
        play_w, play_h = ResponsiveUI.scale_size(220, 50, self.ratio)
        play_font = ResponsiveUI.scale_font_size(36, self.ratio)
        Ui_PlayButton = Button(play_x, play_y, play_w, play_h, "PLAY GAME", play_font, 
                              root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        Ui_PlayButton.set_on_click(lambda: self.engine.set_scene("InGame"))
        self.add_ui_element(Ui_PlayButton)
        
        leader_x, leader_y = ResponsiveUI.scale_position(512, 270, self.ratio)
        leader_w, leader_h = ResponsiveUI.scale_size(220, 50, self.ratio)
        leader_font = ResponsiveUI.scale_font_size(36, self.ratio)
        Ui_LeaderboardButton = Button(leader_x, leader_y, leader_w, leader_h, "LEADERBOARD", leader_font,
                                     root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        Ui_LeaderboardButton.set_on_click(lambda: self.engine.set_scene("Leaderboard"))
        self.add_ui_element(Ui_LeaderboardButton)
        
        exit_x, exit_y = ResponsiveUI.scale_position(512, 340, self.ratio)
        exit_w, exit_h = ResponsiveUI.scale_size(220, 50, self.ratio)
        exit_font = ResponsiveUI.scale_font_size(36, self.ratio)
        Ui_ExitButton = Button(exit_x, exit_y, exit_w, exit_h, "EXIT", exit_font,
                              root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        Ui_ExitButton.set_on_click(lambda: setattr(self.engine, 'running', False))
        self.add_ui_element(Ui_ExitButton)
        
        theme_x, theme_y = ResponsiveUI.scale_position(512, 410, self.ratio)
        theme_w, theme_h = ResponsiveUI.scale_size(200, 35, self.ratio)
        theme_font = ResponsiveUI.scale_font_size(20, self.ratio)
        Ui_ThemeLabel = TextLabel(theme_x, theme_y - 30, "THEME", 24,
                                root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        self.add_ui_element(Ui_ThemeLabel)
        
        Ui_ThemeDropdown = Dropdown(theme_x, theme_y, theme_w, theme_h, 
                                   self.engine.get_theme_names(), theme_font,
                                   root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        Ui_ThemeDropdown.set_on_selection_changed(lambda i, n: self.engine.set_global_theme(ThemeManager.get_theme_type_by_name(n)))
        self.add_ui_element(Ui_ThemeDropdown)
        
        color_x, color_y = ResponsiveUI.scale_position(512, 480, self.ratio)
        color_font = ResponsiveUI.scale_font_size(24, self.ratio)
        Ui_ColorLabel = TextLabel(color_x, color_y, "SNAKE COLOR", color_font,
                                 root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        self.add_ui_element(Ui_ColorLabel)
        
        slider_x = 350 * self.ratio.x
        slider_y_start = 520 * self.ratio.y
        slider_spacing = 40 * self.ratio.y
        
        Ui_RedLabel = TextLabel(slider_x, slider_y_start, "RED", 20,
                               root_point=(0, 0.5), theme=ThemeManager.get_current_theme())
        self.add_ui_element(Ui_RedLabel)
        
        self.Ui_RedSlider = Slider(slider_x + 80 * self.ratio.x, slider_y_start, 
                                  150 * self.ratio.x, 20 * self.ratio.y,
                                  0, 255, self.snake_color[0],
                                  root_point=(0, 0.5), theme=ThemeManager.get_current_theme())
        self.Ui_RedSlider.on_value_changed = lambda v: self.update_snake_color(0, int(v))
        self.add_ui_element(self.Ui_RedSlider)
        
        Ui_GreenLabel = TextLabel(slider_x, slider_y_start + slider_spacing, "GREEN", 20,
                                 root_point=(0, 0.5), theme=ThemeManager.get_current_theme())
        self.add_ui_element(Ui_GreenLabel)
        
        self.Ui_GreenSlider = Slider(slider_x + 80 * self.ratio.x, slider_y_start + slider_spacing,
                                    150 * self.ratio.x, 20 * self.ratio.y,
                                    0, 255, self.snake_color[1],
                                    root_point=(0, 0.5), theme=ThemeManager.get_current_theme())
        self.Ui_GreenSlider.on_value_changed = lambda v: self.update_snake_color(1, int(v))
        self.add_ui_element(self.Ui_GreenSlider)
        
        Ui_BlueLabel = TextLabel(slider_x, slider_y_start + slider_spacing * 2, "BLUE", 20,
                                root_point=(0, 0.5), theme=ThemeManager.get_current_theme())
        self.add_ui_element(Ui_BlueLabel)
        
        self.Ui_BlueSlider = Slider(slider_x + 80 * self.ratio.x, slider_y_start + slider_spacing * 2,
                                   150 * self.ratio.x, 20 * self.ratio.y,
                                   0, 255, self.snake_color[2],
                                   root_point=(0, 0.5), theme=ThemeManager.get_current_theme())
        self.Ui_BlueSlider.on_value_changed = lambda v: self.update_snake_color(2, int(v))
        self.add_ui_element(self.Ui_BlueSlider)
        
        preview_x, preview_y = ResponsiveUI.scale_position(650, 540, self.ratio)
        preview_w, preview_h = ResponsiveUI.scale_size(80, 80, self.ratio)
        self.preview_rect = pygame.Rect(preview_x, preview_y, preview_w, preview_h)

    def update_snake_color(self, channel: int, value: int):
        new_color = list(self.snake_color)
        new_color[channel] = value
        self.snake_color = tuple(new_color)
        
    def update(self, dt):
        self.ratio = ResponsiveUI.get_ratio(self.engine)
            
    def render(self, renderer:Renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))
        
        preview_x, preview_y = ResponsiveUI.scale_position(650, 540, self.ratio)
        preview_w, preview_h = ResponsiveUI.scale_size(80, 80, self.ratio)
        self.preview_rect = pygame.Rect(preview_x, preview_y, preview_w, preview_h)
        
        renderer.draw_rect(self.preview_rect.x, self.preview_rect.y, 
                          self.preview_rect.width, self.preview_rect.height, 
                          (50, 50, 50))
        renderer.draw_rect(self.preview_rect.x + 2, self.preview_rect.y + 2,
                          self.preview_rect.width - 4, self.preview_rect.height - 4,
                          self.snake_color)

class LeaderboardScene(Scene):
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        self.leaderboard = Leaderboard()
        self.ratio = ResponsiveUI.get_ratio(engine)
        self.scroll_frame = None
        
    def on_enter(self, previous_scene=None):
        self.engine.set_global_theme(ThemeType.DEEP_SPACE)
        self.clear_ui_elements()
        self.setup_ui()
        self.update_leaderboard_display()
        return super().on_enter(previous_scene)
    
    def setup_ui(self):
        title_x, title_y = ResponsiveUI.scale_position(512, 80, self.ratio)
        title_font = ResponsiveUI.scale_font_size(64, self.ratio)
        Ui_TitleLabel = TextLabel(title_x, title_y, "LEADERBOARD", title_font,
                                 root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        self.add_ui_element(Ui_TitleLabel)
        
        frame_x, frame_y = ResponsiveUI.scale_position(512, 350, self.ratio)
        frame_w, frame_h = ResponsiveUI.scale_size(800, 450, self.ratio)
        content_w, content_h = ResponsiveUI.scale_size(780, 800, self.ratio)
        
        self.scroll_frame = ScrollingFrame(int(frame_x), int(frame_y), int(frame_w), int(frame_h), 
                                         int(content_w), int(content_h),
                                         root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        self.add_ui_element(self.scroll_frame)
        
        back_x, back_y = ResponsiveUI.scale_position(512, 650, self.ratio)
        back_w, back_h = ResponsiveUI.scale_size(200, 50, self.ratio)
        back_font = ResponsiveUI.scale_font_size(36, self.ratio)
        Ui_BackButton = Button(back_x, back_y, back_w, back_h, "BACK", back_font,
                              root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        Ui_BackButton.set_on_click(lambda: self.engine.set_scene("MainMenu"))
        self.add_ui_element(Ui_BackButton)
    
    def update_leaderboard_display(self):
        if not self.scroll_frame:
            return
            
        self.scroll_frame.clear_children()
        
        top_scores = self.leaderboard.get_top_scores(10)
        
        if not top_scores:
            no_scores_label = TextLabel(400, 200, "No scores yet! Play the game!", 32,
                                      root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
            self.scroll_frame.add_child(no_scores_label)
            return
        
        entry_height = 60
        content_height = len(top_scores) * entry_height
        self.scroll_frame.content_height = max(content_height, 450)
        
        for i, score_data in enumerate(top_scores):
            y_pos = i * entry_height + 30
            
            rank_text = f"#{i+1} {score_data['name']}"
            rank_label = TextLabel(50, y_pos, rank_text, 28,
                                 root_point=(0, 0.5), theme=ThemeManager.get_current_theme())
            self.scroll_frame.add_child(rank_label)
            
            score_text = f"{score_data['score']} pts"
            score_label = TextLabel(350, y_pos, score_text, 28,
                                  root_point=(0, 0.5), theme=ThemeManager.get_current_theme())
            self.scroll_frame.add_child(score_label)
            
            date_text = score_data['date']
            date_label = TextLabel(550, y_pos, date_text, 20,
                                 root_point=(0, 0.5), theme=ThemeManager.get_current_theme())
            self.scroll_frame.add_child(date_label)
    
    def update(self, dt):
        self.ratio = ResponsiveUI.get_ratio(self.engine)
        self.update_leaderboard_display()
    
    def render(self, renderer: Renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))

class NameInputScene(Scene):
    def __init__(self, engine: LunaEngine, score):
        super().__init__(engine)
        self.score = score
        self.ratio = ResponsiveUI.get_ratio(engine)
        
    def on_enter(self, previous_scene=None):
        self.engine.set_global_theme(ThemeType.BUILDER)
        self.clear_ui_elements()
        self.setup_ui()
        return super().on_enter(previous_scene)
    
    def setup_ui(self):
        title_x, title_y = ResponsiveUI.scale_position(512, 200, self.ratio)
        title_font = ResponsiveUI.scale_font_size(48, self.ratio)
        Ui_TitleLabel = TextLabel(title_x, title_y, "NEW HIGH SCORE!", title_font,
                                 root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        self.add_ui_element(Ui_TitleLabel)
        
        score_x, score_y = ResponsiveUI.scale_position(512, 260, self.ratio)
        score_font = ResponsiveUI.scale_font_size(36, self.ratio)
        Ui_ScoreLabel = TextLabel(score_x, score_y, f"Score: {self.score}", score_font,
                                 root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        self.add_ui_element(Ui_ScoreLabel)
        
        name_x, name_y = ResponsiveUI.scale_position(512, 330, self.ratio)
        name_font = ResponsiveUI.scale_font_size(32, self.ratio)
        Ui_NameLabel = TextLabel(name_x, name_y, "ENTER YOUR NAME:", name_font,
                                root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        self.add_ui_element(Ui_NameLabel)
        
        input_x, input_y = ResponsiveUI.scale_position(512, 380, self.ratio)
        input_w, input_h = ResponsiveUI.scale_size(300, 50, self.ratio)
        self.name_input = TextBox(input_x, input_y, input_w, input_h, "", 
                                   ResponsiveUI.scale_font_size(32, self.ratio),
                                   root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        self.add_ui_element(self.name_input)
        
        submit_x, submit_y = ResponsiveUI.scale_position(512, 460, self.ratio)
        submit_w, submit_h = ResponsiveUI.scale_size(200, 50, self.ratio)
        submit_font = ResponsiveUI.scale_font_size(36, self.ratio)
        Ui_SubmitButton = Button(submit_x, submit_y, submit_w, submit_h, "SAVE", submit_font,
                                root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        Ui_SubmitButton.set_on_click(self.save_score)
        self.add_ui_element(Ui_SubmitButton)
    
    def save_score(self):
        name = self.name_input.text.strip()
        if not name:
            name = "Anonymous"
        
        leaderboard = Leaderboard()
        leaderboard.add_score(name, self.score)
        self.engine.set_scene("Leaderboard")
    
    def update(self, dt):
        self.ratio = ResponsiveUI.get_ratio(self.engine)
        self.name_input.update(dt)
    
    def render(self, renderer: Renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))

class InGameScene(Scene):
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        self.ratio = ResponsiveUI.get_ratio(engine)
        
    def on_enter(self, previous_scene=None):
        self.engine.set_global_theme(ThemeType.EMERALD)
        self.clear_ui_elements()
        
        if "MainMenu" in self.engine.scenes:
            main_menu = self.engine.scenes["MainMenu"]
            self.snake_color = main_menu.snake_color
        else:
            self.snake_color = (0, 255, 0)
        
        self.reset_game()
        self.setup_ui()
        
        @self.engine.on_event(pygame.KEYDOWN)
        def on_key_press(event):
            self.handle_key_press(event.key)
            
        return super().on_enter(previous_scene)
    
    def reset_game(self):
        self.cell_size = int(40 * self.ratio.x)
        self.grid_width = int(self.engine.width // self.cell_size)
        self.grid_height = int(self.engine.height // self.cell_size)
        
        self.snake = [
            (self.grid_width // 2, self.grid_height // 2),
            (self.grid_width // 2 - 1, self.grid_height // 2),
            (self.grid_width // 2 - 2, self.grid_height // 2)
        ]
        self.direction = (1, 0)
        self.next_direction = self.direction
        
        self.score = 0
        self.game_over = False
        self.base_speed = 5
        self.speed = self.base_speed
        self.move_timer = 0
        self.apples_eaten = 0
        
        self.special_apple = None
        self.special_apple_timer = 0
        self.special_apple_duration = 10.0
        
        self.spawn_apple()
    
    def setup_ui(self):
        score_x, score_y = ResponsiveUI.scale_position(20, 20, self.ratio)
        score_font = ResponsiveUI.scale_font_size(28, self.ratio)
        self.Ui_ScoreLabel = TextLabel(score_x, score_y, f"SCORE: {self.score}", score_font,
                                      root_point=(0, 0), theme=ThemeManager.get_current_theme())
        self.add_ui_element(self.Ui_ScoreLabel)
        
        info_x, info_y = ResponsiveUI.scale_position(20, 50, self.ratio)
        info_font = ResponsiveUI.scale_font_size(18, self.ratio)
        self.Ui_InfoLabel = TextLabel(info_x, info_y, "WASD/ARROWS TO MOVE | ESC TO MENU", info_font,
                                     root_point=(0, 0), theme=ThemeManager.get_current_theme())
        self.add_ui_element(self.Ui_InfoLabel)
    
    def spawn_apple(self):
        while True:
            apple_pos = (
                random.randint(0, self.grid_width - 1),
                random.randint(0, self.grid_height - 1)
            )
            if apple_pos not in self.snake and apple_pos != self.special_apple:
                self.apple = apple_pos
                break
    
    def spawn_special_apple(self):
        if self.special_apple is None and random.random() < 0.3:
            while True:
                special_pos = (
                    random.randint(0, self.grid_width - 1),
                    random.randint(0, self.grid_height - 1)
                )
                if (special_pos not in self.snake and 
                    special_pos != self.apple):
                    self.special_apple = special_pos
                    self.special_apple_timer = 0
                    break
    
    def handle_key_press(self, key):
        if key == pygame.K_ESCAPE:
            self.engine.set_scene("MainMenu")
            return
        
        if self.game_over:
            if key == pygame.K_SPACE:
                self.reset_game()
            return
        
        if key in [pygame.K_RIGHT, pygame.K_d] and self.direction != (-1, 0):
            self.next_direction = (1, 0)
        elif key in [pygame.K_LEFT, pygame.K_a] and self.direction != (1, 0):
            self.next_direction = (-1, 0)
        elif key in [pygame.K_DOWN, pygame.K_s] and self.direction != (0, -1):
            self.next_direction = (0, 1)
        elif key in [pygame.K_UP, pygame.K_w] and self.direction != (0, 1):
            self.next_direction = (0, -1)
    
    def update_snake(self):
        self.direction = self.next_direction
        
        head_x, head_y = self.snake[0]
        new_head_x = (head_x + self.direction[0]) % self.grid_width
        new_head_y = (head_y + self.direction[1]) % self.grid_height
        new_head = (new_head_x, new_head_y)
        
        if new_head in self.snake:
            self.game_over = True
            self.check_high_score()
            return
        
        self.snake.insert(0, new_head)
        
        if new_head == self.apple:
            self.score += 10
            self.apples_eaten += 1
            self.spawn_apple()
            
            if self.apples_eaten % 5 == 0:
                self.speed = min(12, self.speed + 0.5)
                
            self.spawn_special_apple()
                
        elif self.special_apple and new_head == self.special_apple:
            self.score += 50
            self.special_apple = None
            
        else:
            self.snake.pop()
    
    def check_high_score(self):
        leaderboard = Leaderboard()
        top_scores = leaderboard.get_top_scores(10)
        
        if len(top_scores) < 10 or self.score > top_scores[-1]["score"]:
            self.engine.add_scene("NameInput", NameInputScene(self.engine, self.score))
            self.engine.set_scene("NameInput")
    
    def update(self, dt):
        if self.game_over:
            return
            
        self.ratio = ResponsiveUI.get_ratio(self.engine)
        
        self.move_timer += dt
        move_interval = 0.65 / self.speed
        
        if self.move_timer >= move_interval:
            self.update_snake()
            self.move_timer = 0
        
        if self.special_apple:
            self.special_apple_timer += dt
            if self.special_apple_timer >= self.special_apple_duration:
                self.special_apple = None
        
        if "MainMenu" in self.engine.scenes:
            main_menu = self.engine.scenes["MainMenu"]
            self.snake_color = main_menu.snake_color
        
        self.Ui_ScoreLabel.set_text(f"SCORE: {self.score}")
    
    def render(self, renderer: Renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))
        
        grid_color = tuple(max(0, c - 15) for c in ThemeManager.get_color('background2'))
        for x in range(0, self.engine.width, self.cell_size):
            renderer.draw_line(x, 0, x, self.engine.height, grid_color)
        for y in range(0, self.engine.height, self.cell_size):
            renderer.draw_line(0, y, self.engine.width, y, grid_color)
        
        apple_x = self.apple[0] * self.cell_size
        apple_y = self.apple[1] * self.cell_size
        renderer.draw_rect(apple_x, apple_y, self.cell_size, self.cell_size, (255, 0, 0))
        
        if self.special_apple:
            special_x = self.special_apple[0] * self.cell_size
            special_y = self.special_apple[1] * self.cell_size
            
            pulse = (abs(pygame.time.get_ticks() % 1000 - 500) / 500.0) * 55
            golden_color = (255, 215 + pulse, 0)
            renderer.draw_rect(special_x, special_y, self.cell_size, self.cell_size, golden_color)
            
            time_left = 1.0 - (self.special_apple_timer / self.special_apple_duration)
            bar_width = int(self.cell_size * time_left)
            renderer.draw_rect(special_x, special_y - 5, bar_width, 3, (255, 255, 255))
        
        for i, (x, y) in enumerate(self.snake):
            segment_x = x * self.cell_size
            segment_y = y * self.cell_size
            
            if i == 0:
                head_color = tuple(min(255, c + 40) for c in self.snake_color)
                color = head_color
                eye_size = self.cell_size // 5
                if self.direction == (1, 0):
                    renderer.draw_rect(segment_x + self.cell_size - eye_size, segment_y + eye_size, eye_size, eye_size, (0, 0, 0))
                    renderer.draw_rect(segment_x + self.cell_size - eye_size, segment_y + self.cell_size - eye_size*2, eye_size, eye_size, (0, 0, 0))
                elif self.direction == (-1, 0):
                    renderer.draw_rect(segment_x, segment_y + eye_size, eye_size, eye_size, (0, 0, 0))
                    renderer.draw_rect(segment_x, segment_y + self.cell_size - eye_size*2, eye_size, eye_size, (0, 0, 0))
                elif self.direction == (0, 1):
                    renderer.draw_rect(segment_x + eye_size, segment_y + self.cell_size - eye_size, eye_size, eye_size, (0, 0, 0))
                    renderer.draw_rect(segment_x + self.cell_size - eye_size*2, segment_y + self.cell_size - eye_size, eye_size, eye_size, (0, 0, 0))
                elif self.direction == (0, -1):
                    renderer.draw_rect(segment_x + eye_size, segment_y, eye_size, eye_size, (0, 0, 0))
                    renderer.draw_rect(segment_x + self.cell_size - eye_size*2, segment_y, eye_size, eye_size, (0, 0, 0))
            else:
                darken_factor = min(80, i * 6)
                color = tuple(max(0, c - darken_factor) for c in self.snake_color)
            
            renderer.draw_rect(segment_x, segment_y, self.cell_size, self.cell_size, color)
            
            border_color = tuple(max(0, c - 30) for c in color)
            renderer.draw_rect(segment_x, segment_y, self.cell_size, self.cell_size, border_color, fill=False)
        
        if self.game_over:
            overlay = pygame.Surface((self.engine.width, self.engine.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            renderer.blit(overlay, (0, 0))
            
            game_over_font = ResponsiveUI.scale_font_size(72, self.ratio)
            score_font = ResponsiveUI.scale_font_size(48, self.ratio)
            restart_font = ResponsiveUI.scale_font_size(36, self.ratio)
            
            game_over_x, game_over_y = ResponsiveUI.scale_position(512, 280, self.ratio)
            score_x, score_y = ResponsiveUI.scale_position(512, 360, self.ratio)
            restart_x, restart_y = ResponsiveUI.scale_position(512, 420, self.ratio)
            menu_x, menu_y = ResponsiveUI.scale_position(512, 480, self.ratio)
            
            game_over_text = "GAME OVER"
            game_over_surface = FontManager.get_font(None, game_over_font).render(game_over_text, True, (255, 255, 255))
            renderer.blit(game_over_surface, (game_over_x - game_over_surface.get_width()//2, game_over_y - game_over_surface.get_height()//2))
            
            score_text = f"Final Score: {self.score}"
            score_surface = FontManager.get_font(None, score_font).render(score_text, True, (255, 255, 255))
            renderer.blit(score_surface, (score_x - score_surface.get_width()//2, score_y - score_surface.get_height()//2))
            
            restart_text = "Press SPACE to restart"
            restart_surface = FontManager.get_font(None, restart_font).render(restart_text, True, (255, 255, 255))
            renderer.blit(restart_surface, (restart_x - restart_surface.get_width()//2, restart_y - restart_surface.get_height()//2))
            
            menu_text = "Press ESC for menu"
            menu_surface = FontManager.get_font(None, restart_font).render(menu_text, True, (200, 200, 200))
            renderer.blit(menu_surface, (menu_x - menu_surface.get_width()//2, menu_y - menu_surface.get_height()//2))

def main():
    try:
        engine = LunaEngine("Snake Game", 1024, 720)
        pygame.display.set_icon(pygame.image.load(f"{os.path.dirname(__file__)}/icon.png"))
        engine.initialize()
        
        engine.add_scene("MainMenu", MainMenuScene)
        engine.add_scene("InGame", InGameScene)
        engine.add_scene("Leaderboard", LeaderboardScene)
        
        engine.set_scene("MainMenu")
        
        engine.run()
        
    except Exception as e:
        print(f"Error running game: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()