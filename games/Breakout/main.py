from lunaengine.core import LunaEngine, Scene
from lunaengine.ui import *
from lunaengine.backend import OpenGLRenderer
import sys, os, random, json, pygame, math

from datetime import datetime
from argparse import ArgumentParser
from pathlib import Path

argparser = ArgumentParser()
argparser.add_argument('--debug', action='store_true', default=False, help="Enable debug mode")
argparser.add_argument('--fullscreen', action='store_true', default=False, help="Run in fullscreen")

# ---------- Leaderboard Manager ----------
class LeaderboardManager:
    def __init__(self, file_name: str = 'leaderboard.json'):
        self.file_name = Path(os.path.abspath(os.path.dirname(__file__))) / file_name
        self.data: dict = {'scores': []}
        self.current_username: str = ''
        self.get_data()

    def get_data(self):
        if os.path.exists(self.file_name):
            with open(self.file_name, 'r') as f:
                self.data = json.load(f)
        else:
            with open(self.file_name, 'w') as f:
                json.dump(self.data, f)

    def save(self):
        with open(self.file_name, 'w') as f:
            json.dump(self.data, f)

    def add_score(self, score: int, start_time: datetime):
        self.data['scores'].append({
            'name': self.current_username,
            'score': score,
            'time_played': (datetime.now() - start_time).total_seconds(),
            'date': datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        self.data['scores'].sort(key=lambda x: x['score'], reverse=True)
        self.data['scores'] = self.data['scores'][:10]
        self.save()

LDM = LeaderboardManager()

# ---------- Paddle ----------
class Paddle:
    def __init__(self, x, y, width, height, speed=300):
        self.width = width
        self.height = height
        self.speed = speed          # current speed (will increase)
        self.rect = pygame.Rect(x, y, width, height)

    def move(self, dx: float, dt: float):
        self.rect.x += dx * self.speed * dt
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > 1024:
            self.rect.right = 1024

    def reset(self, x, y):
        self.rect.x = x
        self.rect.y = y

# ---------- Brick ----------
class Brick:
    def __init__(self, x, y, width, height, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color

# ---------- Ball ----------
class Ball:
    def __init__(self, x, y, radius, speed):
        self.radius = radius
        self.speed = speed          # current speed
        self.max_speed = 12         # soft cap
        self.rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)
        self.vx = speed * random.choice([-1, 1])
        self.vy = -speed
        self.launched = False

    def move(self):
        if self.launched:
            self.rect.x += self.vx
            self.rect.y += self.vy

    def bounce_wall(self):
        self.vy = -self.vy

    def bounce_paddle(self, paddle):
        # Relative hit position (-1..1)
        offset = (self.rect.centerx - paddle.rect.centerx) / (paddle.width / 2)
        offset = max(-1, min(1, offset))
        max_angle = 75
        angle = offset * math.radians(max_angle)

        # Increase speed slightly, cap it
        self.speed = min(self.speed * 1.02, self.max_speed)
        self.vx = self.speed * math.sin(angle)
        self.vy = -self.speed * math.cos(angle)

    def reset(self, x, y):
        self.rect.center = (x, y)
        self.vx = self.speed * random.choice([-1, 1])
        self.vy = -self.speed
        self.launched = False

# ---------- Main Menu ----------
class MainMenu(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.engine.add_function_to_live_inspector(
            'Create Random Leader', self.create_test_leader,
            [('user', str)], 'Create a random user for leaderboard')

        self.setup_ui()

    def create_test_leader(self, username: str):
        LDM.current_username = username
        LDM.add_score(random.randint(0, 10000), datetime.now())
        LDM.save()
        return False

    def play(self):
        if self.username_textbox.text == '':
            return
        LDM.current_username = self.username_textbox.text
        self.engine.set_scene("game")

    def setup_ui(self):
        self.add_ui_element(TextLabel(self.engine.width//2, 30*self.engine.ratio.y,
                                      'Breakout', 72, font_name='dotgothic', pivot=(0.5, 0)))

        play_button = Button(self.engine.width//2, 150*self.engine.ratio.y,
                             250*self.engine.ratio.x, 65*self.engine.ratio.y,
                             'Play', 50, font_name='dotgothic', pivot=(0.5, 0))
        play_button.set_on_click(self.play)
        self.add_ui_element(play_button)

        exit_button = Button(self.engine.width//2, 220*self.engine.ratio.y,
                             200*self.engine.ratio.x, 50*self.engine.ratio.y,
                             'Exit', 40, font_name='dotgothic', pivot=(0.5, 0))
        exit_button.set_on_click(lambda: setattr(self.engine, 'running', False))
        self.add_ui_element(exit_button)

        self.username_textbox = TextBox(self.engine.width//2, 290*self.engine.ratio.y,
                                        150*self.engine.ratio.x, 40*self.engine.ratio.y,
                                        '', 32, font_name='dotgothic', pivot=(0.5, 0))
        self.add_ui_element(self.username_textbox)

        leaderboard_frame = ScrollingFrame(self.engine.width//2, self.engine.height - 15*self.engine.ratio.y,
                                           600*self.engine.ratio.x, 400*self.engine.ratio.y,
                                           580*self.engine.ratio.x, 700*self.engine.ratio.y,
                                           pivot=(0.5, 1))
        self.add_ui_element(leaderboard_frame)

        self.leaderboard_table = Table(5*self.engine.ratio.x, 5*self.engine.ratio.y,
                                       570*self.engine.ratio.x, 700*self.engine.ratio.y,
                                       ['Name', 'Score', 'Time Played', 'Date'])
        leaderboard_frame.add_child(self.leaderboard_table)

    def on_enter(self, previous_scene: str | None = None) -> None:
        self.reload_table()

    def reload_table(self):
        self.leaderboard_table.clear()
        scores = LDM.data.get('scores', [])
        scores.sort(key=lambda x: x['score'], reverse=True)
        for score in scores:
            self.leaderboard_table.add_row([score['name'], str(score['score']),
                                            str(round(score['time_played'], 1)), score['date']])

    def render(self, renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))

# ---------- Game Scene (Infinite) ----------
class GameScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.paddle = None
        self.ball = None
        self.bricks = []
        self.lives = 3
        self.score = 0
        self.game_over = False
        self.start_time = None
        self.game_started = False

        # Difficulty scaling
        self.level = 1
        self.paddle_speed = 300
        self.max_paddle_speed = 600
        self.ball_speed = 5
        self.max_ball_speed = 12
        self.speed_timer = 0.0
        self.speed_increase_interval = 5.0  # seconds
        
        self.engine.add_function_to_live_inspector('Add Life', lambda: self.__setattr__('lives', 100), [], 'Set to 100 lives')
        self.engine.add_function_to_live_inspector('Suicide', lambda: self.__setattr__('lives', 0), [], 'Set to 0 lives')

        # UI elements
        self.score_label = TextLabel(self.engine.width//2, 30*self.engine.ratio.y,
                                     'Score: 0', 32, (200, 170, 100), pivot=(0.5, 0))
        self.add_ui_element(self.score_label)

        self.lives_label = TextLabel(30*self.engine.ratio.x, 30*self.engine.ratio.y,
                                     'Lives: 3', 32, (255, 255, 255), pivot=(0, 0))
        self.add_ui_element(self.lives_label)

        self.level_label = TextLabel(self.engine.width - 30*self.engine.ratio.x, 30*self.engine.ratio.y,
                                     'Level: 1', 28, (200, 200, 200), pivot=(1, 0))
        self.add_ui_element(self.level_label)

        self.start_label = TextLabel(self.engine.width//2, self.engine.height//2 - 50,
                                     'Press SPACE to launch', 36, (255, 255, 255),
                                     pivot=(0.5, 0.5), font_name='dotgothic')
        self.start_label.visible = False
        self.add_ui_element(self.start_label)

        self.message_label = TextLabel(self.engine.width//2, self.engine.height//2 - 100,
                                       '', 48, (255, 200, 100), pivot=(0.5, 0.5),
                                       font_name='dotgothic')
        self.message_label.visible = False
        self.add_ui_element(self.message_label)

        self.menu_btn = Button(self.engine.width//2, self.engine.height//2 + 80,
                               200*self.engine.ratio.x, 50*self.engine.ratio.y,
                               'Main Menu', 32, font_name='dotgothic', pivot=(0.5, 0.5))
        self.menu_btn.set_on_click(lambda: self.engine.set_scene('main'))
        self.menu_btn.visible = False
        self.add_ui_element(self.menu_btn)

        self.restart_btn = Button(self.engine.width//2, self.engine.height//2 + 20,
                                  200*self.engine.ratio.x, 50*self.engine.ratio.y,
                                  'Play Again', 32, font_name='dotgothic', pivot=(0.5, 0.5))
        self.restart_btn.set_on_click(self.restart)
        self.restart_btn.visible = False
        self.add_ui_element(self.restart_btn)

        @self.engine.on_event(pygame.KEYDOWN)
        def on_key_down(event):
            if event.key == pygame.K_SPACE and not self.game_started and not self.game_over:
                self.launch_ball()

    def on_enter(self, previous_scene: str | None = None) -> None:
        # Full reset
        self.lives = 3
        self.score = 0
        self.game_over = False
        self.game_started = False
        self.start_time = datetime.now()
        self.bricks.clear()
        self.level = 1
        self.paddle_speed = 300
        self.ball_speed = 5
        self.speed_timer = 0.0

        # Create paddle and ball
        pad_width = 100
        pad_height = 16
        pad_x = (self.engine.width - pad_width) // 2
        pad_y = self.engine.height - 60
        self.paddle = Paddle(pad_x, pad_y, pad_width, pad_height, self.paddle_speed)

        ball_radius = 10
        ball_x = self.engine.width // 2
        ball_y = pad_y - ball_radius
        self.ball = Ball(ball_x, ball_y, ball_radius, self.ball_speed)

        self.generate_bricks(lines=6, cols=12)

        self.update_score_display()
        self.update_lives_display()
        self.update_level_display()
        self.start_label.visible = True
        self.message_label.visible = False
        self.menu_btn.visible = False
        self.restart_btn.visible = False

    def generate_bricks(self, lines, cols):
        margin = 40
        spacing = 4
        top_offset = 80
        total_width = self.engine.width - 2 * margin
        brick_width = (total_width - (cols - 1) * spacing) // cols
        brick_height = 20

        # Slightly randomize base color for each level
        base_color = [random.randint(100, 255) for _ in range(3)]
        for row in range(lines):
            row_color = [max(0, c - row * (255 // lines)) for c in base_color]
            for col in range(cols):
                x = margin + col * (brick_width + spacing)
                y = top_offset + row * (brick_height + spacing)
                brick = Brick(x, y, brick_width, brick_height, row_color[:])
                self.bricks.append(brick)

    def launch_ball(self):
        if not self.ball.launched:
            self.ball.launched = True
            self.game_started = True
            self.start_label.visible = False
            self.ball.vx = self.ball.speed * random.choice([-1, 1])
            self.ball.vy = -self.ball.speed

    def update_score_display(self):
        self.score_label.set_text(f'Score: {self.score}')

    def update_lives_display(self):
        self.lives_label.set_text(f'Lives: {self.lives}')

    def update_level_display(self):
        self.level_label.set_text(f'Level: {self.level}')

    def lose_life(self):
        self.lives -= 1
        self.update_lives_display()
        if self.lives <= 0:
            self.game_over = True
            self.show_game_over()
        else:
            # Reset ball and paddle (but keep speeds)
            self.ball.reset(self.engine.width//2, self.paddle.rect.top - self.ball.radius)
            self.paddle.reset((self.engine.width - self.paddle.width)//2,
                              self.engine.height - 60)
            self.game_started = False
            self.start_label.visible = True
            self.ball.launched = False

    def show_game_over(self):
        self.message_label.set_text('GAME OVER')
        self.message_label.visible = True
        self.menu_btn.visible = True
        self.restart_btn.visible = True
        self.start_label.visible = False
        # Save score
        LDM.add_score(self.score, self.start_time)

    def restart(self):
        self.engine.set_scene('game')   # fresh start

    def update(self, dt: float):
        if self.game_over:
            return

        # Increase speeds over time
        self.speed_timer += dt
        if self.speed_timer >= self.speed_increase_interval:
            self.speed_timer = 0.0
            # Increase paddle speed
            if self.paddle_speed < self.max_paddle_speed:
                self.paddle_speed = min(self.paddle_speed + 20, self.max_paddle_speed)
                self.paddle.speed = self.paddle_speed
            # Increase ball speed
            if self.ball_speed < self.max_ball_speed:
                self.ball_speed = min(self.ball_speed + 0.5, self.max_ball_speed)
                self.ball.speed = self.ball_speed
                # Update current velocity magnitude proportionally
                current_speed = math.hypot(self.ball.vx, self.ball.vy)
                if current_speed > 0:
                    scale = self.ball_speed / current_speed
                    self.ball.vx *= scale
                    self.ball.vy *= scale

        # Paddle control
        keys = pygame.key.get_pressed()
        dx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -1
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = 1
        self.paddle.move(dx, dt)

        self.ball.move()

        # ---- Wall collisions ----
        if self.ball.rect.top <= 0:
            self.ball.bounce_wall()
            self.ball.rect.top = 0

        if self.ball.rect.left <= 0 or self.ball.rect.right >= self.engine.width:
            self.ball.vx = -self.ball.vx
            if self.ball.rect.left < 0:
                self.ball.rect.left = 0
            if self.ball.rect.right > self.engine.width:
                self.ball.rect.right = self.engine.width

        if self.ball.rect.bottom >= self.engine.height:
            self.lose_life()
            return

        # ---- Paddle collision ----
        if self.ball.rect.colliderect(self.paddle.rect):
            self.ball.bounce_paddle(self.paddle)
            self.ball.rect.bottom = self.paddle.rect.top

        # ---- Brick collisions ----
        for brick in self.bricks[:]:
            if self.ball.rect.colliderect(brick.rect):
                overlap_x = (self.ball.rect.right - brick.rect.left) if self.ball.vx > 0 else (brick.rect.right - self.ball.rect.left)
                overlap_y = (self.ball.rect.bottom - brick.rect.top) if self.ball.vy > 0 else (brick.rect.bottom - self.ball.rect.top)
                if overlap_x < overlap_y:
                    self.ball.vx = -self.ball.vx
                else:
                    self.ball.vy = -self.ball.vy
                self.bricks.remove(brick)
                self.score += 10
                self.update_score_display()
                break

        # ---- Infinite: if no bricks left, spawn new level ----
        if not self.bricks:
            self.level += 1
            self.update_level_display()
            # Increase difficulty: more rows, more columns, or just more bricks
            rows = min(6 + self.level // 2, 12)   # max 12 rows
            cols = min(12 + self.level // 3, 16)  # max 16 cols
            self.generate_bricks(rows, cols)
            # Reset ball position (keep speed)
            self.ball.reset(self.engine.width//2, self.paddle.rect.top - self.ball.radius)
            self.game_started = False
            self.start_label.visible = True
            self.ball.launched = False

    def render(self, renderer: OpenGLRenderer):
        renderer.fill_screen(ThemeManager.get_color('background'))

        for brick in self.bricks:
            renderer.draw_rect(brick.rect.x, brick.rect.y, brick.rect.width, brick.rect.height,
                               brick.color, corner_radius=2)

        renderer.draw_rect(self.paddle.rect.x, self.paddle.rect.y,
                           self.paddle.rect.width, self.paddle.rect.height,
                           (255, 255, 255))

        renderer.draw_circle(self.ball.rect.centerx, self.ball.rect.centery,
                             self.ball.radius, (255, 255, 255))

        super().render(renderer)

# ---------- Main ----------
def main():
    args = argparser.parse_args(sys.argv[1:])
    engine = LunaEngine('Breakout', 1024, 768, debug=args.debug, fullscreen=args.fullscreen)

    engine.update_ratio(1024, 768)
    engine.set_global_theme(ThemeType.GALAXY)

    engine.atlas.add_folder('root', Path(os.path.abspath(os.path.dirname(__file__))))
    engine.atlas.add_folder('assets', engine.atlas.get_item('root').path / 'assets')
    engine.atlas.add_font('dotgothic', engine.atlas.get_item('assets').path / 'DotGothic16.ttf')

    engine.set_icon(str(engine.atlas.get_item('assets').path / 'icon.png'))

    engine.add_scene('main', MainMenu)
    engine.add_scene('game', GameScene)
    engine.set_scene('main')

    engine.run()

if __name__ == '__main__':
    main()