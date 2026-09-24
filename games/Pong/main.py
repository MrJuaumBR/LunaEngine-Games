"""
Pong Game - LunaEngine Implementation
Classic arcade Pong with multiplayer and AI opponent options
"""

import sys, os, random, json, pygame
from datetime import datetime
from typing import Tuple, Optional
from enum import Enum

from lunaengine.core import Scene, LunaEngine, Renderer
from lunaengine.ui import *

class GameMode(Enum):
    PLAYER_VS_AI = 0
    PLAYER_VS_PLAYER = 1
    AI_VS_AI = 2

class LeaderboardPong:
    """Leaderboard handler for Pong game"""
    
    def __init__(self, filename: str = "pong_leaderboard.json"):
        self.filename = filename
        self.scores = self.load_scores()
    
    def load_scores(self) -> list:
        """Load scores from JSON file"""
        try:
            if os.path.exists(f'{os.path.dirname(__file__)}/'+self.filename):
                with open(f'{os.path.dirname(__file__)}/'+self.filename, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading leaderboard: {e}")
        return []
    
    def save_scores(self):
        """Save scores to JSON file"""
        try:
            with open(f'{os.path.dirname(__file__)}/'+self.filename, 'w') as f:
                json.dump(self.scores, f, indent=2)
        except Exception as e:
            print(f"Error saving leaderboard: {e}")
    
    def add_score(self, player1_name: str, player2_name: str, 
                  player1_score: int, player2_score: int, 
                  winner: str, duration: int):
        """Add a new score to the leaderboard"""
        self.scores.append({
            "player1": player1_name,
            "player2": player2_name,
            "score1": player1_score,
            "score2": player2_score,
            "winner": winner,
            "duration": duration,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        self.scores = self.scores[:50]  # Keep only top 50
        self.save_scores()
    
    def get_top_scores(self, count: int = 20) -> list:
        """Get top N scores"""
        return self.scores[:count]

class Paddle:
    """Paddle class for Pong game"""
    
    def __init__(self, x: int, y: int, width: int = 15, height: int = 100, speed: int = 5):
        self.rect = pygame.Rect(x, y, width, height)
        self.width = width
        self.height = height
        self.speed = speed
        self.score = 0
        self.ai_difficulty = 0.8  # 0-1, higher is harder
    
    def move(self, direction: int, screen_height: int):
        """Move paddle up (-1) or down (1)"""
        self.rect.y += direction * self.speed
        self.rect.y = max(0, min(self.rect.y, screen_height - self.height))
    
    def ai_move(self, ball_rect: pygame.Rect, screen_height: int):
        """AI movement logic"""
        # Calculate where the ball will be
        paddle_center = self.rect.centery
        ball_center = ball_rect.centery
        
        # Add some imperfection based on difficulty
        error = random.uniform(-20 * (1 - self.ai_difficulty), 20 * (1 - self.ai_difficulty))
        target_y = ball_center + error
        
        # Move towards target
        if abs(paddle_center - target_y) > self.speed:
            if paddle_center < target_y:
                self.move(1, screen_height)
            else:
                self.move(-1, screen_height)
        elif abs(paddle_center - target_y) > 2:
            # Fine adjustment
            if paddle_center < target_y:
                self.rect.y += 1
            else:
                self.rect.y -= 1
    
    def reset(self, x: int, y: int):
        """Reset paddle position"""
        self.rect.x = x
        self.rect.y = y
        self.score = 0

class Ball:
    """Ball class for Pong game"""
    
    def __init__(self, x: int, y: int, radius: int = 10, speed: int = 4):
        self.rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)
        self.radius = radius
        self.speed = speed
        self.vx = speed
        self.vy = random.choice([-speed, speed])
        self.speed_increment = 0.1  # Speed increase per bounce
        self.max_speed = 10
    
    def move(self):
        """Move the ball"""
        self.rect.x += self.vx
        self.rect.y += self.vy
    
    def reset(self, screen_width: int, screen_height: int):
        """Reset ball to center"""
        self.rect.center = (screen_width // 2, screen_height // 2)
        self.vx = self.speed * random.choice([-1, 1])
        self.vy = random.choice([-self.speed, self.speed])
    
    def bounce_paddle(self, paddle: Paddle):
        """Bounce off paddle with angle based on hit position"""
        # Calculate hit position relative to paddle center
        relative_y = (paddle.rect.centery - self.rect.centery) / (paddle.height / 2)
        
        # Set angle based on hit position
        angle = relative_y * 0.7  # Max 70 degree angle
        
        # Reverse horizontal direction and adjust vertical
        self.vx = -self.vx
        self.vy = -angle * self.speed
        
        # Increase speed slightly
        if abs(self.vx) < self.max_speed:
            self.vx *= 1 + self.speed_increment
            self.vy *= 1 + self.speed_increment
    
    def bounce_wall(self):
        """Bounce off top/bottom walls"""
        self.vy = -self.vy
    
    def check_score(self, screen_width: int) -> Optional[int]:
        """Check if ball scored, return player number (1 or 2) or None"""
        if self.rect.left <= 0:
            return 2  # Player 2 scores
        elif self.rect.right >= screen_width:
            return 1  # Player 1 scores
        return None

class ResponsiveUIPong:
    """Responsive UI helper for Pong"""
    
    @staticmethod
    def get_ratio(engine) -> pygame.math.Vector2:
        return pygame.math.Vector2(engine.width/1024, engine.height/768)
    
    @staticmethod
    def scale_position(x: float, y: float, ratio: pygame.math.Vector2) -> Tuple[int, int]:
        return (int(x * ratio.x), int(y * ratio.y))
    
    @staticmethod
    def scale_size(width: float, height: float, ratio: pygame.math.Vector2) -> Tuple[int, int]:
        return (int(width * ratio.x), int(height * ratio.y))
    
    @staticmethod
    def scale_font_size(base_size: int, ratio: pygame.math.Vector2) -> int:
        avg_ratio = (ratio.x + ratio.y) / 2
        return int(base_size * avg_ratio)

class MainMenuPong(Scene):
    """Pong Main Menu Scene"""
    
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        self.leaderboard = LeaderboardPong()
        self.ratio = ResponsiveUIPong.get_ratio(engine)
        self.game_mode = GameMode.PLAYER_VS_AI
        self.ai_difficulty = 2  # 0-2: Easy, Medium, Hard
        self.winning_score = 5
    
    def on_enter(self, previous_scene: str = None):
        self.clear_ui_elements()
        self.setup_ui()
        ThemeManager.set_current_theme(ThemeType.MATRIX)
        self.engine._update_all_ui_themes(ThemeManager.get_current_theme())
        return super().on_enter(previous_scene)
    
    def setup_ui(self):
        """Setup main menu UI"""
        title_x, title_y = ResponsiveUIPong.scale_position(512, 80, self.ratio)
        title_font = ResponsiveUIPong.scale_font_size(86, self.ratio)
        title = TextLabel(title_x, title_y, "CLASSIC PONG", title_font, 
                         pivot=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        self.add_ui_element(title)
        
        # Game mode selection
        mode_x, mode_y = ResponsiveUIPong.scale_position(512, 180, self.ratio)
        mode_font = ResponsiveUIPong.scale_font_size(36, self.ratio)
        mode_label = TextLabel(mode_x, mode_y, "GAME MODE", mode_font,
                              pivot=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        self.add_ui_element(mode_label)
        
        mode_btn_x, mode_btn_y = ResponsiveUIPong.scale_position(512, 230, self.ratio)
        mode_btn_w, mode_btn_h = ResponsiveUIPong.scale_size(300, 50, self.ratio)
        mode_btn_font = ResponsiveUIPong.scale_font_size(24, self.ratio)
        
        self.mode_dropdown = Dropdown(mode_btn_x, mode_btn_y, mode_btn_w, mode_btn_h,
                                     ["Player vs AI", "Player vs Player", "AI vs AI"], 
                                     mode_btn_font, pivot=(0.5, 0.5), 
                                     theme=ThemeManager.get_current_theme())
        self.mode_dropdown.set_on_selection_changed(self.change_game_mode)
        self.add_ui_element(self.mode_dropdown)
        
        # AI Difficulty
        diff_x, diff_y = ResponsiveUIPong.scale_position(512, 300, self.ratio)
        diff_font = ResponsiveUIPong.scale_font_size(36, self.ratio)
        diff_label = TextLabel(diff_x, diff_y, "AI DIFFICULTY", diff_font,
                              pivot=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        self.add_ui_element(diff_label)
        
        diff_btn_x, diff_btn_y = ResponsiveUIPong.scale_position(512, 350, self.ratio)
        diff_btn_w, diff_btn_h = ResponsiveUIPong.scale_size(200, 50, self.ratio)
        diff_btn_font = ResponsiveUIPong.scale_font_size(24, self.ratio)
        
        self.diff_dropdown = Dropdown(diff_btn_x, diff_btn_y, diff_btn_w, diff_btn_h,
                                     ["Easy", "Medium", "Hard"], 
                                     diff_btn_font, pivot=(0.5, 0.5),
                                     theme=ThemeManager.get_current_theme())
        self.diff_dropdown.set_on_selection_changed(self.change_ai_difficulty)
        self.diff_dropdown.selected_index = self.ai_difficulty
        self.add_ui_element(self.diff_dropdown)
        
        # Winning Score
        score_x, score_y = ResponsiveUIPong.scale_position(512, 420, self.ratio)
        score_font = ResponsiveUIPong.scale_font_size(36, self.ratio)
        score_label = TextLabel(score_x, score_y, "WINNING SCORE", score_font,
                               pivot=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        self.add_ui_element(score_label)
        
        score_btn_x, score_btn_y = ResponsiveUIPong.scale_position(512, 470, self.ratio)
        score_btn_w, score_btn_h = ResponsiveUIPong.scale_size(150, 50, self.ratio)
        score_btn_font = ResponsiveUIPong.scale_font_size(24, self.ratio)
        
        self.score_dropdown = Dropdown(score_btn_x, score_btn_y, score_btn_w, score_btn_h,
                                      ["3", "5", "7", "10"], 
                                      score_btn_font, pivot=(0.5, 0.5),
                                      theme=ThemeManager.get_current_theme())
        self.score_dropdown.set_on_selection_changed(self.change_winning_score)
        self.score_dropdown.selected_index = 1  # Default to 5
        self.add_ui_element(self.score_dropdown)
        
        # Play button
        play_x, play_y = ResponsiveUIPong.scale_position(512, 550, self.ratio)
        play_w, play_h = ResponsiveUIPong.scale_size(200, 60, self.ratio)
        play_font = ResponsiveUIPong.scale_font_size(36, self.ratio)
        play_btn = Button(play_x, play_y, play_w, play_h, "PLAY", play_font,
                         pivot=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        play_btn.set_on_click(lambda: self.engine.set_scene("GamePong"))
        self.add_ui_element(play_btn)
        
        # Leaderboard button
        leader_x, leader_y = ResponsiveUIPong.scale_position(512, 630, self.ratio)
        leader_w, leader_h = ResponsiveUIPong.scale_size(200, 60, self.ratio)
        leader_font = ResponsiveUIPong.scale_font_size(36, self.ratio)
        leader_btn = Button(leader_x, leader_y, leader_w, leader_h, "LEADERBOARD", leader_font,
                          pivot=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        leader_btn.set_on_click(lambda: self.engine.set_scene("LeaderboardPong"))
        self.add_ui_element(leader_btn)
        
        # Exit button
        exit_x, exit_y = ResponsiveUIPong.scale_position(512, 690, self.ratio)
        exit_w, exit_h = ResponsiveUIPong.scale_size(200, 60, self.ratio)
        exit_font = ResponsiveUIPong.scale_font_size(36, self.ratio)
        exit_btn = Button(exit_x, exit_y, exit_w, exit_h, "EXIT", exit_font,
                         pivot=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        exit_btn.set_on_click(lambda: setattr(self.engine, 'running', False))
        self.add_ui_element(exit_btn)
    
    def change_game_mode(self, index: int, value: str):
        """Change the game mode"""
        self.game_mode = GameMode(index)
    
    def change_ai_difficulty(self, index: int, value: str):
        """Change AI difficulty"""
        self.ai_difficulty = index
    
    def change_winning_score(self, index: int, value: str):
        """Change winning score"""
        self.winning_score = int(value)
    
    def update(self, dt: float):
        self.ratio = ResponsiveUIPong.get_ratio(self.engine)
    
    def render(self, renderer: Renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))

class GamePongScene(Scene):
    """Pong Game Scene"""
    
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        self.ratio = ResponsiveUIPong.get_ratio(engine)
        self.game_started = False
        self.game_over = False
        self.winner = None
        self.start_time = 0
        self.game_duration = 0
        
        # Get settings from main menu
        if "MainMenuPong" in engine.scenes:
            main_menu = engine.scenes["MainMenuPong"]
            self.game_mode = main_menu.game_mode
            self.ai_difficulty = main_menu.ai_difficulty
            self.winning_score = main_menu.winning_score
        else:
            self.game_mode = GameMode.PLAYER_VS_AI
            self.ai_difficulty = 2
            self.winning_score = 5
        
        # Game objects
        self.paddle_width = 15
        self.paddle_height = 100
        self.paddle_speed = 5
        self.ball_radius = 10
        self.ball_speed = 4
        
        self.paddle1 = None
        self.paddle2 = None
        self.ball = None
        
        # Control states
        self.paddle1_up = False
        self.paddle1_down = False
        self.paddle2_up = False
        self.paddle2_down = False
    
    def on_enter(self, previous_scene: str = None):
        ThemeManager.set_current_theme(ThemeType.MATRIX)
        self.clear_ui_elements()
        self.setup_game()
        self.setup_ui()
        self.start_time = pygame.time.get_ticks()
        
        # Setup keyboard controls
        @self.engine.on_event(pygame.KEYDOWN)
        def on_key_down(event):
            self.handle_key_down(event.key)
        
        @self.engine.on_event(pygame.KEYUP)
        def on_key_up(event):
            self.handle_key_up(event.key)
        
        return super().on_enter(previous_scene)
    
    def setup_game(self):
        """Initialize game objects"""
        screen_width = self.engine.width
        screen_height = self.engine.height
        
        # Create paddles
        paddle_margin = 30
        paddle1_x = paddle_margin
        paddle2_x = screen_width - paddle_margin - self.paddle_width
        paddle_y = (screen_height - self.paddle_height) // 2
        
        self.paddle1 = Paddle(paddle1_x, paddle_y, self.paddle_width, 
                             self.paddle_height, self.paddle_speed)
        self.paddle2 = Paddle(paddle2_x, paddle_y, self.paddle_width, 
                             self.paddle_height, self.paddle_speed)
        
        # Set AI difficulty
        difficulty_map = {0: 0.6, 1: 0.8, 2: 0.95}
        ai_level = difficulty_map.get(self.ai_difficulty, 0.8)
        self.paddle1.ai_difficulty = ai_level
        self.paddle2.ai_difficulty = ai_level
        
        # Create ball
        self.ball = Ball(screen_width // 2, screen_height // 2, 
                        self.ball_radius, self.ball_speed)
    
    def setup_ui(self):
        """Setup game UI"""
        screen_width = self.engine.width
        screen_height = self.engine.height
        
        # Score display
        score_font = ResponsiveUIPong.scale_font_size(72, self.ratio)
        self.score1_label = TextLabel(screen_width // 4, 50, "0", score_font,
                                     pivot=(0.5, 0), theme=ThemeManager.get_current_theme())
        self.score2_label = TextLabel(screen_width * 3 // 4, 50, "0", score_font,
                                     pivot=(0.5, 0), theme=ThemeManager.get_current_theme())
        self.add_ui_element(self.score1_label)
        self.add_ui_element(self.score2_label)
        
        # Player names
        name_font = ResponsiveUIPong.scale_font_size(24, self.ratio)
        player1_name = "PLAYER 1" if self.game_mode != GameMode.AI_VS_AI else "AI 1"
        player2_name = "PLAYER 2" if self.game_mode == GameMode.PLAYER_VS_PLAYER else "AI 2"
        
        self.name1_label = TextLabel(screen_width // 4, 120, player1_name, name_font,
                                    pivot=(0.5, 0), theme=ThemeManager.get_current_theme())
        self.name2_label = TextLabel(screen_width * 3 // 4, 120, player2_name, name_font,
                                    pivot=(0.5, 0), theme=ThemeManager.get_current_theme())
        self.add_ui_element(self.name1_label)
        self.add_ui_element(self.name2_label)
        
        # Center line
        self.center_line = []
        for i in range(0, screen_height, 30):
            self.center_line.append((screen_width // 2, i))
        
        # Start message
        start_font = ResponsiveUIPong.scale_font_size(36, self.ratio)
        self.start_label = TextLabel(screen_width // 2, screen_height // 2 - 50, 
                                    "PRESS SPACE TO START", start_font,
                                    pivot=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        self.add_ui_element(self.start_label)
        
        # Game over message (initially hidden)
        game_over_font = ResponsiveUIPong.scale_font_size(48, self.ratio)
        self.game_over_label = TextLabel(screen_width // 2, screen_height // 2 - 100, 
                                        "", game_over_font,
                                        pivot=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        self.game_over_label.visible = False
        self.add_ui_element(self.game_over_label)
        
        # Menu button (hidden initially)
        menu_btn_x, menu_btn_y = ResponsiveUIPong.scale_position(512, 600, self.ratio)
        menu_btn_w, menu_btn_h = ResponsiveUIPong.scale_size(200, 50, self.ratio)
        menu_font = ResponsiveUIPong.scale_font_size(28, self.ratio)
        self.menu_btn = Button(menu_btn_x, menu_btn_y, menu_btn_w, menu_btn_h, 
                              "BACK TO MENU", menu_font,
                              pivot=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        self.menu_btn.set_on_click(lambda: self.engine.set_scene("MainMenuPong"))
        self.menu_btn.visible = False
        self.add_ui_element(self.menu_btn)
        
        # Restart button (hidden initially)
        restart_btn_x, restart_btn_y = ResponsiveUIPong.scale_position(512, 500, self.ratio)
        restart_btn_w, restart_btn_h = ResponsiveUIPong.scale_size(200, 50, self.ratio)
        restart_font = ResponsiveUIPong.scale_font_size(28, self.ratio)
        self.restart_btn = Button(restart_btn_x, restart_btn_y, restart_btn_w, restart_btn_h, 
                                 "PLAY AGAIN", restart_font,
                                 pivot=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        self.restart_btn.set_on_click(self.restart_game)
        self.restart_btn.visible = False
        self.add_ui_element(self.restart_btn)
    
    def handle_key_down(self, key: int):
        """Handle key down events"""
        if not self.game_started and key == pygame.K_SPACE:
            self.game_started = True
            self.start_label.visible = False
            return
        
        if self.game_over:
            return
        
        # Player 1 controls (W/S)
        if key == pygame.K_w:
            self.paddle1_up = True
        elif key == pygame.K_s:
            self.paddle1_down = True
        
        # Player 2 controls (Up/Down)
        if key == pygame.K_UP:
            self.paddle2_up = True
        elif key == pygame.K_DOWN:
            self.paddle2_down = True
    
    def handle_key_up(self, key: int):
        """Handle key up events"""
        # Player 1 controls
        if key == pygame.K_w:
            self.paddle1_up = False
        elif key == pygame.K_s:
            self.paddle1_down = False
        
        # Player 2 controls
        if key == pygame.K_UP:
            self.paddle2_up = False
        elif key == pygame.K_DOWN:
            self.paddle2_down = False
    
    def restart_game(self):
        """Restart the game"""
        self.game_started = False
        self.game_over = False
        self.winner = None
        self.start_time = pygame.time.get_ticks()
        
        # Reset paddles
        screen_height = self.engine.height
        paddle_y = (screen_height - self.paddle_height) // 2
        self.paddle1.reset(30, paddle_y)
        self.paddle2.reset(self.engine.width - 45, paddle_y)
        
        # Reset ball
        self.ball.reset(self.engine.width, self.engine.height)
        
        # Update UI
        self.start_label.visible = True
        self.game_over_label.visible = False
        self.menu_btn.visible = False
        self.restart_btn.visible = False
        self.update_score_display()
    
    def update(self, dt: float):
        self.ratio = ResponsiveUIPong.get_ratio(self.engine)
        
        if not self.game_started or self.game_over:
            return
        
        # Update game duration
        self.game_duration = (pygame.time.get_ticks() - self.start_time) // 1000
        
        # Handle player 1 movement
        if self.game_mode == GameMode.PLAYER_VS_PLAYER or self.game_mode == GameMode.PLAYER_VS_AI:
            if self.paddle1_up:
                self.paddle1.move(-1, self.engine.height)
            if self.paddle1_down:
                self.paddle1.move(1, self.engine.height)
        elif self.game_mode == GameMode.AI_VS_AI:
            # AI controls paddle 1
            self.paddle1.ai_move(self.ball.rect, self.engine.height)
        
        # Handle player 2 movement
        if self.game_mode == GameMode.PLAYER_VS_PLAYER:
            if self.paddle2_up:
                self.paddle2.move(-1, self.engine.height)
            if self.paddle2_down:
                self.paddle2.move(1, self.engine.height)
        else:
            # AI controls paddle 2 (in AI vs AI or Player vs AI)
            self.paddle2.ai_move(self.ball.rect, self.engine.height)
        
        # Move ball
        self.ball.move()
        
        # Ball collision with top/bottom walls
        if self.ball.rect.top <= 0 or self.ball.rect.bottom >= self.engine.height:
            self.ball.bounce_wall()
        
        # Ball collision with paddles
        if self.ball.rect.colliderect(self.paddle1.rect):
            self.ball.bounce_paddle(self.paddle1)
            # Ensure ball doesn't get stuck
            self.ball.rect.left = self.paddle1.rect.right
        
        if self.ball.rect.colliderect(self.paddle2.rect):
            self.ball.bounce_paddle(self.paddle2)
            # Ensure ball doesn't get stuck
            self.ball.rect.right = self.paddle2.rect.left
        
        # Check for score
        scorer = self.ball.check_score(self.engine.width)
        if scorer is not None:
            if scorer == 1:
                self.paddle1.score += 1
            else:
                self.paddle2.score += 1
            
            # Update score display
            self.update_score_display()
            
            # Check for winner
            if self.paddle1.score >= self.winning_score:
                self.game_over = True
                self.winner = "PLAYER 1" if self.game_mode != GameMode.AI_VS_AI else "AI 1"
            elif self.paddle2.score >= self.winning_score:
                self.game_over = True
                self.winner = "PLAYER 2" if self.game_mode == GameMode.PLAYER_VS_PLAYER else "AI 2"
            
            # Reset ball if game isn't over
            if not self.game_over:
                self.ball.reset(self.engine.width, self.engine.height)
            else:
                self.show_game_over()
    
    def update_score_display(self):
        """Update the score display"""
        self.score1_label.set_text(str(self.paddle1.score))
        self.score2_label.set_text(str(self.paddle2.score))
    
    def show_game_over(self):
        """Show game over screen"""
        self.game_over_label.set_text(f"{self.winner} WINS!")
        self.game_over_label.visible = True
        self.menu_btn.visible = True
        self.restart_btn.visible = True
        
        # Save to leaderboard
        player1_name = "PLAYER 1" if self.game_mode != GameMode.AI_VS_AI else "AI 1"
        player2_name = "PLAYER 2" if self.game_mode == GameMode.PLAYER_VS_PLAYER else "AI 2"
        
        leaderboard = LeaderboardPong()
        leaderboard.add_score(
            player1_name, player2_name,
            self.paddle1.score, self.paddle2.score,
            self.winner, self.game_duration
        )
    
    def render(self, renderer: Renderer):
        # Background
        renderer.fill_screen(ThemeManager.get_color('background'))
        
        # Draw center line
        for x, y in self.center_line:
            renderer.draw_rect(x - 2, y, 4, 15, (255, 255, 255, 128))
        
        if not self.game_started:
            super().render(renderer)
            return
        
        # Draw paddles
        renderer.draw_rect(self.paddle1.rect.x, self.paddle1.rect.y,
                          self.paddle1.width, self.paddle1.height,
                          (255, 255, 255))
        renderer.draw_rect(self.paddle2.rect.x, self.paddle2.rect.y,
                          self.paddle2.width, self.paddle2.height,
                          (255, 255, 255))
        
        # Draw ball
        renderer.draw_circle(self.ball.rect.centerx, self.ball.rect.centery,
                            self.ball.radius, (255, 255, 255))
        
        # Draw center circle
        renderer.draw_circle(self.engine.width // 2, self.engine.height // 2,
                            50, (255, 255, 255), fill=False)
        
        # Draw goal areas
        renderer.draw_rect(0, self.engine.height // 2 - 150, 20, 300,
                          (255, 255, 255, 30))
        renderer.draw_rect(self.engine.width - 20, self.engine.height // 2 - 150,
                         20, 300, (255, 255, 255, 30))
        
        super().render(renderer)

class LeaderboardPongScene(Scene):
    """Pong Leaderboard Scene"""
    
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        self.leaderboard = LeaderboardPong()
        self.ratio = ResponsiveUIPong.get_ratio(engine)
        self.scroll_frame = None
    
    def on_enter(self, previous_scene: str = None):
        ThemeManager.set_current_theme(ThemeType.MATRIX)
        self.clear_ui_elements()
        self.setup_ui()
        self.reload_leaderboard()
        return super().on_enter(previous_scene)
    
    def setup_ui(self):
        """Setup leaderboard UI"""
        title_x, title_y = ResponsiveUIPong.scale_position(512, 60, self.ratio)
        title_font = ResponsiveUIPong.scale_font_size(64, self.ratio)
        title = TextLabel(title_x, title_y, "PONG LEADERBOARD", title_font,
                         pivot=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        self.add_ui_element(title)
        
        # Scrolling frame for scores
        frame_x, frame_y = ResponsiveUIPong.scale_position(512, 350, self.ratio)
        frame_w, frame_h = ResponsiveUIPong.scale_size(900, 450, self.ratio)
        content_w, content_h = ResponsiveUIPong.scale_size(880, 600, self.ratio)
        
        self.scroll_frame = ScrollingFrame(
            int(frame_x), int(frame_y), int(frame_w), int(frame_h),
            int(content_w), int(content_h),
            pivot=(0.5, 0.5), theme=ThemeManager.get_current_theme()
        )
        self.add_ui_element(self.scroll_frame)
        
        # Refresh button
        refresh_x, refresh_y = ResponsiveUIPong.scale_position(800, 650, self.ratio)
        refresh_w, refresh_h = ResponsiveUIPong.scale_size(150, 50, self.ratio)
        refresh_font = ResponsiveUIPong.scale_font_size(28, self.ratio)
        refresh_btn = Button(refresh_x, refresh_y, refresh_w, refresh_h, "REFRESH", refresh_font,
                           pivot=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        refresh_btn.set_on_click(self.reload_leaderboard)
        self.add_ui_element(refresh_btn)
        
        # Back button
        back_x, back_y = ResponsiveUIPong.scale_position(512, 650, self.ratio)
        back_w, back_h = ResponsiveUIPong.scale_size(200, 50, self.ratio)
        back_font = ResponsiveUIPong.scale_font_size(36, self.ratio)
        back_btn = Button(back_x, back_y, back_w, back_h, "BACK", back_font,
                         pivot=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        back_btn.set_on_click(lambda: self.engine.set_scene("MainMenuPong"))
        self.add_ui_element(back_btn)
    
    def reload_leaderboard(self):
        """Reload leaderboard data and update display"""
        self.leaderboard = LeaderboardPong()
        self.update_leaderboard_display()
    
    def update_leaderboard_display(self):
        """Update the leaderboard display"""
        if not self.scroll_frame:
            return
        
        self.scroll_frame.clear_children()
        
        scores = self.leaderboard.get_top_scores(20)
        
        if not scores:
            no_scores = TextLabel(400, 200, "No games played yet!", 32,
                                 pivot=(0.5, 0.5), theme=ThemeManager.get_current_theme())
            self.scroll_frame.add_child(no_scores)
            return
        
        # Headers
        headers = ["DATE", "PLAYER 1", "SCORE", "PLAYER 2", "SCORE", "WINNER", "TIME"]
        header_positions = [50, 150, 250, 350, 450, 550, 650]
        
        for i, header in enumerate(headers):
            header_label = TextLabel(header_positions[i], 30, header, 24,
                                    (200, 200, 255), pivot=(0, 0))
            self.scroll_frame.add_child(header_label)
        
        # Score entries
        entry_height = 40
        content_height = len(scores) * entry_height + 80
        self.scroll_frame.content_height = max(content_height, 450)
        
        for i, score_data in enumerate(scores):
            y_pos = 70 + i * entry_height
            
            # Date
            date_label = TextLabel(header_positions[0], y_pos, score_data['date'], 20,
                                 pivot=(0, 0.5))
            self.scroll_frame.add_child(date_label)
            
            # Player 1
            player1_label = TextLabel(header_positions[1], y_pos, score_data['player1'], 20,
                                     pivot=(0, 0.5))
            self.scroll_frame.add_child(player1_label)
            
            # Score 1
            score1_label = TextLabel(header_positions[2], y_pos, str(score_data['score1']), 20,
                                    pivot=(0, 0.5))
            self.scroll_frame.add_child(score1_label)
            
            # Player 2
            player2_label = TextLabel(header_positions[3], y_pos, score_data['player2'], 20,
                                     pivot=(0, 0.5))
            self.scroll_frame.add_child(player2_label)
            
            # Score 2
            score2_label = TextLabel(header_positions[4], y_pos, str(score_data['score2']), 20,
                                    pivot=(0, 0.5))
            self.scroll_frame.add_child(score2_label)
            
            # Winner
            winner_label = TextLabel(header_positions[5], y_pos, score_data['winner'], 20,
                                    pivot=(0, 0.5))
            self.scroll_frame.add_child(winner_label)
            
            # Duration
            time_label = TextLabel(header_positions[6], y_pos, f"{score_data['duration']}s", 20,
                                  pivot=(0, 0.5))
            self.scroll_frame.add_child(time_label)
    
    def update(self, dt: float):
        self.ratio = ResponsiveUIPong.get_ratio(self.engine)
    
    def render(self, renderer: Renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))

def main():
    """Main entry point"""
    fullscreen = False
    if len(sys.argv) >= 2:
        if sys.argv[1] == "--fullscreen":
            fullscreen = True
    
    engine = LunaEngine("Classic Pong - LunaEngine", 1024, 768, fullscreen=fullscreen)
    
    # Try to load icon if available
    try:
        pygame.display.set_icon(pygame.image.load(f"{os.path.dirname(__file__)}/icon.png"))
    except:
        pass
    
    engine.initialize()
    
    # Set sunset theme globally
    ThemeManager.set_current_theme(ThemeType.MATRIX)
    
    # Add scenes
    engine.add_scene("MainMenuPong", MainMenuPong)
    engine.add_scene("GamePong", GamePongScene)
    engine.add_scene("LeaderboardPong", LeaderboardPongScene)
    
    engine.set_scene("MainMenuPong")
    
    engine.run()

if __name__ == "__main__":
    main()