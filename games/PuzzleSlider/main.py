import sys, os, random, json, pygame, time
from lunaengine.core import Scene, LunaEngine
from lunaengine.ui import *
from lunaengine.backend import OpenGLRenderer
from typing import Literal, Optional, Tuple

class _Data:
    screen_width = 1024
    screen_height = 768
    leaderboard:dict = {}
    
    def __init__(self):
        self.load_leaderboard()
        
    def load_leaderboard(self):
        if os.path.exists(f'{os.path.dirname(__file__)}/leaderboard.json'):
            with open(f'{os.path.dirname(__file__)}/leaderboard.json', 'r') as f:
                self.leaderboard = json.load(f)
        else:
            self.leaderboard = {"scores": []}
            with open(f'{os.path.dirname(__file__)}/leaderboard.json', 'w+') as f:
                json.dump(self.leaderboard, f)
                f.close()
            
    def update_leaderboard(self):
        with open(f'{os.path.dirname(__file__)}/leaderboard.json', 'w+') as f:
            json.dump(self.leaderboard, f)
            f.close()
    
    def set_screen_size(self, width, height):
        self.screen_width = width
        self.screen_height = height
    
    @property
    def ratio(self) -> pygame.math.Vector2:
        return pygame.math.Vector2(self.screen_width / 1024, self.screen_height / 768)
    
    @ratio.getter
    def ratio(self) -> pygame.math.Vector2:
        return pygame.math.Vector2(self.screen_width / 1024, self.screen_height / 768)

data = _Data()

class SlidePuzzle:
    BLANK = None
    UP = 'up'
    DOWN = 'down'
    LEFT = 'left'
    RIGHT = 'right'
    
    def __init__(self, board_width: int, board_height: int, tile_size: int = 80):
        self.board_width = board_width
        self.board_height = board_height
        self.tile_size = tile_size
        self.board = []
        self.solved_board = []
        self.animating = False
        self.animation_progress = 0
        self.animation_direction = None
        self.animation_tile_pos = None
        self.animation_speed = 200
        self.message = "Click tile or press arrow keys to slide."
        
        self.BGCOLOR = (75, 75, 95)
        self.TILECOLOR = (190, 170, 100) 
        self.TEXTCOLOR = (50, 50, 60)
        self.BORDERCOLOR = (80, 70, 50)
        self.MESSAGECOLOR = (100, 90, 60)
        
        self.reset_board()
    
    def get_starting_board(self):
        """Return a board data structure with tiles in the solved state."""
        counter = 1
        board = []
        for x in range(self.board_width):
            column = []
            for y in range(self.board_height):
                column.append(counter)
                counter += self.board_width
            board.append(column)
            counter -= self.board_width * (self.board_height - 1) + self.board_width - 1
        
        board[self.board_width-1][self.board_height-1] = self.BLANK
        return board
    
    def reset_board(self):
        """Reset the board to solved state."""
        self.board = self.get_starting_board()
        self.solved_board = self.get_starting_board()
        self.animating = False
        self.message = "Click tile or press arrow keys to slide."
    
    def shuffle_board(self, num_moves: int = 50):
        """Shuffle the board by making random moves."""
        last_move = None
        for _ in range(num_moves):
            move = self.get_random_move(last_move)
            self.make_move(move)
            last_move = move
    
    def get_blank_position(self):
        """Return the x and y of board coordinates of the blank space."""
        for x in range(self.board_width):
            for y in range(self.board_height):
                if self.board[x][y] == self.BLANK:
                    return (x, y)
    
    def make_move(self, move):
        """Move a tile into the blank space."""
        if not self.is_valid_move(move):
            return
        
        blankx, blanky = self.get_blank_position()
        
        if move == self.UP:
            self.board[blankx][blanky], self.board[blankx][blanky + 1] = self.board[blankx][blanky + 1], self.board[blankx][blanky]
        elif move == self.DOWN:
            self.board[blankx][blanky], self.board[blankx][blanky - 1] = self.board[blankx][blanky - 1], self.board[blankx][blanky]
        elif move == self.LEFT:
            self.board[blankx][blanky], self.board[blankx + 1][blanky] = self.board[blankx + 1][blanky], self.board[blankx][blanky]
        elif move == self.RIGHT:
            self.board[blankx][blanky], self.board[blankx - 1][blanky] = self.board[blankx - 1][blanky], self.board[blankx][blanky]
    
    def is_valid_move(self, move):
        """Check if a move is valid."""
        if move is None:
            return False
            
        blankx, blanky = self.get_blank_position()
        return (move == self.UP and blanky != self.board_height - 1) or \
               (move == self.DOWN and blanky != 0) or \
               (move == self.LEFT and blankx != self.board_width - 1) or \
               (move == self.RIGHT and blankx != 0)
    
    def get_random_move(self, last_move=None):
        """Get a random valid move."""
        valid_moves = [self.UP, self.DOWN, self.LEFT, self.RIGHT]
        
        # Remove moves that would undo the last move or are invalid
        if last_move == self.UP or not self.is_valid_move(self.DOWN):
            valid_moves.remove(self.DOWN)
        if last_move == self.DOWN or not self.is_valid_move(self.UP):
            valid_moves.remove(self.UP)
        if last_move == self.LEFT or not self.is_valid_move(self.RIGHT):
            valid_moves.remove(self.RIGHT)
        if last_move == self.RIGHT or not self.is_valid_move(self.LEFT):
            valid_moves.remove(self.LEFT)
        
        return random.choice(valid_moves) if valid_moves else None
    
    def get_spot_clicked(self, x: int, y: int, board_rect: pygame.Rect):
        """Convert screen coordinates to board coordinates."""
        if not board_rect.collidepoint(x, y):
            return (None, None)
            
        # Adjust coordinates relative to board
        rel_x = x - board_rect.left
        rel_y = y - board_rect.top
        
        tile_x = rel_x // self.tile_size
        tile_y = rel_y // self.tile_size
        
        if tile_x < self.board_width and tile_y < self.board_height:
            return (tile_x, tile_y)
        return (None, None)
    
    def check_solved(self):
        """Check if the puzzle is solved."""
        return self.board == self.solved_board
    
    def handle_click(self, pos: Tuple[int, int], board_rect: pygame.Rect):
        """Handle mouse click to slide a tile."""
        if self.animating:
            return
            
        spotx, spoty = self.get_spot_clicked(pos[0], pos[1], board_rect)
        if (spotx, spoty) == (None, None):
            return
        
        blankx, blanky = self.get_blank_position()
        move = None
        
        if spotx == blankx + 1 and spoty == blanky:
            move = self.LEFT
        elif spotx == blankx - 1 and spoty == blanky:
            move = self.RIGHT
        elif spotx == blankx and spoty == blanky + 1:
            move = self.UP
        elif spotx == blankx and spoty == blanky - 1:
            move = self.DOWN
        
        if move and self.is_valid_move(move):
            self.start_animation(move)
    
    def handle_key(self, key):
        """Handle keyboard input."""
        if self.animating:
            return
            
        move = None
        if key in (pygame.K_LEFT, pygame.K_a):
            move = self.LEFT
        elif key in (pygame.K_RIGHT, pygame.K_d):
            move = self.RIGHT
        elif key in (pygame.K_UP, pygame.K_w):
            move = self.UP
        elif key in (pygame.K_DOWN, pygame.K_s):
            move = self.DOWN
        
        if move and self.is_valid_move(move):
            self.start_animation(move)
    
    def start_animation(self, move):
        """Start the slide animation."""
        self.animating = True
        self.animation_progress = 0
        self.animation_direction = move
        
        blankx, blanky = self.get_blank_position()
        if move == self.UP:
            self.animation_tile_pos = (blankx, blanky + 1)
        elif move == self.DOWN:
            self.animation_tile_pos = (blankx, blanky - 1)
        elif move == self.LEFT:
            self.animation_tile_pos = (blankx + 1, blanky)
        elif move == self.RIGHT:
            self.animation_tile_pos = (blankx - 1, blanky)
    
    def update_animation(self, dt: float):
        """Update animation progress."""
        if not self.animating:
            return
            
        self.animation_progress += self.animation_speed * dt
        if self.animation_progress >= self.tile_size:
            self.animating = False
            self.animation_progress = 0
            self.make_move(self.animation_direction)
            
            if self.check_solved():
                self.message = "Solved!"
    
    def get_board_rect(self, center_x: int, center_y: int):
        """Get the rectangle for drawing the board."""
        width = self.board_width * self.tile_size
        height = self.board_height * self.tile_size
        return pygame.Rect(
            center_x - width // 2,
            center_y - height // 2,
            width,
            height
        )

class MainMenu(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.setup_ui()
        
    def setup_ui(self):
        ThemeManager.set_current_theme(ThemeType.SUNSET)
        title = TextLabel(self.engine.width//2, 100*data.ratio.y, "Puzzle Slider", 86, (50, 50, 60), None, root_point=(0.5, 0))
        hover_anim = Tween.create(title)
        hover_anim.to(
            y = 60 * data.ratio.y,
            duration = 2,
            easing=EasingType.LINEAR
        )
        hover_anim.set_loops(-1, True)
        self.engine.animation_handler.add('title_hover_anim', hover_anim, True)
        self.add_ui_element(title)
        
        self.play_button = Button(self.engine.width//2, 250*data.ratio.y, 200*data.ratio.x, 65*data.ratio.y, "Play", 50, None, root_point=(0.5, 0))
        self.play_button.set_on_click(self.play)
        self.add_ui_element(self.play_button)
        
        self.difficulty_dropdown = Dropdown(self.engine.width-200*data.ratio.x, 225*data.ratio.y, 200*data.ratio.x, 50*data.ratio.y, ['Easy', 'Normal', 'Hard'], 40, None, root_point=(1, 0))
        self.add_ui_element(self.difficulty_dropdown)
        
        self.leaderboard_button = Button(self.engine.width//2, 330*data.ratio.y, 200*data.ratio.x, 50*data.ratio.y, "Leaderboard", 40, None, root_point=(0.5, 0))
        self.leaderboard_button.set_on_click(self.leaderboard)
        self.add_ui_element(self.leaderboard_button)
        
        self.exit_button = Button(self.engine.width//2, 390*data.ratio.y, 200*data.ratio.x, 50*data.ratio.y, "Exit", 40, None, root_point=(0.5, 0))
        self.exit_button.set_on_click(self.quit)
        self.add_ui_element(self.exit_button)
        
    def play(self):
        self.engine.add_scene('game', GameScene, self.difficulty_dropdown.selected_index)
        self.engine.set_scene('game')
        
    def leaderboard(self):
        self.engine.set_scene("leaderboard")
        
    def quit(self):
        self.engine.shutdown()
    
    def on_enter(self, previous_scene = None):
        return super().on_enter(previous_scene)
    
    def on_exit(self, next_scene = None):
        return super().on_exit(next_scene)
        
    def update(self, dt):
        return super().update(dt)
    
    def render(self, renderer:OpenGLRenderer):
        renderer.fill_screen(ThemeManager.get_color('background'))

class GameScene(Scene):
    def __init__(self, engine, difficulty:int=0):
        super().__init__(engine)
        self.difficulty = difficulty
        
        # Set grid size based on difficulty
        if difficulty == 0:
            grid_size = (4, 4)
            tile_size = 80
        elif difficulty == 1:
            grid_size = (5, 5)
            tile_size = 64
        elif difficulty == 2:
            grid_size = (6, 6)
            tile_size = 53
        else:
            raise ValueError("Invalid difficulty")
        
        self.grid_size = grid_size
        self.start_time = time.time()
        self.moves_count = 0
        self.solved = False
        
        # Create the puzzle
        self.puzzle = SlidePuzzle(grid_size[0], grid_size[1], tile_size)
        self.puzzle.shuffle_board(100)  # Shuffle with 100 moves
        
        self.setup_ui()
        
    def on_enter(self, previous_scene = None):
        self.start_time = time.time()
        self.moves_count = 0
        self.solved = False
        
    def setup_ui(self):
        # Timer
        self.timer = TextLabel(self.engine.width//2, 50*data.ratio.y, "00:00", 50, (0, 0, 0), None, root_point=(0.5, 0))
        self.add_ui_element(self.timer)
        
        # Difficulty label
        difficulty_names = ['Easy', 'Normal', 'Hard']
        self.add_ui_element(TextLabel(self.engine.width//2, 110*data.ratio.y, 
                                     difficulty_names[self.difficulty], 24, (200, 170, 100), 
                                     None, root_point=(0.5, 0)))
        
        # Moves counter
        self.moves_label = TextLabel(self.engine.width//2, 150*data.ratio.y, "Moves: 0", 24, (200, 170, 100), 
                                     None, root_point=(0.5, 0))
        self.add_ui_element(self.moves_label)
        
        # Message display
        self.message_label = TextLabel(self.engine.width//2, 180*data.ratio.y, 
                                      "Click tiles to slide", 20, self.puzzle.MESSAGECOLOR, 
                                      None, root_point=(0.5, 0))
        self.add_ui_element(self.message_label)
        
        # Control buttons
        self.reset_button = Button(self.engine.width - 150*data.ratio.x, 50*data.ratio.y, 
                                  120*data.ratio.x, 40*data.ratio.y, "Reset", 30, 
                                  None, root_point=(1, 0))
        self.reset_button.set_on_click(self.reset_puzzle)
        self.add_ui_element(self.reset_button)
        
        self.new_button = Button(self.engine.width - 150*data.ratio.x, 100*data.ratio.y, 
                               120*data.ratio.x, 40*data.ratio.y, "New Game", 30, 
                               None, root_point=(1, 0))
        self.new_button.set_on_click(self.new_puzzle)
        self.add_ui_element(self.new_button)
        
        self.menu_button = Button(self.engine.width - 150*data.ratio.x, 150*data.ratio.y, 
                                120*data.ratio.x, 40*data.ratio.y, "Menu", 30, 
                                None, root_point=(1, 0))
        self.menu_button.set_on_click(self.go_to_menu)
        self.add_ui_element(self.menu_button)
        
        # Solved message (initially hidden)
        self.solved_message = TextLabel(self.engine.width//2, 250*data.ratio.y, 
                                       "Puzzle Solved! 🎉", 48, (0, 255, 0), 
                                       None, root_point=(0.5, 0))
        self.solved_message.visible = False
        
        # Save score button (shown when solved)
        self.save_button = Button(self.engine.width//2, 320*data.ratio.y, 
                                200*data.ratio.x, 50*data.ratio.y, "Save Score", 40, 
                                None, root_point=(0.5, 0))
        self.save_button.set_on_click(self.save_score)
        self.save_button.visible = False
        
        self.add_ui_element(self.solved_message)
        self.add_ui_element(self.save_button)

        @self.engine.on_event(pygame.MOUSEBUTTONDOWN)
        def handle_click(event):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Check if click is on puzzle board
                board_rect = self.puzzle.get_board_rect(self.engine.width//2, 
                                                    self.engine.height//2 + 50*data.ratio.y)
                self.puzzle.handle_click(event.pos, board_rect)
                if not self.solved and self.puzzle.animating:
                    self.moves_count += 1
        @self.engine.on_event(pygame.KEYDOWN)
        def handle_event(event):
            """Handle pygame events."""
            if event.type == pygame.KEYDOWN:
                if not self.solved:
                    self.puzzle.handle_key(event.key)
                    if self.puzzle.animating:
                        self.moves_count += 1
        
    def update(self, dt):
        # Update timer
        elapsed = int(time.time() - self.start_time)
        minutes = elapsed // 60
        seconds = elapsed % 60
        self.timer.set_text(f"{minutes:02d}:{seconds:02d}")
        
        # Update puzzle animation
        self.puzzle.update_animation(dt)
        
        # Update moves counter
        self.moves_label.set_text(f"Moves: {self.moves_count}")
        
        # Update message
        self.message_label.set_text(self.puzzle.message)
        
        # Check if solved
        if not self.solved and self.puzzle.check_solved():
            self.solved = True
            self.solved_message.visible = True
            self.save_button.visible = True
            self.puzzle.message = "Solved!"
            
            # Pulse animation for solved message
            solved_anim = Tween.create(self.solved_message)
            solved_anim.to(
                scale = 1.2,
                duration = 0.5,
                easing=EasingType.EASE_IN_OUT_SINE
            )
            solved_anim.set_loops(-1, True)
            self.engine.animation_handler.add('solved_pulse', solved_anim, True)
        
        super().update(dt)
    
    def render(self, renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))
        
        # Draw puzzle board
        board_center_x = self.engine.width // 2
        board_center_y = self.engine.height // 2 + 50 * data.ratio.y
        board_rect = self.puzzle.get_board_rect(board_center_x, board_center_y)
        
        # Draw border
        renderer.draw_rect(board_rect.left, board_rect.top, board_rect.width, board_rect.height, self.puzzle.BORDERCOLOR, border_width=4)
        
        # Draw board background
        renderer.draw_rect(board_rect.left, board_rect.top, board_rect.width, board_rect.height, self.puzzle.BGCOLOR)
        
        # Draw tiles
        tile_size = self.puzzle.tile_size
        for x in range(self.puzzle.board_width):
            for y in range(self.puzzle.board_height):
                # Detect if it's animating
                if self.puzzle.animating and self.puzzle.animation_tile_pos == (x, y):
                    continue
                tile_value = self.puzzle.board[x][y]
                if tile_value != self.puzzle.BLANK:
                    tile_rect = pygame.Rect(
                        board_rect.left + x * tile_size,
                        board_rect.top + y * tile_size,
                        tile_size - 2,
                        tile_size - 2
                    )
                    
                    # Draw tile
                    renderer.draw_rect(tile_rect.left, tile_rect.top, tile_rect.width, tile_rect.height, self.puzzle.TILECOLOR)
                    
                    # Draw tile number
                    renderer.draw_text(str(tile_value), tile_rect.centerx, tile_rect.centery, self.puzzle.TEXTCOLOR, FontManager.get_font(None, 36))
        
        # Draw animation if active
        if self.puzzle.animating and self.puzzle.animation_tile_pos:
            anim_x, anim_y = self.puzzle.animation_tile_pos
            tile_value = self.puzzle.board[anim_x][anim_y]
            
            # Calculate animated position
            base_x = board_rect.left + anim_x * tile_size
            base_y = board_rect.top + anim_y * tile_size
            
            offset_x, offset_y = 0, 0
            if self.puzzle.animation_direction == self.puzzle.LEFT:
                offset_x = -self.puzzle.animation_progress
            elif self.puzzle.animation_direction == self.puzzle.RIGHT:
                offset_x = self.puzzle.animation_progress
            elif self.puzzle.animation_direction == self.puzzle.UP:
                offset_y = -self.puzzle.animation_progress
            elif self.puzzle.animation_direction == self.puzzle.DOWN:
                offset_y = self.puzzle.animation_progress
            
            anim_rect = pygame.Rect(
                base_x + offset_x,
                base_y + offset_y,
                tile_size - 2,
                tile_size - 2
            )
            
            # Draw animated tile
            renderer.draw_rect(anim_rect.left, anim_rect.top, anim_rect.width, anim_rect.height, self.puzzle.TILECOLOR)
            
            # Draw animated tile number
            renderer.draw_text(str(tile_value), anim_rect.centerx, anim_rect.centery, self.puzzle.TEXTCOLOR, FontManager.get_font(None, 36))
        
        super().render(renderer)
    
    def reset_puzzle(self):
        """Reset the current puzzle."""
        self.puzzle.reset_board()
        self.puzzle.shuffle_board(100)
        self.moves_count = 0
        self.start_time = time.time()
        self.solved = False
        self.solved_message.visible = False
        self.save_button.visible = False
        if self.engine.animation_handler.get('solved_pulse'):
            self.engine.animation_handler.remove('solved_pulse')
    
    def new_puzzle(self):
        """Create a new shuffled puzzle."""
        self.puzzle.shuffle_board(100)
        self.moves_count = 0
        self.start_time = time.time()
        self.solved = False
        self.solved_message.visible = False
        self.save_button.visible = False
        if self.engine.animation_handler.get('solved_pulse'):
            self.engine.animation_handler.remove('solved_pulse')
    
    def go_to_menu(self):
        """Return to main menu."""
        self.engine.set_scene("main")
    
    def save_score(self):
        """Save score to leaderboard."""
        if self.solved:
            elapsed = int(time.time() - self.start_time)
            minutes = elapsed // 60
            seconds = elapsed % 60
            
            # For now, just print the score. You can implement a dialog for name entry
            print(f"Score saved: {self.moves_count} moves in {minutes:02d}:{seconds:02d}")
            
            # In a real implementation, you'd show a dialog for name entry
            # and then save to leaderboard.json
    
class LeaderboardScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.setup_ui()
        
    def on_enter(self, previous_scene = None):
        self.reload_scores()
        
    def setup_ui(self):
        ThemeManager.set_current_theme(ThemeType.SUNSET)
        self.add_ui_element(TextLabel(self.engine.width//2, 30*data.ratio.y, 'Leaderboard', 72, (200, 170, 100), None, root_point=(0.5, 0)))
    
        self.add_ui_element(TextLabel(self.engine.width//2, 120*data.ratio.y, 'Rank - Name - Score - Date - Difficulty', 36, (200, 170, 100), None, root_point=(0.5, 0)))    
        self.scrolling_frame = ScrollingFrame(self.engine.width//2, int(180*data.ratio.y), int(600*data.ratio.x), int(400*data.ratio.y), int(600*data.ratio.x), int(600*data.ratio.y), root_point=(0.5, 0))
        self.add_ui_element(self.scrolling_frame)
        
        # Back button
        self.back_button = Button(100*data.ratio.x, 50*data.ratio.y, 
                                120*data.ratio.x, 50*data.ratio.y, "Back", 40, 
                                None, root_point=(0, 0))
        self.back_button.set_on_click(self.go_back)
        self.add_ui_element(self.back_button)
    
    def load_scores(self):
        for i, score in enumerate(data.leaderboard['scores']):
            user_name:str = score['name']
            user_score:str = score['score']
            user_score_date:str = score['date']
            user_difficulty:str = score['difficulty']
            self.scrolling_frame.add_child(TextLabel(5*data.ratio.x, i*30*data.ratio.y, f"{i+1} - {user_name} - {user_score} - {user_score_date} - {user_difficulty}", 28, (200, 170, 100), None, root_point=(0, 0)))
            
    def reload_scores(self):
        self.scrolling_frame.clear_children()
        data.load_leaderboard()
        self.load_scores()
        
    def go_back(self):
        self.engine.set_scene("main")
    
    def render(self, renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))

def main():
    fullscreen = False
    if len(sys.argv) >= 2:
        if sys.argv[1] == "--fullscreen":
            fullscreen = True
    
    engine = LunaEngine("Puzzle Slider", 1024, 768, fullscreen=fullscreen)
    pygame.display.set_icon(pygame.image.load(f"{os.path.dirname(__file__)}/icon.png"))
    engine.initialize()
    
    data.set_screen_size(engine.width, engine.height)
    
    engine.add_scene("main", MainMenu)
    engine.add_scene("leaderboard", LeaderboardScene)
    
    engine.set_scene("main")
    
    engine.run()
    
if __name__ == "__main__":
    main()