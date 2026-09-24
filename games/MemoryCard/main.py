"""
Memory Card Game - LunaEngine Implementation
A classic memory card matching game with difficulty settings.
"""

import sys
import os
import random
import json
import pygame
import math
from datetime import datetime
from typing import List, Tuple, Optional
from pathlib import Path

from lunaengine.core import Scene, LunaEngine, Renderer
from lunaengine.ui import *
from lunaengine.ui.elements.base import FontManager
from lunaengine.backend import OpenGLRenderer

# ---------- Leaderboard Manager ----------
class LeaderboardManager:
    """Leaderboard handler for Memory Card game"""
    
    def __init__(self, filename: str = "memory_leaderboard.json"):
        self.filename = filename
        self.scores = self.load_scores()
    
    def load_scores(self) -> list:
        """Load scores from JSON file"""
        try:
            filepath = Path(os.path.abspath(os.path.dirname(__file__))) / self.filename
            if filepath.exists():
                with open(filepath, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading leaderboard: {e}")
        return []
    
    def save_scores(self):
        """Save scores to JSON file"""
        try:
            filepath = Path(os.path.abspath(os.path.dirname(__file__))) / self.filename
            with open(filepath, 'w') as f:
                json.dump(self.scores, f, indent=2)
        except Exception as e:
            print(f"Error saving leaderboard: {e}")
    
    def add_score(self, name: str, difficulty: str, pairs: int, time_left: float, matches: int):
        """Add a new score to the leaderboard"""
        self.scores.append({
            "name": name,
            "difficulty": difficulty,
            "pairs": pairs,
            "time_left": round(time_left, 1),
            "matches": matches,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        self.scores.sort(key=lambda x: x["pairs"], reverse=True)
        self.scores = self.scores[:20]
        self.save_scores()
    
    def get_top_scores(self, count: int = 10) -> list:
        """Get top N scores"""
        return self.scores[:count]

LDM = LeaderboardManager()


# ---------- Card Class ----------
class Card:
    """Individual memory card"""
    
    CARD_WIDTH = 80
    CARD_HEIGHT = 120
    
    def __init__(self, x: int, y: int, number: int, color: str):
        self.x = x
        self.y = y
        self.number = number
        self.color = color
        self.face_up = False
        self.matched = False
        self.rect = pygame.Rect(x, y, self.CARD_WIDTH, self.CARD_HEIGHT)
        self.display_number = self._get_display_number()
        self.display_color = (200, 50, 50) if color == 'red' else (50, 50, 50)
    
    def _get_display_number(self) -> str:
        if self.number == 1:
            return "A"
        elif self.number == 11:
            return "J"
        elif self.number == 12:
            return "Q"
        elif self.number == 13:
            return "K"
        return str(self.number)
    
    def get_pair_id(self) -> Tuple[int, str]:
        return (self.number, self.color)
    
    def flip(self):
        self.face_up = not self.face_up
    
    def is_face_up(self) -> bool:
        return self.face_up
    
    def is_matched(self) -> bool:
        return self.matched
    
    def set_matched(self, matched: bool = True):
        self.matched = matched
    
    def contains(self, pos: Tuple[int, int]) -> bool:
        return self.rect.collidepoint(pos)
    
    def draw(self, renderer: Renderer):
        x, y = self.x, self.y
        w, h = self.CARD_WIDTH, self.CARD_HEIGHT
        
        if self.matched:
            renderer.draw_rect(x, y, w, h, (60, 160, 60), corner_radius=8)
            renderer.draw_rect(x, y, w, h, (100, 200, 100), fill=False, corner_radius=8)
            font = FontManager.get_font('luckiestguy', 28, bold=True)
            renderer.draw_text("OK", x + w//2, y + h//2, (255, 255, 255), font, pivot=(0.5, 0.5))
            return
        
        if self.face_up:
            renderer.draw_rect(x, y, w, h, (255, 255, 255), corner_radius=8)
            renderer.draw_rect(x, y, w, h, (200, 200, 200), fill=False, corner_radius=8)
            
            font_size = 36 if self.number <= 10 else 28
            font = FontManager.get_font('luckiestguy', font_size, bold=True)
            renderer.draw_text(self.display_number, x + w//2, y + h//2 - 10,
                               self.display_color, font, pivot=(0.5, 0.5))
            
            suit_symbol = "♥" if self.color == 'red' else "♠"
            font_suit = FontManager.get_font('luckiestguy', 20)
            renderer.draw_text(suit_symbol, x + w//2, y + h//2 + 30,
                               self.display_color, font_suit, pivot=(0.5, 0.5))
        else:
            renderer.draw_rect(x, y, w, h, (50, 80, 150), corner_radius=8)
            renderer.draw_rect(x, y, w, h, (80, 110, 200), fill=False, corner_radius=8)
            renderer.draw_rect(x, y, w, h, (60, 90, 160), fill=False, corner_radius=6, border_width=2)
            font = FontManager.get_font('luckiestguy', 40, bold=True)
            renderer.draw_text("?", x + w//2, y + h//2, (200, 220, 255), font, pivot=(0.5, 0.5))


# ---------- Main Menu Scene ----------
class MainMenu(Scene):
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        self.ratio = pygame.math.Vector2(engine.width/1024, engine.height/768)
        self.username = ""
        self.difficulty = "Normal"
        self.difficulty_index = 1
        
        self.setup_ui()
        
        @engine.on_event(pygame.KEYDOWN)
        def on_key(event):
            if event.key == pygame.K_F5:
                self.reload_leaderboard()
    
    def on_enter(self, previous_scene: str = None):
        ThemeManager.set_current_theme(ThemeType.SUNSET)
        self.engine._update_all_ui_themes(ThemeManager.get_current_theme())
        self.reload_leaderboard()
        return super().on_enter(previous_scene)
    
    def setup_ui(self):
        title = TextLabel(self.engine.width//2, 50 * self.ratio.y,
                          "Memory Card", 72, font_name='luckiestguy', pivot=(0.5, 0))
        self.add_ui_element(title)
        
        username_label = TextLabel(self.engine.width//2 - 150 * self.ratio.x, 145 * self.ratio.y,
                                   "Username:", 28, font_name='luckiestguy', pivot=(0.5, 0))
        self.add_ui_element(username_label)
        
        self.username_box = TextBox(self.engine.width//2 + 50 * self.ratio.x, 140 * self.ratio.y,
                                    200 * self.ratio.x, 40 * self.ratio.y,
                                    self.username, 28, font_name='luckiestguy',
                                    pivot=(0.5, 0), max_length=20)
        self.username_box.set_on_text_changed(lambda text: setattr(self, 'username', text))
        self.add_ui_element(self.username_box)
        
        diff_label = TextLabel(self.engine.width//2 - 150 * self.ratio.x, 195 * self.ratio.y,
                               "Difficulty:", 28, font_name='luckiestguy', pivot=(0.5, 0))
        self.add_ui_element(diff_label)
        
        self.diff_dropdown = Dropdown(self.engine.width//2 + 50 * self.ratio.x, 190 * self.ratio.y,
                                      200 * self.ratio.x, 40 * self.ratio.y,
                                      ['Easy', 'Normal', 'Hard'], 28,
                                      font_name='luckiestguy', pivot=(0.5, 0))
        self.diff_dropdown.set_selected_index(self.difficulty_index)
        self.diff_dropdown.set_on_selection_changed(self._on_difficulty_changed)
        self.add_ui_element(self.diff_dropdown)
        
        play_btn = Button(self.engine.width//2, 260 * self.ratio.y,
                          250 * self.ratio.x, 60 * self.ratio.y,
                          "Play", 50, font_name='luckiestguy', pivot=(0.5, 0))
        play_btn.set_on_click(self.start_game)
        self.add_ui_element(play_btn)
        
        exit_btn = Button(self.engine.width//2, 335 * self.ratio.y,
                          200 * self.ratio.x, 50 * self.ratio.y,
                          "Exit", 40, font_name='luckiestguy', pivot=(0.5, 0))
        exit_btn.set_on_click(lambda: setattr(self.engine, 'running', False))
        self.add_ui_element(exit_btn)
        
        lb_title = TextLabel(self.engine.width//2, 410 * self.ratio.y,
                             "Leaderboard", 40, font_name='luckiestguy', pivot=(0.5, 0))
        self.add_ui_element(lb_title)
        
        self.leader_frame = ScrollingFrame(self.engine.width//2, 460 * self.ratio.y,
                                           600 * self.ratio.x, 280 * self.ratio.y,
                                           580 * self.ratio.x, 500 * self.ratio.y,
                                           pivot=(0.5, 0))
        self.add_ui_element(self.leader_frame)
        
        self.leader_table = Table(10 * self.ratio.x, 10 * self.ratio.y,
                                  560 * self.ratio.x, 500 * self.ratio.y,
                                  ['Name', 'Difficulty', 'Pairs', 'Time', 'Date'])
        self.leader_frame.add_child(self.leader_table)
        
        refresh_btn = Button(self.engine.width - 100 * self.ratio.x, 420 * self.ratio.y,
                             80 * self.ratio.x, 30 * self.ratio.y,
                             "R", 24, font_name='luckiestguy', pivot=(0.5, 0))
        refresh_btn.set_on_click(self.reload_leaderboard)
        self.add_ui_element(refresh_btn)
    
    def _on_difficulty_changed(self, index: int, value: str):
        self.difficulty_index = index
        self.difficulty = value
    
    def start_game(self):
        if not self.username.strip():
            self.username = "Player"
            self.username_box.set_text("Player")
        
        LDM.current_username = self.username
        
        if self.difficulty == "Easy":
            pairs, time_limit, time_bonus = 3, 15, 2
        elif self.difficulty == "Hard":
            pairs, time_limit, time_bonus = 7, 10, 1
        else:  # Normal
            pairs, time_limit, time_bonus = 5, 12, 2
        
        game_scene = GameScene(self.engine, pairs, time_limit, time_bonus, self.difficulty)
        self.engine.add_scene("game", game_scene, replace=True)
        self.engine.set_scene("game")
    
    def reload_leaderboard(self):
        self.leader_table.clear()
        for score in LDM.get_top_scores(30):
            self.leader_table.add_row([
                score.get('name', 'Unknown'),
                score.get('difficulty', 'Normal'),
                str(score.get('pairs', 0)),
                f"{score.get('time_left', 0):.1f}s",
                score.get('date', '')
            ])
    
    def update(self, dt: float):
        self.ratio = pygame.math.Vector2(self.engine.width/1024, self.engine.height/768)
    
    def render(self, renderer: Renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))


# ---------- Game Scene ----------
class GameScene(Scene):
    def __init__(self, engine: LunaEngine, pairs: int = 5, time_limit: int = 12,
                 time_bonus: int = 2, difficulty: str = "Normal"):
        super().__init__(engine)
        self.pairs = pairs
        self.time_limit = time_limit
        self.time_bonus = time_bonus
        self.difficulty = difficulty
        self.ratio = pygame.math.Vector2(engine.width/1024, engine.height/768)
        
        # Initialize game state
        self.cards: List[Card] = []
        self.selected_cards: List[Card] = []
        self.matched_pairs = 0
        self.total_pairs = pairs
        self.score = 0
        self.time_remaining = time_limit
        self.game_over = False
        self.round = 1
        self.is_processing = False
        self.processing_timer = 0.0
        
        # UI must be created before generating the board
        self.setup_ui()
        self.setup_game()   # now generates board and updates UI
        
        @engine.on_event(pygame.KEYDOWN)
        def on_key(event):
            if event.key == pygame.K_ESCAPE:
                self.engine.set_scene("main")
            elif event.key == pygame.K_r and self.game_over:
                self.restart_game()
                
        @engine.on_event(pygame.MOUSEBUTTONUP)
        def on_mouse(event):
            self.handle_card_click(self.engine.input_state.mouse_pos)
    
    def setup_game(self):
        """Set up initial game board and reset state"""
        self.cards.clear()
        self.selected_cards.clear()
        self.matched_pairs = 0
        self.time_remaining = self.time_limit
        self.game_over = False
        self.is_processing = False
        self.processing_timer = 0.0
        self.round = 1
        
        # Generate board and update UI
        self._generate_board()
        self._update_ui()
    
    def _generate_board(self):
        """Generate a new board with fresh pairs (does NOT update UI)"""
        card_pairs = self._generate_card_pairs(self.pairs)
        random.shuffle(card_pairs)
        
        cols = math.ceil(math.sqrt(self.pairs * 2))
        rows = math.ceil((self.pairs * 2) / cols)
        if cols * rows < self.pairs * 2:
            cols += 1
            rows = math.ceil((self.pairs * 2) / cols)
        
        card_width = Card.CARD_WIDTH
        card_height = Card.CARD_HEIGHT
        spacing = 15
        total_width = cols * card_width + (cols - 1) * spacing
        total_height = rows * card_height + (rows - 1) * spacing
        start_x = (self.engine.width - total_width) // 2
        start_y = (self.engine.height - total_height) // 2 + 30
        
        for idx, (number, color) in enumerate(card_pairs):
            row = idx // cols
            col = idx % cols
            x = start_x + col * (card_width + spacing)
            y = start_y + row * (card_height + spacing)
            self.cards.append(Card(x, y, number, color))
        
        # Reset counters for this round
        self.matched_pairs = 0
        self.total_pairs = self.pairs
    
    def _generate_card_pairs(self, num_pairs: int) -> List[Tuple[int, str]]:
        numbers = list(range(1, 14))
        colors = ['red', 'black']
        available = [(n, c) for n in numbers for c in colors]
        random.shuffle(available)
        selected = available[:num_pairs]
        return selected * 2  # each pair appears twice
    
    def _update_ui(self):
        """Update all UI labels to reflect current state"""
        self.score_label.set_text(f"Score: {self.score}")
        self.pairs_label.set_text(f"Pairs: {self.matched_pairs}/{self.total_pairs}")
        self.timer_label.set_text(f"Time: {self.time_remaining:.1f}s")
        self.round_label.set_text(f"Round: {self.round}")
    
    def setup_ui(self):
        self.score_label = TextLabel(20 * self.ratio.x, 20 * self.ratio.y,
                                     f"Score: {self.score}", 32,
                                     font_name='luckiestguy', pivot=(0, 0))
        self.add_ui_element(self.score_label)
        
        self.pairs_label = TextLabel(20 * self.ratio.x, 60 * self.ratio.y,
                                     f"Pairs: {self.matched_pairs}/{self.total_pairs}", 28,
                                     font_name='luckiestguy', pivot=(0, 0))
        self.add_ui_element(self.pairs_label)
        
        self.timer_label = TextLabel(self.engine.width - 20 * self.ratio.x, 20 * self.ratio.y,
                                     f"Time: {self.time_remaining:.1f}s", 32,
                                     font_name='luckiestguy', pivot=(1, 0))
        self.add_ui_element(self.timer_label)
        
        self.round_label = TextLabel(self.engine.width - 20 * self.ratio.x, 60 * self.ratio.y,
                                     f"Round: {self.round}", 24,
                                     font_name='luckiestguy', pivot=(1, 0))
        self.add_ui_element(self.round_label)
        
        diff_label = TextLabel(self.engine.width - 20 * self.ratio.x, 90 * self.ratio.y,
                               f"Difficulty: {self.difficulty}", 20,
                               font_name='luckiestguy', pivot=(1, 0))
        self.add_ui_element(diff_label)
        
        menu_btn = Button(20 * self.ratio.x, 100 * self.ratio.y,
                          80 * self.ratio.x, 30 * self.ratio.y,
                          "Menu", 20, font_name='luckiestguy', pivot=(0, 0))
        menu_btn.set_on_click(lambda: self.engine.set_scene("main"))
        self.add_ui_element(menu_btn)
        
        restart_btn = Button(110 * self.ratio.x, 100 * self.ratio.y,
                             80 * self.ratio.x, 30 * self.ratio.y,
                             "Restart", 20, font_name='luckiestguy', pivot=(0, 0))
        restart_btn.set_on_click(self.restart_game)
        self.add_ui_element(restart_btn)
        
        self.game_over_label = TextLabel(self.engine.width//2, self.engine.height//2 - 60,
                                         "GAME OVER", 64, font_name='luckiestguy', pivot=(0.5, 0.5))
        self.game_over_label.visible = False
        self.add_ui_element(self.game_over_label)
        
        self.final_score_label = TextLabel(self.engine.width//2, self.engine.height//2 + 10,
                                           f"Pairs Found: {self.matched_pairs}/{self.total_pairs}", 36,
                                           font_name='luckiestguy', pivot=(0.5, 0.5))
        self.final_score_label.visible = False
        self.add_ui_element(self.final_score_label)
        
        self.game_over_menu_btn = Button(self.engine.width//2 - 110, self.engine.height//2 + 70,
                                         100 * self.ratio.x, 40 * self.ratio.y,
                                         "Menu", 28, font_name='luckiestguy', pivot=(0.5, 0.5))
        self.game_over_menu_btn.visible = False
        self.game_over_menu_btn.set_on_click(lambda: self.engine.set_scene("main"))
        self.add_ui_element(self.game_over_menu_btn)
        
        self.game_over_restart_btn = Button(self.engine.width//2 + 110, self.engine.height//2 + 70,
                                            100 * self.ratio.x, 40 * self.ratio.y,
                                            "Restart", 28, font_name='luckiestguy', pivot=(0.5, 0.5))
        self.game_over_restart_btn.visible = False
        self.game_over_restart_btn.set_on_click(self.restart_game)
        self.add_ui_element(self.game_over_restart_btn)
    
    def restart_game(self):
        self.setup_game()
        self.score = 0
        self.game_over = False
        self.game_over_label.visible = False
        self.final_score_label.visible = False
        self.game_over_menu_btn.visible = False
        self.game_over_restart_btn.visible = False
        self._update_ui()
    
    def next_round(self):
        """Advance to the next round with new cards"""
        self.round += 1
        self.time_remaining = self.time_limit  # reset timer to base
        self.cards.clear()
        self.selected_cards.clear()
        self.is_processing = False
        self.processing_timer = 0.0
        self._generate_board()
        self._update_ui()
    
    def handle_card_click(self, pos: Tuple[int, int]):
        if self.game_over or self.is_processing:
            return
        
        clicked = None
        for card in self.cards:
            if card.contains(pos) and not card.is_matched() and not card.is_face_up():
                clicked = card
                break
        
        if clicked is None:
            return
        
        # Debug: print clicked card info
        print(f"Card clicked: {clicked.display_number} {clicked.color}")
        
        clicked.flip()
        self.selected_cards.append(clicked)
        
        if len(self.selected_cards) == 2:
            self.is_processing = True
            self.processing_timer = 0.0
            self._check_match()
    
    def _check_match(self):
        c1, c2 = self.selected_cards
        if c1.get_pair_id() == c2.get_pair_id():
            c1.set_matched(True)
            c2.set_matched(True)
            self.matched_pairs += 1
            self.score += 10
            self.time_remaining += self.time_bonus
            
            self._update_ui()
            
            self.selected_cards.clear()
            self.is_processing = False
            
            if self.matched_pairs == self.total_pairs:
                # Start next round
                self.next_round()
        # else: wait for flip-back
    
    def _flip_back_cards(self):
        for card in self.selected_cards:
            card.flip()
        self.selected_cards.clear()
        self.is_processing = False
    
    def _show_game_over(self):
        self.game_over_label.visible = True
        self.final_score_label.visible = True
        self.final_score_label.set_text(
            f"Pairs Found: {self.matched_pairs}/{self.total_pairs}  |  Score: {self.score}"
        )
        self.game_over_menu_btn.visible = True
        self.game_over_restart_btn.visible = True
        # Save score to leaderboard (using current round pairs found)
        LDM.add_score(LDM.current_username, self.difficulty,
                      self.matched_pairs, self.time_remaining, self.score)
    
    def update(self, dt: float):
        self.ratio = pygame.math.Vector2(self.engine.width/1024, self.engine.height/768)
        
        if not self.game_over:
            self.time_remaining -= dt
            self.timer_label.set_text(f"Time: {self.time_remaining:.1f}s")
            if self.time_remaining <= 0:
                self.time_remaining = 0
                self.game_over = True
                self._show_game_over()
        
        if self.is_processing:
            self.processing_timer += dt
            if self.processing_timer >= 0.8:
                self._flip_back_cards()
    
    def render(self, renderer: Renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))
        for card in self.cards:
            card.draw(renderer)
        super().render(renderer)
    
    def on_enter(self, previous_scene: str = None):
        ThemeManager.set_current_theme(ThemeType.SUNSET)
        self.engine._update_all_ui_themes(ThemeManager.get_current_theme())
        return super().on_enter(previous_scene)


# ---------- Main ----------
def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', default=False)
    parser.add_argument('--fullscreen', action='store_true', default=False)
    args = parser.parse_args(sys.argv[1:])
    
    engine = LunaEngine('Memory Card', 1024, 768, debug=args.debug, fullscreen=args.fullscreen)
    engine.update_ratio(1024, 768)
    engine.set_global_theme(ThemeType.SUNSET)
    engine.set_dark_mode(False)
    
    engine.atlas.add_folder('root', Path(os.path.abspath(os.path.dirname(__file__))))
    engine.atlas.add_font('luckiestguy', engine.atlas.get_item('root').path / 'LuckiestGuy.ttf')
    engine.atlas.add_texture('icon', engine.atlas.get_item('root').path / 'icon.png')
    engine.atlas.add_texture('card', engine.atlas.get_item('root').path / 'card.png')
    engine.set_icon(str(engine.atlas.get_item('icon').path))
    
    engine.add_scene('main', MainMenu)
    engine.set_scene('main')
    engine.run()


if __name__ == '__main__':
    main()