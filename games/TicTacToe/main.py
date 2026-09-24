import sys, os, random, json, pygame, time
from datetime import datetime
from typing import List, Tuple, Optional, Literal

from lunaengine.core import Scene, LunaEngine, Renderer
from lunaengine.ui import *

class _Data:
    screen_width, screen_height = 1024, 768
    ratio: pygame.math.Vector2
    leaderboard:dict
    def __init__(self):
        self.load_leaderboard()
        
    def load_leaderboard(self):
        if not os.path.exists(f'{os.path.abspath(os.path.dirname(__file__))}/leaderboard.json'):
            self.leaderboard = {
                "scores": []
            }
            with open(f'{os.path.abspath(os.path.dirname(__file__))}/leaderboard.json', 'w') as f:
                json.dump(self.leaderboard, f)
                f.close()
        else:
            with open(f'{os.path.abspath(os.path.dirname(__file__))}/leaderboard.json', 'r') as f:
                self.leaderboard = json.load(f)
                f.close()
    
    def update_leaderboard(self):
        with open(f'{os.path.abspath(os.path.dirname(__file__))}/leaderboard.json', 'w') as f:
            json.dump(self.leaderboard, f)
            f.close()
        
    def set_ratio(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.ratio = pygame.math.Vector2(screen_width / 1024, screen_height / 768)
        
data = _Data()

class TicTacToeGame:
    """Tic Tac Toe game logic - adapted from working Pygame version"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset the game board"""
        self.board = [['-' for _ in range(3)] for _ in range(3)]
        self.current_player = 'X'
        self.winner = None
        self.game_over = False
        self.taking_move = True
        self.winning_cells = []
        self.line_type = None
    
    def make_move(self, col, row):
        """Make a move on the board - note: col, row (x, y) format"""
        if not self.game_over and self.board[col][row] == '-':
            self.board[col][row] = self.current_player
            self.check_winner()
            if not self.game_over:
                self.switch_player()
            return True
        return False
    
    def switch_player(self):
        """Switch between X and O players"""
        self.current_player = 'O' if self.current_player == 'X' else 'X'
    
    def check_winner(self):
        """Check if there's a winner or if it's a tie"""
        # Check rows (vertical in original)
        for col in range(3):
            win = True
            pattern_list = []
            for row in range(3):
                if self.board[col][row] != self.current_player:
                    win = False
                    break
                else:
                    pattern_list.append((col, row))
            if win:
                self.winner = self.current_player
                self.game_over = True
                self.taking_move = False
                self.winning_cells = pattern_list
                self.line_type = "ver"
                return True
        
        # Check columns (horizontal in original)
        for row in range(3):
            win = True
            pattern_list = []
            for col in range(3):
                if self.board[col][row] != self.current_player:
                    win = False
                    break
                else:
                    pattern_list.append((col, row))
            if win:
                self.winner = self.current_player
                self.game_over = True
                self.taking_move = False
                self.winning_cells = pattern_list
                self.line_type = "hor"
                return True
        
        # Check left diagonal (top-left to bottom-right)
        win = True
        pattern_list = []
        for i in range(3):
            if self.board[i][i] != self.current_player:
                win = False
                break
            else:
                pattern_list.append((i, i))
        if win:
            self.winner = self.current_player
            self.game_over = True
            self.taking_move = False
            self.winning_cells = pattern_list
            self.line_type = "left-diag"
            return True
        
        # Check right diagonal (top-right to bottom-left)
        win = True
        pattern_list = []
        for i in range(3):
            if self.board[2-i][i] != self.current_player:
                win = False
                break
            else:
                pattern_list.append((2-i, i))
        if win:
            self.winner = self.current_player
            self.game_over = True
            self.taking_move = False
            self.winning_cells = pattern_list
            self.line_type = "right-diag"
            return True
        
        # Check for tie
        blank_cells = 0
        for col in self.board:
            for cell in col:
                if cell == '-':
                    blank_cells += 1
        if blank_cells == 0:
            self.game_over = True
            self.taking_move = False
            self.winner = 'TIE'
            return True
        
        return False
    
    def get_empty_cells(self):
        """Get list of empty cells"""
        cells = []
        for col in range(3):
            for row in range(3):
                if self.board[col][row] == '-':
                    cells.append((col, row))
        return cells

class MainMenu(Scene):
    def __init__(self, engine, *args, **kwargs):
        super().__init__(engine, *args, **kwargs)
        self.setup_ui()
        
    def setup_ui(self):
        ThemeManager.set_current_theme(ThemeType.SUNSET)
        title = TextLabel(self.engine.width//2, 100*data.ratio.y, "Tic Tac Toe", 86, (50, 50, 60), None, pivot=(0.5, 0))
        hover_anim = Tween.create(title)
        hover_anim.to(
            y=60 * data.ratio.y,
            duration=2,
            easing=EasingType.LINEAR
        )
        hover_anim.set_loops(-1, True)
        self.engine.animation_handler.add('title_hover_anim', hover_anim, True)
        self.add_ui_element(title)
        
        self.play_button = Button(self.engine.width//2, 250*data.ratio.y, 200*data.ratio.x, 65*data.ratio.y, "Play", 50, None, pivot=(0.5, 0))
        self.play_button.set_on_click(self.play)
        self.add_ui_element(self.play_button)
        
        self.leaderboard_button = Button(self.engine.width//2, 330*data.ratio.y, 200*data.ratio.x, 50*data.ratio.y, "Leaderboard", 40, None, pivot=(0.5, 0))
        self.leaderboard_button.set_on_click(self.leaderboard)
        self.add_ui_element(self.leaderboard_button)
        
        self.exit_button = Button(self.engine.width//2, 390*data.ratio.y, 200*data.ratio.x, 50*data.ratio.y, "Exit", 40, None, pivot=(0.5, 0))
        self.exit_button.set_on_click(lambda: setattr(self.engine, 'running', False))
        self.add_ui_element(self.exit_button)
        
    def play(self):
        self.engine.set_scene("game")
    
    def  leaderboard(self):
        self.engine.set_scene("leaderboard")
        
    def on_enter(self, previous_scene: str = None):
        return super().on_enter(previous_scene)
    
    def on_exit(self, next_scene: str = None):
        return super().on_exit(next_scene)
    
    def render(self, renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))
        
    def update(self, dt):
        return super().update(dt)
        
class GameScene(Scene):
    def __init__(self, engine, *args, **kwargs):
        super().__init__(engine, *args, **kwargs)
        self.game = TicTacToeGame()
        self.start_play = 0
        self.vitories_x = 0
        self.vitories_o = 0
        self.setup_ui()
        
    def on_enter(self, previous_scene = None):
        self.start_play = time.time()
        self.game.reset()
        
        # Set up event handlers
        @self.engine.on_event(pygame.MOUSEBUTTONDOWN)
        def handle_click(event):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_board_click(event.pos)
        
        @self.engine.on_event(pygame.KEYDOWN)
        def handle_key(event):
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.reset_game()
                elif event.key == pygame.K_ESCAPE:
                    self.engine.set_scene("main")
        
    def setup_ui(self):
        ThemeManager.set_current_theme(ThemeType.SUNSET)
        
        # Title
        self.add_ui_element(TextLabel(self.engine.width//2, 30*data.ratio.y, 'Tic Tac Toe', 64, (200, 170, 100), None, pivot=(0.5, 0)))
        
        # Timer and score
        self.timer = TextLabel(self.engine.width//2, 100*data.ratio.y, '00:00', 36, (200, 170, 100), None, pivot=(0.5, 0))
        self.score_label = TextLabel(self.engine.width//2, 150*data.ratio.y, 'X: 0 - O: 0', 32, (200, 170, 100), None, pivot=(0.5, 0))
        
        # Current player indicator
        self.player_indicator = TextLabel(self.engine.width//2, 200*data.ratio.y, "X's Turn", 32, (200, 170, 100), None, pivot=(0.5, 0))
        
        # Back button
        self.back_button = Button(100*data.ratio.x, 50*data.ratio.y, 
                            120*data.ratio.x, 50*data.ratio.y, "Back", 40, 
                            None, pivot=(0, 0))
        self.back_button.set_on_click(lambda: self.engine.set_scene("main"))
        self.add_ui_element(self.back_button)
        
        # Reset button
        self.reset_button = Button(self.engine.width - 120*data.ratio.x, 50*data.ratio.y,
                             120*data.ratio.x, 50*data.ratio.y, "Reset", 40,
                             None, pivot=(1, 0))
        self.reset_button.set_on_click(self.reset_game)
        self.add_ui_element(self.reset_button)
        
        self.add_ui_element(self.timer)
        self.add_ui_element(self.score_label)
        self.add_ui_element(self.player_indicator)
    
    def handle_board_click(self, pos):
        """Handle click on the game board"""
        if not self.game.taking_move:
            return
        
        # Calculate board position
        board_width = 312 * data.ratio.x
        board_height = 312 * data.ratio.y
        board_x = self.engine.width//2 - board_width//2
        board_y = self.engine.height//2 - board_height//2 + 50*data.ratio.y
        cell_size = 104 * data.ratio.x
        
        # Check if click is inside board
        if (board_x <= pos[0] <= board_x + board_width and 
            board_y <= pos[1] <= board_y + board_height):
            
            # Calculate grid position (col, row format)
            col = int((pos[0] - board_x) // cell_size)
            row = int((pos[1] - board_y) // cell_size)
            
            # Make move
            if self.game.make_move(col, row):
                self.update_player_indicator()
                if self.game.game_over:
                    self.handle_game_end()
    
    def update_player_indicator(self):
        """Update the current player indicator"""
        if self.game.game_over:
            if self.game.winner == 'TIE':
                self.player_indicator.set_text("It's a Tie!")
            else:
                self.player_indicator.set_text(f"{self.game.winner} Wins!")
        else:
            self.player_indicator.set_text(f"{self.game.current_player}'s Turn")
    
    def handle_game_end(self):
        """Handle end of game"""
        # Update victories
        if self.game.winner == 'X':
            self.vitories_x += 1
        elif self.game.winner == 'O':
            self.vitories_o += 1
        
        # Save to leaderboard
        if self.game.winner != 'TIE':
            data.leaderboard['scores'].append({
                "name": f"Player {self.game.winner}",
                "score": self.vitories_x if self.game.winner == 'X' else self.vitories_o,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            data.update_leaderboard()
    
    def reset_game(self):
        """Reset the game"""
        self.game.reset()
        self.update_player_indicator()
        self.start_play = time.time()
        
    def draw_winning_line(self, renderer, board_x, board_y, cell_size):
        """Draw winning line based on line type"""
        if not self.game.winning_cells or not self.game.line_type:
            return
        
        mid_val = cell_size // 2
        table_space = 20 * data.ratio.x
        
        if self.game.line_type == "ver":
            # Vertical line
            start_point, end_point = self.game.winning_cells[0], self.game.winning_cells[-1]
            start_x = board_x + start_point[0] * cell_size + mid_val
            start_y = board_y + table_space
            end_x = board_x + end_point[0] * cell_size + mid_val
            end_y = board_y + 3 * cell_size - table_space
            renderer.draw_line(start_x, start_y, end_x, end_y, (38, 255, 0), 8*data.ratio.x)
            
        elif self.game.line_type == "hor":
            # Horizontal line
            start_point, end_point = self.game.winning_cells[0], self.game.winning_cells[-1]
            start_x = board_x + table_space
            start_y = board_y + start_point[1] * cell_size + mid_val
            end_x = board_x + 3 * cell_size - table_space
            end_y = board_y + end_point[1] * cell_size + mid_val
            renderer.draw_line(start_x, start_y, end_x, end_y, (38, 255, 0), 8*data.ratio.x)
            
        elif self.game.line_type == "left-diag":
            # Left diagonal
            start_x = board_x + table_space
            start_y = board_y + table_space
            end_x = board_x + 3 * cell_size - table_space
            end_y = board_y + 3 * cell_size - table_space
            renderer.draw_line(start_x, start_y, end_x, end_y, (38, 255, 0), 8*data.ratio.x)
            
        elif self.game.line_type == "right-diag":
            # Right diagonal
            start_x = board_x + 3 * cell_size - table_space
            start_y = board_y + table_space
            end_x = board_x + table_space
            end_y = board_y + 3 * cell_size - table_space
            renderer.draw_line(start_x, start_y, end_x, end_y, (38, 255, 0), 8*data.ratio.x)
        
    def render(self, renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))
        
        # Draw game board
        board_width = 312 * data.ratio.x
        board_height = 312 * data.ratio.y
        board_x = self.engine.width//2 - board_width//2
        board_y = self.engine.height//2 - board_height//2 + 50*data.ratio.y
        cell_size = 104 * data.ratio.x
        
        # Draw board background
        renderer.draw_rect(board_x, board_y, board_width, board_height, (180, 179, 181))
        
        # Draw grid lines (thicker lines like in the original)
        line_color = (50, 50, 50)
        line_width = 8 * data.ratio.x
        
        # Horizontal lines
        renderer.draw_line(board_x, board_y + cell_size, board_x + board_width, 
                         board_y + cell_size, line_color, line_width)
        renderer.draw_line(board_x, board_y + 2*cell_size, board_x + board_width, 
                         board_y + 2*cell_size, line_color, line_width)
        
        # Vertical lines
        renderer.draw_line(board_x + cell_size, board_y, board_x + cell_size, 
                         board_y + board_height, line_color, line_width)
        renderer.draw_line(board_x + 2*cell_size, board_y, board_x + 2*cell_size, 
                         board_y + board_height, line_color, line_width)
        
        # Draw X's and O's
        for col in range(3):
            for row in range(3):
                cell_center_x = board_x + col * cell_size + cell_size // 2
                cell_center_y = board_y + row * cell_size + cell_size // 2
                
                if self.game.board[col][row] == 'X':
                    # Draw X (red color)
                    size = 40 * data.ratio.x
                    renderer.draw_line(cell_center_x - size, cell_center_y - size, 
                                     cell_center_x + size, cell_center_y + size, 
                                     (255, 100, 100), 6*data.ratio.x)
                    renderer.draw_line(cell_center_x + size, cell_center_y - size,
                                     cell_center_x - size, cell_center_y + size,
                                     (255, 100, 100), 6*data.ratio.x)
                elif self.game.board[col][row] == 'O':
                    # Draw O (blue color)
                    radius = 40 * data.ratio.x
                    renderer.draw_circle(cell_center_x, cell_center_y, radius, 
                                       (100, 100, 255), 6*data.ratio.x)
        
        # Draw winning line if there's a winner
        if self.game.winner and self.game.winner != 'TIE':
            self.draw_winning_line(renderer, board_x, board_y, cell_size)
        
        # Draw instructions
        instructions = [
            "Click on a cell to place your mark",
            "Press R to restart",
            "Press ESC to return to menu"
        ]
        for i, text in enumerate(instructions):
            renderer.draw_text(text, self.engine.width//2, 600*data.ratio.y + i*30, 
                             (200, 200, 200), FontManager.get_font(None, 20))
        
    def update(self, dt):
        # Update timer
        elapsed = int(time.time() - self.start_play)
        minutes = elapsed // 60
        seconds = elapsed % 60
        self.timer.set_text(f'Time: {minutes:02d}:{seconds:02d}')
        
        # Update score display
        self.score_label.set_text(f'X: {self.vitories_x} - O: {self.vitories_o}')
        
        # Auto-reset after game ends (after 3 seconds)
        if self.game.game_over and time.time() - self.start_play > elapsed + 3:
            self.reset_game()
        
        return super().update(dt)
    
class LeaderboardScene(Scene):
    def __init__(self, engine, *args, **kwargs):
        super().__init__(engine, *args, **kwargs)
        self.setup_ui()
        
    def on_enter(self, previous_scene = None):
        self.reload_scores()
        return super().on_enter(previous_scene)
        
    def setup_ui(self):
        ThemeManager.set_current_theme(ThemeType.SUNSET)
        self.add_ui_element(TextLabel(self.engine.width//2, 30*data.ratio.y, 'Leaderboard', 72, (200, 170, 100), None, pivot=(0.5, 0)))
        
        self.back_button = Button(self.engine.width//2, 700*data.ratio.y, 200*data.ratio.x, 50*data.ratio.y, "Back", 40, None, pivot=(0.5, 0))
        self.back_button.set_on_click(lambda: self.engine.set_scene("main"))
        self.add_ui_element(self.back_button)
        
        self.add_ui_element(TextLabel(self.engine.width//2, 120*data.ratio.y, 'Rank - Name - Wins - Date', 36, (200, 170, 100), None, pivot=(0.5, 0)))
        self.leaderboard_scrolling = ScrollingFrame(self.engine.width//2, int(180*data.ratio.y), int(600*data.ratio.x), int(400*data.ratio.y), int(600*data.ratio.x), int(600*data.ratio.y), pivot=(0.5, 0))
        self.add_ui_element(self.leaderboard_scrolling)
        
    def load_leaderboard(self):
        data.load_leaderboard()
        # Sort by wins (descending)
        data.leaderboard['scores'].sort(key=lambda x: x['score'], reverse=True)
        
        for i, score in enumerate(data.leaderboard['scores'][:10]):  # Show top 10
            score_name:str = score['name']
            score_wins:int = score['score']
            score_date:str = score['date']
            
            self.leaderboard_scrolling.add_child(TextLabel(5*data.ratio.x, i*40*data.ratio.y, 
                f"{i+1}. {score_name} - {score_wins} wins - {score_date}", 28, 
                (200, 170, 100), None, pivot=(0, 0)))
            
    def reload_scores(self):
        self.leaderboard_scrolling.clear_children()
        self.load_leaderboard()
        
def main():
    fullscreen = False
    if len(sys.argv) >= 2:
        if sys.argv[1] == "--fullscreen":
            fullscreen = True
            
    engine = LunaEngine("TicTacToe", 1024, 768, fullscreen=fullscreen)
    pygame.display.set_icon(pygame.image.load(f"{os.path.abspath(os.path.dirname(__file__))}/icon.png"))
    engine.initialize()
    
    data.set_ratio(engine.width, engine.height)
    
    engine.add_scene("main", MainMenu)
    engine.add_scene("game", GameScene)
    engine.add_scene("leaderboard", LeaderboardScene)
    
    engine.set_scene("main")
    
    engine.run()
    
if __name__ == "__main__":
    main()