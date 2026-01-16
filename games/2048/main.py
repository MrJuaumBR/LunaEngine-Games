
"""
2048 Game - LunaEngine Implementation
"""

import sys, os, random, json, pygame
from datetime import datetime
from typing import List, Tuple, Optional

from lunaengine.core import Scene, LunaEngine, Renderer
from lunaengine.ui import *

class Leaderboard2048:
    """Leaderboard handler for 2048 game"""
    
    def __init__(self, filename: str = "2048_leaderboard.json"):
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
    
    def add_score(self, name: str, score: int, max_tile: int, moves: int):
        """Add a new score to the leaderboard"""
        self.scores.append({
            "name": name,
            "score": score,
            "max_tile": max_tile,
            "moves": moves,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        self.scores.sort(key=lambda x: x["score"], reverse=True)
        self.scores = self.scores[:20]
        self.save_scores()
    
    def get_top_scores(self, count: int = 10) -> list:
        """Get top N scores"""
        return self.scores[:count]
    
    def is_high_score(self, score: int) -> bool:
        """Check if score qualifies for leaderboard"""
        if len(self.scores) < 10:
            return True
        return score > self.scores[-1]["score"]

class Game2048:
    """2048 game logic core"""
    
    def __init__(self, grid_size: int = 4):
        self.grid_size = grid_size
        self.grid = [[0 for _ in range(grid_size)] for _ in range(grid_size)]
        self.score = 0
        self.game_over = False
        self.won = False
        self.moves = 0
        self.previous_grid = None
        self.can_undo = False
        self.reset()
    
    def reset(self):
        """Reset the game"""
        self.grid = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.score = 0
        self.game_over = False
        self.won = False
        self.moves = 0
        self.previous_grid = None
        self.can_undo = False
        self.add_random_tile()
        self.add_random_tile()
        return True
    
    def add_random_tile(self):
        """Add a random tile (2 or 4) to an empty cell"""
        empty_cells = [
            (r, c) for r in range(self.grid_size) 
            for c in range(self.grid_size) 
            if self.grid[r][c] == 0
        ]
        
        if empty_cells:
            row, col = random.choice(empty_cells)
            self.grid[row][col] = 2 if random.random() < 0.9 else 4
            return True
        return False
    
    def get_max_tile(self) -> int:
        """Get the maximum tile value"""
        return max(max(row) for row in self.grid)
    
    def compress(self, row: List[int]) -> List[int]:
        """Compress row by removing zeros"""
        new_row = [num for num in row if num != 0]
        new_row += [0] * (self.grid_size - len(new_row))
        return new_row
    
    def merge(self, row: List[int]) -> Tuple[List[int], int]:
        """Merge tiles and calculate score increase"""
        score_increase = 0
        for i in range(self.grid_size - 1):
            if row[i] == row[i + 1] and row[i] != 0:
                row[i] *= 2
                row[i + 1] = 0
                score_increase += row[i]
                if row[i] == 2048:
                    self.won = True
        return row, score_increase
    
    def move_left(self) -> bool:
        """Move tiles left"""
        self.previous_grid = [row[:] for row in self.grid]
        moved = False
        for r in range(self.grid_size):
            original = self.grid[r][:]
            self.grid[r] = self.compress(self.grid[r])
            self.grid[r], score_inc = self.merge(self.grid[r])
            self.score += score_inc
            self.grid[r] = self.compress(self.grid[r])
            
            if self.grid[r] != original:
                moved = True
        
        if moved:
            self.moves += 1
            self.add_random_tile()
            self.can_undo = True
            self.check_game_over()
        
        return moved
    
    def move_right(self) -> bool:
        """Move tiles right"""
        self.previous_grid = [row[:] for row in self.grid]
        moved = False
        for r in range(self.grid_size):
            original = self.grid[r][:]
            self.grid[r] = self.grid[r][::-1]
            self.grid[r] = self.compress(self.grid[r])
            self.grid[r], score_inc = self.merge(self.grid[r])
            self.score += score_inc
            self.grid[r] = self.compress(self.grid[r])
            self.grid[r] = self.grid[r][::-1]
            
            if self.grid[r] != original:
                moved = True
        
        if moved:
            self.moves += 1
            self.add_random_tile()
            self.can_undo = True
            self.check_game_over()
        
        return moved
    
    def move_up(self) -> bool:
        """Move tiles up"""
        self.previous_grid = [row[:] for row in self.grid]
        moved = False
        
        for c in range(self.grid_size):
            column = [self.grid[r][c] for r in range(self.grid_size)]
            original = column[:]
            
            column = self.compress(column)
            column, score_inc = self.merge(column)
            self.score += score_inc
            column = self.compress(column)
            
            for r in range(self.grid_size):
                self.grid[r][c] = column[r]
            
            if column != original:
                moved = True
        
        if moved:
            self.moves += 1
            self.add_random_tile()
            self.can_undo = True
            self.check_game_over()
        
        return moved
    
    def move_down(self) -> bool:
        """Move tiles down"""
        self.previous_grid = [row[:] for row in self.grid]
        moved = False
        
        for c in range(self.grid_size):
            column = [self.grid[r][c] for r in range(self.grid_size)]
            original = column[:]
            
            column = column[::-1]
            column = self.compress(column)
            column, score_inc = self.merge(column)
            self.score += score_inc
            column = self.compress(column)
            column = column[::-1]
            
            for r in range(self.grid_size):
                self.grid[r][c] = column[r]
            
            if column != original:
                moved = True
        
        if moved:
            self.moves += 1
            self.add_random_tile()
            self.can_undo = True
            self.check_game_over()
        
        return moved
    
    def undo(self) -> bool:
        """Undo last move"""
        if self.previous_grid and self.can_undo:
            self.grid = [row[:] for row in self.previous_grid]
            self.can_undo = False
            return True
        return False
    
    def check_game_over(self) -> bool:
        """Check if game is over"""
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.grid[r][c] == 0:
                    self.game_over = False
                    return False
        
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                current = self.grid[r][c]
                if c < self.grid_size - 1 and self.grid[r][c + 1] == current:
                    self.game_over = False
                    return False
                if r < self.grid_size - 1 and self.grid[r + 1][c] == current:
                    self.game_over = False
                    return False
        
        self.game_over = True
        return True

class ResponsiveUI2048:
    """Responsive UI helper for 2048"""
    
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

class MainMenu2048(Scene):
    """2048 Main Menu Scene"""
    
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        self.leaderboard = Leaderboard2048()
        self.ratio = ResponsiveUI2048.get_ratio(engine)
        self.grid_size = 4
    
    def on_enter(self, previous_scene: str = None):
        self.clear_ui_elements()
        self.setup_ui()
        # Always use Sunset theme
        ThemeManager.set_current_theme(ThemeType.SUNSET)
        self.engine._update_all_ui_themes(ThemeManager.get_current_theme())
        return super().on_enter(previous_scene)
    
    def setup_ui(self):
        """Setup main menu UI"""
        title_x, title_y = ResponsiveUI2048.scale_position(512, 100, self.ratio)
        title_font = ResponsiveUI2048.scale_font_size(72, self.ratio)
        title = TextLabel(title_x, title_y, "2048", title_font, 
                         root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        self.add_ui_element(title)
        
        play_x, play_y = ResponsiveUI2048.scale_position(512, 200, self.ratio)
        play_w, play_h = ResponsiveUI2048.scale_size(250, 60, self.ratio)
        play_font = ResponsiveUI2048.scale_font_size(36, self.ratio)
        play_btn = Button(play_x, play_y, play_w, play_h, "PLAY", play_font,
                         root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        play_btn.set_on_click(lambda: self.engine.set_scene("Game2048"))
        self.add_ui_element(play_btn)
        
        grid_x, grid_y = ResponsiveUI2048.scale_position(512, 280, self.ratio)
        grid_w, grid_h = ResponsiveUI2048.scale_size(250, 50, self.ratio)
        grid_font = ResponsiveUI2048.scale_font_size(20, self.ratio)
        
        grid_label = TextLabel(grid_x, grid_y - 40, "GRID SIZE", 24,
                              root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        self.add_ui_element(grid_label)
        
        self.grid_dropdown = Dropdown(grid_x, grid_y, grid_w, grid_h,
                                     ["4x4", "5x5", "6x6"], grid_font,
                                     root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        self.grid_dropdown.set_on_selection_changed(self.change_grid_size)
        self.add_ui_element(self.grid_dropdown)
        
        leader_x, leader_y = ResponsiveUI2048.scale_position(512, 350, self.ratio)
        leader_w, leader_h = ResponsiveUI2048.scale_size(250, 60, self.ratio)
        leader_font = ResponsiveUI2048.scale_font_size(36, self.ratio)
        leader_btn = Button(leader_x, leader_y, leader_w, leader_h, "LEADERBOARD", leader_font,
                          root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        leader_btn.set_on_click(lambda: self.engine.set_scene("Leaderboard2048"))
        self.add_ui_element(leader_btn)
        
        exit_x, exit_y = ResponsiveUI2048.scale_position(512, 430, self.ratio)
        exit_w, exit_h = ResponsiveUI2048.scale_size(250, 60, self.ratio)
        exit_font = ResponsiveUI2048.scale_font_size(36, self.ratio)
        exit_btn = Button(exit_x, exit_y, exit_w, exit_h, "EXIT", exit_font,
                         root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        exit_btn.set_on_click(lambda: setattr(self.engine, 'running', False))
        self.add_ui_element(exit_btn)
    
    def change_grid_size(self, index: int, value: str):
        """Change the grid size"""
        size_map = {"4x4": 4, "5x5": 5, "6x6": 6}
        self.grid_size = size_map.get(value, 4)
        print(f"Grid size changed to {self.grid_size}x{self.grid_size}")
    
    def update(self, dt: float):
        self.ratio = ResponsiveUI2048.get_ratio(self.engine)
    
    def render(self, renderer: Renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))

class Game2048Scene(Scene):
    """2048 Game Scene"""
    
    TILE_COLORS = {
        0: (205, 193, 180),
        2: (238, 228, 218),
        4: (237, 224, 200),
        8: (242, 177, 121),
        16: (245, 149, 99),
        32: (246, 124, 95),
        64: (246, 94, 59),
        128: (237, 207, 114),
        256: (237, 204, 97),
        512: (237, 200, 80),
        1024: (237, 197, 63),
        2048: (237, 194, 46),
        4096: (237, 190, 30),
        8192: (237, 187, 20)
    }
    
    TEXT_COLORS = {
        2: (119, 110, 101),
        4: (119, 110, 101),
        8: (249, 246, 242),
        16: (249, 246, 242),
        32: (249, 246, 242),
        64: (249, 246, 242),
        128: (249, 246, 242),
        256: (249, 246, 242),
        512: (249, 246, 242),
        1024: (249, 246, 242),
        2048: (249, 246, 242)
    }
    
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        self.ratio = ResponsiveUI2048.get_ratio(engine)
        self.game = Game2048()
        self.tile_size = 100
        self.grid_padding = 10
        self.board_offset = (0, 0)
        
        # Get grid size from main menu
        if "MainMenu2048" in engine.scenes:
            main_menu = engine.scenes["MainMenu2048"]
            self.game.grid_size = main_menu.grid_size
        
        # Game over handling
        self.showing_game_over = False
        self.showing_win = False
    
    def on_enter(self, previous_scene: str = None):
        # Always use Sunset theme
        ThemeManager.set_current_theme(ThemeType.SUNSET)
        self.clear_ui_elements()
        self.setup_ui()
        
        # Setup keyboard controls
        @self.engine.on_event(pygame.KEYDOWN)
        def on_key_press(event):
            self.handle_key_press(event.key)
        
        return super().on_enter(previous_scene)
    
    def setup_ui(self):
        """Setup game UI"""
        total_size = self.game.grid_size * (self.tile_size + self.grid_padding) + self.grid_padding
        self.board_offset = ((self.engine.width - total_size) // 2, 150)
        
        score_x, score_y = ResponsiveUI2048.scale_position(50, 50, self.ratio)
        score_font = ResponsiveUI2048.scale_font_size(32, self.ratio)
        self.score_label = TextLabel(score_x, score_y, f"SCORE: {self.game.score}", score_font,
                                    root_point=(0, 0), theme=ThemeManager.get_current_theme())
        self.add_ui_element(self.score_label)
        
        high_x, high_y = ResponsiveUI2048.scale_position(50, 90, self.ratio)
        high_font = ResponsiveUI2048.scale_font_size(24, self.ratio)
        self.high_label = TextLabel(high_x, high_y, f"MAX TILE: {self.game.get_max_tile()}", high_font,
                                   root_point=(0, 0), theme=ThemeManager.get_current_theme())
        self.add_ui_element(self.high_label)
        
        moves_x, moves_y = ResponsiveUI2048.scale_position(50, 120, self.ratio)
        moves_font = ResponsiveUI2048.scale_font_size(24, self.ratio)
        self.moves_label = TextLabel(moves_x, moves_y, f"MOVES: {self.game.moves}", moves_font,
                                    root_point=(0, 0), theme=ThemeManager.get_current_theme())
        self.add_ui_element(self.moves_label)
        
        undo_x, undo_y = ResponsiveUI2048.scale_position(self.engine.width - 120, 50, self.ratio)
        undo_w, undo_h = ResponsiveUI2048.scale_size(100, 40, self.ratio)
        undo_font = ResponsiveUI2048.scale_font_size(20, self.ratio)
        self.undo_btn = Button(undo_x, undo_y, undo_w, undo_h, "UNDO", undo_font,
                              root_point=(0.5, 0), theme=ThemeManager.get_current_theme())
        self.undo_btn.set_on_click(self.undo_move)
        self.add_ui_element(self.undo_btn)
        
        reset_x, reset_y = ResponsiveUI2048.scale_position(self.engine.width - 120, 100, self.ratio)
        reset_w, reset_h = ResponsiveUI2048.scale_size(100, 40, self.ratio)
        reset_font = ResponsiveUI2048.scale_font_size(20, self.ratio)
        reset_btn = Button(reset_x, reset_y, reset_w, reset_h, "RESET", reset_font,
                          root_point=(0.5, 0), theme=ThemeManager.get_current_theme())
        reset_btn.set_on_click(self.reset_game)
        self.add_ui_element(reset_btn)
        
        menu_x, menu_y = ResponsiveUI2048.scale_position(self.engine.width - 120, 150, self.ratio)
        menu_w, menu_h = ResponsiveUI2048.scale_size(100, 40, self.ratio)
        menu_font = ResponsiveUI2048.scale_font_size(20, self.ratio)
        menu_btn = Button(menu_x, menu_y, menu_w, menu_h, "MENU", menu_font,
                         root_point=(0.5, 0), theme=ThemeManager.get_current_theme())
        menu_btn.set_on_click(lambda: self.engine.set_scene("MainMenu2048"))
        self.add_ui_element(menu_btn)
    
    def handle_key_press(self, key: int):
        """Handle keyboard input"""
        # Always allow ESC for menu
        if key == pygame.K_ESCAPE:
            self.engine.set_scene("MainMenu2048")
            return
        
        # Handle game over/win screens
        if self.showing_game_over or self.showing_win:
            if key == pygame.K_SPACE:
                self.reset_game()
                self.showing_game_over = False
                self.showing_win = False
            return
        
        # Handle game controls
        if self.game.game_over or self.game.won:
            return
        
        moved = False
        if key == pygame.K_UP:
            moved = self.game.move_up()
        elif key == pygame.K_DOWN:
            moved = self.game.move_down()
        elif key == pygame.K_LEFT:
            moved = self.game.move_left()
        elif key == pygame.K_RIGHT:
            moved = self.game.move_right()
        elif key == pygame.K_u or key == pygame.K_z:
            self.undo_move()
        elif key == pygame.K_r:
            self.reset_game()
    
    def undo_move(self):
        """Undo the last move"""
        if self.game.undo():
            print("Move undone")
    
    def reset_game(self):
        """Reset the game"""
        self.game.reset()
        self.showing_game_over = False
        self.showing_win = False
        print("Game reset")
    
    def update(self, dt: float):
        self.ratio = ResponsiveUI2048.get_ratio(self.engine)
        
        # Update labels
        self.score_label.set_text(f"SCORE: {self.game.score}")
        self.high_label.set_text(f"MAX TILE: {self.game.get_max_tile()}")
        self.moves_label.set_text(f"MOVES: {self.game.moves}")
        
        # Update undo button state
        self.undo_btn.enabled = self.game.can_undo
        
        # Check for game over/win
        if self.game.game_over and not self.showing_game_over:
            self.showing_game_over = True
            self.check_high_score()
        
        if self.game.won and not self.showing_win:
            self.showing_win = True
    
    def check_high_score(self):
        """Check if score qualifies for leaderboard"""
        leaderboard = Leaderboard2048()
        if leaderboard.is_high_score(self.game.score):
            self.engine.add_scene("NameInput2048", NameInput2048Scene(
                self.engine, self.game.score, self.game.get_max_tile(), self.game.moves
            ))
            self.engine.set_scene("NameInput2048")
    
    def draw_tile(self, renderer: Renderer, x: int, y: int, value: int):
        """Draw a single tile"""
        color = self.TILE_COLORS.get(value, (60, 58, 50))
        
        # Draw tile background
        renderer.draw_rect(x, y, self.tile_size, self.tile_size, color)
        
        # Draw tile border
        border_color = tuple(max(0, c - 30) for c in color)
        renderer.draw_rect(x, y, self.tile_size, self.tile_size, border_color, fill=False)
        
        # Draw value
        if value > 0:
            font_size = 40 if value < 100 else 32 if value < 1000 else 24
            font = FontManager.get_font(None, font_size)
            
            text_color = self.TEXT_COLORS.get(value, (249, 246, 242))
            text = str(value)
            text_surface = font.render(text, True, text_color)
            
            text_x = x + (self.tile_size - text_surface.get_width()) // 2
            text_y = y + (self.tile_size - text_surface.get_height()) // 2
            
            renderer.blit(text_surface, (text_x, text_y))
    
    def render(self, renderer: Renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))
        
        # Draw game board background
        board_width = self.game.grid_size * (self.tile_size + self.grid_padding) + self.grid_padding
        board_height = board_width
        
        renderer.draw_rect(
            self.board_offset[0] - 5, self.board_offset[1] - 5,
            board_width + 10, board_height + 10,
            (187, 173, 160)
        )
        
        # Draw tiles
        for r in range(self.game.grid_size):
            for c in range(self.game.grid_size):
                value = self.game.grid[r][c]
                
                x = self.board_offset[0] + c * (self.tile_size + self.grid_padding) + self.grid_padding
                y = self.board_offset[1] + r * (self.tile_size + self.grid_padding) + self.grid_padding
                
                self.draw_tile(renderer, x, y, value)
        
        # Draw game over/win screen
        if self.showing_game_over:
            self.draw_game_over(renderer)
        elif self.showing_win:
            self.draw_win_screen(renderer)
    
    def draw_game_over(self, renderer: Renderer):
        """Draw game over overlay"""
        overlay = pygame.Surface((self.engine.width, self.engine.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        renderer.blit(overlay, (0, 0))
        
        font_size = ResponsiveUI2048.scale_font_size(72, self.ratio)
        font = FontManager.get_font(None, font_size)
        
        text = "GAME OVER"
        text_surface = font.render(text, True, (255, 255, 255))
        text_x = (self.engine.width - text_surface.get_width()) // 2
        text_y = (self.engine.height - text_surface.get_height()) // 2 - 50
        
        renderer.blit(text_surface, (text_x, text_y))
        
        score_font_size = ResponsiveUI2048.scale_font_size(48, self.ratio)
        score_font = FontManager.get_font(None, score_font_size)
        
        score_text = f"Score: {self.game.score}"
        score_surface = score_font.render(score_text, True, (255, 255, 255))
        score_x = (self.engine.width - score_surface.get_width()) // 2
        score_y = text_y + 80
        
        renderer.blit(score_surface, (score_x, score_y))
        
        restart_font_size = ResponsiveUI2048.scale_font_size(36, self.ratio)
        restart_font = FontManager.get_font(None, restart_font_size)
        
        restart_text = "Press SPACE to restart"
        restart_surface = restart_font.render(restart_text, True, (200, 200, 255))
        restart_x = (self.engine.width - restart_surface.get_width()) // 2
        restart_y = score_y + 60
        
        renderer.blit(restart_surface, (restart_x, restart_y))
        
        menu_text = "Press ESC for menu"
        menu_surface = restart_font.render(menu_text, True, (200, 200, 200))
        menu_x = (self.engine.width - menu_surface.get_width()) // 2
        menu_y = restart_y + 50
        
        renderer.blit(menu_surface, (menu_x, menu_y))
    
    def draw_win_screen(self, renderer: Renderer):
        """Draw win screen overlay"""
        overlay = pygame.Surface((self.engine.width, self.engine.height), pygame.SRCALPHA)
        overlay.fill((255, 215, 0, 100))
        renderer.blit(overlay, (0, 0))
        
        font_size = ResponsiveUI2048.scale_font_size(72, self.ratio)
        font = FontManager.get_font(None, font_size)
        
        text = "YOU WIN!"
        text_surface = font.render(text, True, (255, 255, 255))
        text_x = (self.engine.width - text_surface.get_width()) // 2
        text_y = (self.engine.height - text_surface.get_height()) // 2 - 50
        
        renderer.blit(text_surface, (text_x, text_y))
        
        continue_font_size = ResponsiveUI2048.scale_font_size(32, self.ratio)
        continue_font = FontManager.get_font(None, continue_font_size)
        
        continue_text = "Press SPACE to continue playing"
        continue_surface = continue_font.render(continue_text, True, (255, 255, 255))
        continue_x = (self.engine.width - continue_surface.get_width()) // 2
        continue_y = text_y + 100
        
        renderer.blit(continue_surface, (continue_x, continue_y))

class Leaderboard2048Scene(Scene):
    """2048 Leaderboard Scene"""
    
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        self.leaderboard = Leaderboard2048()
        self.ratio = ResponsiveUI2048.get_ratio(engine)
        self.scroll_frame = None
    
    def on_enter(self, previous_scene: str = None):
        # Always use Sunset theme
        ThemeManager.set_current_theme(ThemeType.SUNSET)
        self.clear_ui_elements()
        self.setup_ui()
        # Auto-reload leaderboard when entering the scene
        self.reload_leaderboard()
        return super().on_enter(previous_scene)
    
    def setup_ui(self):
        """Setup leaderboard UI"""
        title_x, title_y = ResponsiveUI2048.scale_position(512, 80, self.ratio)
        title_font = ResponsiveUI2048.scale_font_size(64, self.ratio)
        title = TextLabel(title_x, title_y, "2048 LEADERBOARD", title_font,
                         root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        self.add_ui_element(title)
        
        frame_x, frame_y = ResponsiveUI2048.scale_position(512, 350, self.ratio)
        frame_w, frame_h = ResponsiveUI2048.scale_size(900, 450, self.ratio)
        content_w, content_h = ResponsiveUI2048.scale_size(880, 800, self.ratio)
        
        self.scroll_frame = ScrollingFrame(
            int(frame_x), int(frame_y), int(frame_w), int(frame_h),
            int(content_w), int(content_h),
            root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme()
        )
        self.add_ui_element(self.scroll_frame)
        
        # Refresh button
        refresh_x, refresh_y = ResponsiveUI2048.scale_position(800, 650, self.ratio)
        refresh_w, refresh_h = ResponsiveUI2048.scale_size(120, 50, self.ratio)
        refresh_font = ResponsiveUI2048.scale_font_size(28, self.ratio)
        refresh_btn = Button(refresh_x, refresh_y, refresh_w, refresh_h, "REFRESH", refresh_font,
                           root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        refresh_btn.set_on_click(self.reload_leaderboard)
        self.add_ui_element(refresh_btn)
        
        # Back button
        back_x, back_y = ResponsiveUI2048.scale_position(512, 650, self.ratio)
        back_w, back_h = ResponsiveUI2048.scale_size(200, 50, self.ratio)
        back_font = ResponsiveUI2048.scale_font_size(36, self.ratio)
        back_btn = Button(back_x, back_y, back_w, back_h, "BACK", back_font,
                         root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        back_btn.set_on_click(lambda: self.engine.set_scene("MainMenu2048"))
        self.add_ui_element(back_btn)
    
    def reload_leaderboard(self):
        """Reload leaderboard data and update display"""
        # Reload the scores from file
        self.leaderboard = Leaderboard2048()
        # Update the display
        self.update_leaderboard_display()
        print("Leaderboard refreshed")
    
    def update_leaderboard_display(self):
        """Update the leaderboard display"""
        if not self.scroll_frame:
            return
        
        self.scroll_frame.clear_children()
        
        top_scores = self.leaderboard.get_top_scores(20)
        
        if not top_scores:
            no_scores = TextLabel(400, 200, "No scores yet! Play the game!", 32,
                                 root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
            self.scroll_frame.add_child(no_scores)
            return
        
        header_y = 30
        headers = ["RANK", "NAME", "SCORE", "MAX TILE", "MOVES", "DATE"]
        header_positions = [50, 150, 300, 400, 500, 600]
        
        for i, header in enumerate(headers):
            header_label = TextLabel(header_positions[i], header_y, header, 24,
                                    (200, 200, 255), root_point=(0, 0))
            self.scroll_frame.add_child(header_label)
        
        entry_height = 50
        content_height = len(top_scores) * entry_height + 80
        self.scroll_frame.content_height = max(content_height, 450)
        
        for i, score_data in enumerate(top_scores):
            y_pos = header_y + 60 + i * entry_height
            
            rank_label = TextLabel(header_positions[0], y_pos, f"#{i+1}", 22,
                                 root_point=(0, 0.5))
            self.scroll_frame.add_child(rank_label)
            
            name_label = TextLabel(header_positions[1], y_pos, score_data['name'][:15], 22,
                                 root_point=(0, 0.5))
            self.scroll_frame.add_child(name_label)
            
            score_label = TextLabel(header_positions[2], y_pos, str(score_data['score']), 22,
                                  root_point=(0, 0.5))
            self.scroll_frame.add_child(score_label)
            
            tile_label = TextLabel(header_positions[3], y_pos, str(score_data['max_tile']), 22,
                                 root_point=(0, 0.5))
            self.scroll_frame.add_child(tile_label)
            
            moves_label = TextLabel(header_positions[4], y_pos, str(score_data['moves']), 22,
                                  root_point=(0, 0.5))
            self.scroll_frame.add_child(moves_label)
            
            date_label = TextLabel(header_positions[5], y_pos, score_data['date'], 18,
                                 root_point=(0, 0.5))
            self.scroll_frame.add_child(date_label)
    
    def update(self, dt: float):
        self.ratio = ResponsiveUI2048.get_ratio(self.engine)
    
    def render(self, renderer: Renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))

class NameInput2048Scene(Scene):
    """Name input scene for high scores"""
    
    def __init__(self, engine: LunaEngine, score: int, max_tile: int, moves: int):
        super().__init__(engine)
        self.score = score
        self.max_tile = max_tile
        self.moves = moves
        self.ratio = ResponsiveUI2048.get_ratio(engine)
    
    def on_enter(self, previous_scene: str = None):
        # Always use Sunset theme
        ThemeManager.set_current_theme(ThemeType.SUNSET)
        self.clear_ui_elements()
        self.setup_ui()
        return super().on_enter(previous_scene)
    
    def setup_ui(self):
        """Setup name input UI"""
        title_x, title_y = ResponsiveUI2048.scale_position(512, 200, self.ratio)
        title_font = ResponsiveUI2048.scale_font_size(48, self.ratio)
        title = TextLabel(title_x, title_y, "NEW HIGH SCORE!", title_font,
                         root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        self.add_ui_element(title)
        
        score_x, score_y = ResponsiveUI2048.scale_position(512, 260, self.ratio)
        score_font = ResponsiveUI2048.scale_font_size(36, self.ratio)
        score_label = TextLabel(score_x, score_y, f"Score: {self.score}", score_font,
                               root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        self.add_ui_element(score_label)
        
        tile_x, tile_y = ResponsiveUI2048.scale_position(512, 300, self.ratio)
        tile_font = ResponsiveUI2048.scale_font_size(24, self.ratio)
        tile_label = TextLabel(tile_x, tile_y, f"Max Tile: {self.max_tile}", tile_font,
                              root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        self.add_ui_element(tile_label)
        
        name_x, name_y = ResponsiveUI2048.scale_position(512, 360, self.ratio)
        name_font = ResponsiveUI2048.scale_font_size(32, self.ratio)
        name_label = TextLabel(name_x, name_y, "ENTER YOUR NAME:", name_font,
                              root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        self.add_ui_element(name_label)
        
        # Create TextBox with proper LunaEngine parameters
        input_x, input_y = ResponsiveUI2048.scale_position(512, 410, self.ratio)
        input_w, input_h = ResponsiveUI2048.scale_size(300, 50, self.ratio)
        input_font = ResponsiveUI2048.scale_font_size(28, self.ratio)
        
        # TextBox parameters as per your LunaEngine:
        # __init__(self, x, y, width, height, text, font_size, font_name, root_point, theme, max_length, element_id)
        self.name_input = TextBox(
            input_x, input_y, input_w, input_h, 
            "",  # text
            input_font,  # font_size
            None,  # font_name (use default)
            (0.5, 0.5),  # root_point
            ThemeManager.get_current_theme(),  # theme
            20,  # max_length
            "name_input"  # element_id
        )
        self.add_ui_element(self.name_input)
        
        save_x, save_y = ResponsiveUI2048.scale_position(512, 480, self.ratio)
        save_w, save_h = ResponsiveUI2048.scale_size(200, 50, self.ratio)
        save_font = ResponsiveUI2048.scale_font_size(36, self.ratio)
        save_btn = Button(save_x, save_y, save_w, save_h, "SAVE", save_font,
                         root_point=(0.5, 0.5), theme=ThemeManager.get_current_theme())
        save_btn.set_on_click(self.save_score)
        self.add_ui_element(save_btn)
    
    def save_score(self):
        """Save the score to leaderboard"""
        name = self.name_input.text.strip()
        if not name:
            name = "Anonymous"
        
        leaderboard = Leaderboard2048()
        leaderboard.add_score(name, self.score, self.max_tile, self.moves)
        print(f"Score saved: {name} - {self.score}")
        self.engine.set_scene("Leaderboard2048")
    
    def update(self, dt: float):
        self.ratio = ResponsiveUI2048.get_ratio(self.engine)
    
    def render(self, renderer: Renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))

def main():
    """Main entry point"""
    fullscreen = False
    if len(sys.argv) >= 2:
        if sys.argv[1] == "--fullscreen":
            fullscreen = True
    
    engine = LunaEngine("2048 - LunaEngine", 1024, 768, fullscreen=fullscreen)
    
    pygame.display.set_icon(pygame.image.load(f"{os.path.dirname(__file__)}/icon.png"))
    
    engine.initialize()
    
    # Set sunset theme globally
    ThemeManager.set_current_theme(ThemeType.SUNSET)
    
    engine.add_scene("MainMenu2048", MainMenu2048)
    engine.add_scene("Game2048", Game2048Scene)
    engine.add_scene("Leaderboard2048", Leaderboard2048Scene)
    
    engine.set_scene("MainMenu2048")
    
    engine.run()

if __name__ == "__main__":
    main()