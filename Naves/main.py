from lunaengine.core import LunaEngine, Scene, AudioSystem, AudioChannel
from lunaengine.graphics import SpriteSheet, Animation, Camera, CameraMode, ParticleType, PhysicsType, ExitPoint
from lunaengine.ui import *
import pygame, os, json, time, random
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--debug', action='store_true', help='Enable debug mode')
args = parser.parse_args()

engine = LunaEngine("Naves")

class Data:
    asteroids: list
    health_bar: list
    spaceship_explosion = None
    spaceship = None
    leaderboard: dict
    started:float
    background: pygame.SurfaceType
    current_username: str = ""
    bullet_sprite: pygame.SurfaceType = None
    size_fix:pygame.Vector2

data = Data()

class Bullet:
    def __init__(self, position):
        self.position = pygame.math.Vector2(position)
        self.speed = 750 * data.size_fix.x
        self.rect = pygame.Rect(position[0], position[1], 8, 4)
        
    def update(self, dt):
        self.position.x += self.speed * dt
        self.rect.x = self.position.x
        self.rect.y = self.position.y
        
    def render(self, renderer):
        renderer.blit(data.bullet_sprite, self.position)

class MainMenu(Scene):
    def on_enter(self, previous_scene = None):
        self.engine.set_global_theme(ThemeType.DEEP_SPACE.value)
        self.update_leaderboard()
        return super().on_enter(previous_scene)
        
    def  on_exit(self, next_scene = None):
        return super().on_exit(next_scene)
    
    def __init__(self, engine):
        super().__init__(engine)
        self.create_ui()
        
    def create_ui(self):
        self.add_ui_element(TextLabel(320*data.size_fix.x, 100*data.size_fix.y, "Naves", 102, (255, 255, 255),font_name=os.path.abspath("./assets/SpaceMono.ttf"), root_point=(0.5, 0)))
        
        self.play_button = Button(320*data.size_fix.x, 300*data.size_fix.y, 300*data.size_fix.x, 90*data.size_fix.y, "PLAY", 40, None, (0.5, 0.5))
        self.play_button.set_on_click(self.play_clicked)
        self.add_ui_element(self.play_button)
        
        self.exit_button = Button(320*data.size_fix.x, 400*data.size_fix.y, 285*data.size_fix.x, 75*data.size_fix.y, "EXIT", 36, None, (0.5, 0.5))
        self.exit_button.set_on_click(self.exit_clicked)
        self.add_ui_element(self.exit_button)
        
        self.add_ui_element(TextLabel(320*data.size_fix.x, 500*data.size_fix.y, "Coloque seu nome + turma aqui:", 24, (255, 255, 255),font_name=None, root_point=(0.5, 0)))
        self.username_textbox = TextBox(320*data.size_fix.x, 532*data.size_fix.y, 300*data.size_fix.x, 35*data.size_fix.y, "", 24, None, (0.5, 0))
        self.add_ui_element(self.username_textbox)
        self.add_ui_element(TextLabel(320*data.size_fix.x, 570*data.size_fix.y, "*Não utilize acentos, este será usado para a entrega da premiação.", 16, (190, 60, 90), None, root_point=(0.5, 0)))
        
        self.add_ui_element(TextLabel(int(640*data.size_fix.x), 15*data.size_fix.y, "LEADERBOARD", 30, (255, 255, 255),font_name=None, root_point=(0, 0)))
        self.leaderboard_scroll = ScrollingFrame(self.engine.width-int(20*data.size_fix.x), int(40*data.size_fix.y), int(360*data.size_fix.x), int(500*data.size_fix.x), int(360*data.size_fix.x), int(900*data.size_fix.y), (1.0, 0))
        
        self.add_ui_element(self.leaderboard_scroll)
        
    def update_leaderboard(self):
        self.leaderboard_scroll.children.clear()
        for index, user in enumerate(sorted(data.leaderboard['scores'], key=lambda x: x['score'], reverse=True)):
            self.leaderboard_scroll.add_child(TextLabel((25*data.size_fix.x), ((index * 50)+15) * data.size_fix.y, f"{index + 1} - {user['name']} - {user['score']}", 48, (255, 255, 255),font_name=None, root_point=(0, 0)))
        
    def play_clicked(self):
        if len(self.username_textbox.text) > 1:
            data.current_username = self.username_textbox.text
            self.engine.set_scene("Game")
    
    def exit_clicked(self):
        self.engine.shutdown()
        exit(0)
        
    def update(self, dt):
        return super().update(dt)
    
    def render(self, renderer):
        pass

class Player:
    max_health:int = 5
    _health:int = 5
    score:int = 0
    name:str
    state:str = 'moving'
    position:pygame.math.Vector2 = pygame.math.Vector2(0, 0)
    
    animations:dict = {
        'moving': None,
        'explosion': None
    }
    
    last_shoot = None
    shoot_cooldown:float = 0.75
    rect:pygame.rect.RectType
    explosion_start_time:float = 0
    invulnerable:bool = False
    invulnerable_start:float = 0
    invulnerable_duration:float = 1.0
    visible:bool = True
    flash_timer:float = 0
    
    @property
    def health(self):
        return self._health
    
    @health.setter
    def health(self, value):
        if value < self._health and not self.invulnerable and self.state != 'explosion':
            self._health = value
            self.invulnerable = True
            self.invulnerable_start = time.time()
        elif value >= self._health:
            self._health = value
    
    def __init__(self, name):
        self.name = name
        self.animations = {
            'moving': data.spaceship,
            'explosion': data.spaceship_explosion
        }
        self.position.xy = (120, 336)
        self.rect = self.animations[self.state].frames[0].get_bounding_rect()
        self.rect.center = self.position.xy
        
    
    def update(self, dt):
        if self.state == 'explosion' and time.time() - self.explosion_start_time > 1.5:
            return
        
        self.rect.center = self.position.xy
        
        if self.invulnerable:
            current_time = time.time()
            if current_time - self.invulnerable_start >= self.invulnerable_duration:
                self.invulnerable = False
                self.visible = True
            else:
                self.flash_timer += dt
                if self.flash_timer >= 0.1:
                    self.visible = not self.visible
                    self.flash_timer = 0
        
    def render(self, renderer:'Renderer'):
        if not self.visible and self.invulnerable:
            return
            
        current_frame = self.animations[self.state].get_current_frame()
        frame_rect = current_frame.get_bounding_rect()
        render_position = (self.rect.centerx - frame_rect.width/2, self.rect.top + 5 - frame_rect.height/2)
        renderer.blit(current_frame, render_position)
    
    def explode(self):
        self.state = 'explosion'
        self.explosion_start_time = time.time()
        self.animations['explosion'].reset()
        
    def get_bullet_spawn_position(self) -> tuple:
        return (self.rect.right, self.rect.centery)

class Game(Scene):
    def on_exit(self, next_scene = None):
        # Resets all things
        self.player = None
        self.score_label = None
        self.clear_ui_elements()
        
        self.max_asteroids = 5
        self.asteroids.clear()
        self.bullets.clear()
        self.last_score = None
        self.game_over = False
        self.asteroid_speed = 0.9
        return super().on_exit(next_scene)
    
    def on_enter(self, previous_scene = None):
        self.player = Player(data.current_username)
        
        @self.engine.on_event(pygame.KEYDOWN)
        def on_keydown(event):
            if event.key == pygame.K_k:
                self.player.health -= 1
        
        self.score_label = TextLabel(self.engine.width-10, 15, f"Pontuação: {int(self.player.score)}", 24, (255, 255, 255),font_name=os.path.join("assets", "SpaceMono.ttf"), root_point=(1, 0))
        self.add_ui_element(self.score_label)
        
        self.audio_system.play_music("bgm", 0.7, 1.0, True)
        self.camera.set_target(self.player.rect, CameraMode.FIXED)
        
        self.create_all_asteroids()
        
        self.last_score = time.time()
        
        self.parallax_x = 0
        self.parallax_sample = self.create_parallax_layer(0.94)
        
        return super().on_enter(previous_scene)
    
    player:Player
    max_asteroids:int = 5
    asteroids:list = []
    asteroid_speed:float = 0.9
    game_over:bool = False
    bullets:list = []
    
    last_score:float
    def __init__(self, engine):
        super().__init__(engine)
        
        self.audio_system = AudioSystem()
        self.audio_system.load_sound_effect("explosion", "./assets/explosion.wav")
        self.audio_system.load_sound_effect("shoot", "./assets/laserShoot.wav")
        self.audio_system.load_music("bgm", "./assets/music.mp3")
        
        self.parallax_x = 0
        self.parallax_sample = self.create_parallax_layer(0.94)
        self.setup_camera()
    
    def setup_camera(self):
        self.camera.position = (0, 0)
        self.camera.mode = CameraMode.FIXED
        
    def render_parallax(self, renderer:'Renderer'):
        for i in range(2):
            par_wid = self.parallax_sample.get_width()
            renderer.blit(self.parallax_sample, (i * par_wid + self.parallax_x, 0))
        
    def create_parallax_layer(self, brightness_factor=1.0):
        layer = data.background.copy()
        
        if brightness_factor != 1.0:
            overlay = pygame.Surface(layer.get_size(), pygame.SRCALPHA)
            brightness_value = int(255 *brightness_factor)
            overlay.fill((brightness_value, brightness_value, brightness_value, 100))
            layer.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        return layer
    
    def input_handler(self, dt):
        if self.game_over:
            return
            
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.player.position.y -= (400 * data.size_fix.y) * dt
            if self.player.position.y < 72:
                self.player.position.y = 72
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.player.position.y += (400 * data.size_fix.y) * dt
            if self.player.position.y > self.engine.height*0.8:
                self.player.position.y = self.engine.height*0.8
            
        if (keys[pygame.K_SPACE] or self.engine.input_state.mouse_buttons_pressed.left) and time.time() - self.player.last_shoot > self.player.shoot_cooldown:
            self.player.last_shoot = time.time()
            self.bullets.append(Bullet(self.player.get_bullet_spawn_position()))
            self.audio_system.play_sound("shoot", 1.0, 1.0, False)
            
    def create_asteroid(self):
        sprite:pygame.Surface = random.choice(data.asteroids)
        sprite_size = sprite.get_size()
        scale_factor = random.uniform(2, 3) * (self.engine.width / 1024)
        sprite = pygame.transform.scale(sprite, (int(sprite_size[0] * scale_factor), int(sprite_size[1] * scale_factor)))
        
        bounding_rect = sprite.get_bounding_rect()
        y = random.randint(80, self.engine.height - (80 + bounding_rect.height))
        
        asteroid_rect = pygame.Rect(self.engine.width+ 20 + bounding_rect.x, y + bounding_rect.y, bounding_rect.width, bounding_rect.height)
        self.asteroids.append((asteroid_rect, sprite))
        
    def create_all_asteroids(self):
        for i in range(self.max_asteroids):
            self.create_asteroid()
    
    def update_bullets(self, dt):
        for bullet in self.bullets[:]:
            bullet.update(dt)
            
            if bullet.position.x > self.engine.width:
                self.bullets.remove(bullet)
                continue
                
            for asteroid_rect, asteroid_sprite in self.asteroids:
                if bullet.rect.colliderect(asteroid_rect):
                    self.asteroids.remove((asteroid_rect, asteroid_sprite))
                    self.bullets.remove(bullet)
                    self.create_asteroid()
                    self.change_score(50)
                    self.audio_system.play_sound("explosion", 1.0, 1.0, False)
                    break
    
    def update_asteroids(self, dt):
        if self.game_over:
            return
            
        for asteroid_rect, asteroid_sprite in self.asteroids[:]:
            asteroid_rect.x -= ((293 * self.asteroid_speed) * data.size_fix.x) * dt
            
            if asteroid_rect.colliderect(self.player.rect) and not self.player.invulnerable and self.player.state != 'explosion':
                self.player.health -= 1
                self.audio_system.play_sound("explosion", 1.0, 1.0, False)
                self.asteroids.remove((asteroid_rect, asteroid_sprite))
                self.create_asteroid()
                
                if self.player.health <= 0 and not self.game_over:
                    self.game_over = True
                    self.player.explode()
                    self.audio_system.stop_music()
                    self.audio_system.play_sound("explosion", 1.0, 1.0, False)
                break
                
            if asteroid_rect.right < 0:
                self.asteroids.remove((asteroid_rect, asteroid_sprite))
                self.create_asteroid()
                
            if len(self.asteroids) < self.max_asteroids:
                self.create_asteroid()
                
    def render_asteroids(self, renderer):
        for asteroid_rect, sprite in self.asteroids:
            bounding_rect = sprite.get_bounding_rect()
            render_position = (asteroid_rect.x - bounding_rect.x, asteroid_rect.y - bounding_rect.y)
            renderer.blit(sprite, render_position)
            
    def render_bullets(self, renderer):
        for bullet in self.bullets:
            bullet.render(renderer)
            
    def render_aim_line(self, renderer):
        start_pos = (self.player.rect.centerx, self.player.rect.centery)
        
        for i in range(10):
            segment_length = 20 * data.size_fix.x
            gap_length = 10 * data.size_fix.x
            segment_start = start_pos[0] + i * (segment_length + gap_length)
            segment_end = segment_start + segment_length
            
            if segment_start < self.engine.width:
                renderer.draw_line(segment_start, start_pos[1], min(segment_end, self.engine.width), start_pos[1], (0, 190, 255, 100), 2)
    
    def render_debug(self, renderer):
        # Player hitbox
        renderer.draw_rect(self.player.rect.x, self.player.rect.y, self.player.rect.width, self.player.rect.height, (0, 255, 0, 100))
        
        # Bullet hitboxes
        for bullet in self.bullets:
            renderer.draw_rect(bullet.rect.x, bullet.rect.y, bullet.rect.width, bullet.rect.height, (255, 255, 0, 100))
        
        # Asteroid hitboxes
        for asteroid_rect, sprite in self.asteroids:
            renderer.draw_rect(asteroid_rect.x, asteroid_rect.y, asteroid_rect.width, asteroid_rect.height, (255, 0, 0, 100))
    
    def update(self, dt):
        if self.player.last_shoot == None: 
            self.player.last_shoot = time.time()
            
        self.input_handler(dt)
        self.player.update(dt)
        self.update_bullets(dt)
        self.update_asteroids(dt)
        
        if not self.game_over:
            parx, pary = self.camera.screen_to_world((self.player.rect.left+10, self.player.rect.centery))
            self.particle_system.emit(
                x=parx, 
                y=pary,
                particle_type=ParticleType.PLASMA,
                count=int(200 * dt),
                exit_point=ExitPoint.LEFT,
                physics_type=PhysicsType.SPACESHOOTER,
                spread=30.0
            )
        
        self.parallax_x -= (202 * self.asteroid_speed) * data.size_fix.x * dt
        if abs(self.parallax_x) > self.parallax_sample.get_width():
            self.parallax_x = 0
        
        if time.time() - self.last_score > 1 and not self.game_over:
            self.change_score(10)
            self.last_score = time.time()
            
        if self.game_over and self.player.state == 'explosion' and time.time() - self.player.explosion_start_time > 1.5:
            self.save_score()
            self.engine.set_scene("GameOver")
                
        super().update(dt)
        
    def change_score(self, value:int):
        if self.player.health > 0:
            self.player.score += value
            
            self.asteroid_speed = 0.9 + (self.player.score / 1000)
            self.max_asteroids = 5 + int(self.player.score / 2000)
            
            self.score_label.set_text(f"Pontuação: {int(self.player.score)}")
            
    def save_score(self):
        data.leaderboard['scores'].append({
            'name': data.current_username,
            'score': int(self.player.score)
        })
        
        with open("./leaderboard.json", "w") as f:
            json.dump(data.leaderboard, f)
            
    def render(self, renderer):
        renderer.fill_screen((30,  15, 50))
        self.render_parallax(renderer)
        
        self.render_asteroids(renderer)
        self.render_bullets(renderer)
        self.render_aim_line(renderer)
        
        self.player.render(renderer)
        
        renderer.blit(pygame.transform.scale(data.health_bar[int(self.player.health) if self.player.health > 0 else 0], (192*data.size_fix.x, 48*data.size_fix.y)), (10*data.size_fix.x, 10*data.size_fix.y))
        
        if args.debug:
            self.render_debug(renderer)
        
        if self.game_over:
            overlay = pygame.Surface((self.engine.width, self.engine.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            renderer.blit(overlay, (0, 0))
            
            font = pygame.font.Font(None, 74)
            text = font.render("GAME OVER", True, (255, 50, 50))
            text_rect = text.get_rect(center=(self.engine.width/2, self.engine.height/2 - (50*data.size_fix.y)))
            renderer.blit(text, text_rect)
            
            font = pygame.font.Font(None, 36)
            score_text = font.render(f"Final Score: {int(self.player.score)}", True, (255, 255, 255))
            score_rect = score_text.get_rect(center=(self.engine.width/2, self.engine.height/2 + (20*data.size_fix.y)))
            renderer.blit(score_text, score_rect)

class GameOver(Scene):
    def on_enter(self, previous_scene = None):
        self.engine.set_global_theme(ThemeType.DEEP_SPACE.value)
        self.create_ui()
        return super().on_enter(previous_scene)
        
    def create_ui(self):
        self.add_ui_element(TextLabel(320*data.size_fix.x, 100*data.size_fix.y, "GAME OVER", 74, (255, 50, 50), font_name=None, root_point=(0.5, 0)))
        
        self.menu_button = Button(320*data.size_fix.x, 300*data.size_fix.y, 300*data.size_fix.x, 90*data.size_fix.y, "MAIN MENU", 40, None, (0.5, 0.5))
        self.menu_button.set_on_click(self.menu_clicked)
        self.add_ui_element(self.menu_button)
        
        self.leaderboard_scroll = ScrollingFrame(self.engine.width-int(40*data.size_fix.x), int(40*data.size_fix.y), int(360*data.size_fix.x), int(640*data.size_fix.y), int(360*data.size_fix.x), int(900*data.size_fix.y), (1, 0))
        self.update_leaderboard()
        self.add_ui_element(self.leaderboard_scroll)
        
    def update_leaderboard(self):
        self.leaderboard_scroll.children.clear()
        for index, user in enumerate(sorted(data.leaderboard['scores'], key=lambda x: x['score'], reverse=True)):
            self.leaderboard_scroll.add_child(TextLabel(25*data.size_fix.x, ((index * 50)+15)*data.size_fix.y, f"{index + 1} - {user['name']} - {user['score']}", 48, (255, 255, 255), font_name=None, root_point=(0, 0)))
        
    def menu_clicked(self):
        self.engine.set_scene("MainMenu")
        
    def update(self, dt):
        return super().update(dt)
    
    def render(self, renderer):
        pass

def main():
    data.started = time.time()
    engine = LunaEngine("Naves", width = 1920, height = 1080)
    engine.initialize()
    
    data.size_fix = pygame.Vector2(engine.width/1024, engine.height/768)

    data.asteroids = SpriteSheet("./assets/Asteroids.png").get_sprites_at_regions([
        (0, 0, 32, 32), (32, 0, 32, 32), (64, 0, 32, 32), (96, 0, 32, 32), (128, 0, 32 ,32),
        (0, 32, 32, 32), (32, 32, 32, 32), (64, 32, 32, 32), (96, 32, 32, 32), (128, 32, 32, 32),
        (0, 64, 32, 32), (32, 64, 32, 32), (64, 64, 32, 32), (96, 64, 32, 32), (128, 64, 32, 32),])
    data.health_bar = SpriteSheet("./assets/Health-bar.png").get_sprites_at_regions([pygame.Rect(640, 0, 128, 32), pygame.Rect(512, 0, 128, 32), pygame.Rect(384, 0, 128, 32), pygame.Rect(256, 0, 128, 32), pygame.Rect(128, 0, 128, 32), pygame.Rect(0, 0, 128, 32)])
    data.spaceship = Animation(spritesheet_file='./assets/Spaceship.png', size=(32, 32), start_pos=(0, 0), frame_count=5, scale=(2.5 * data.size_fix.x, 2.5 * data.size_fix.x), duration=0.75, loop=True)
    data.spaceship_explosion = Animation(spritesheet_file='./assets/Spaceship-explosion.png', size=(32, 32), start_pos=(0, 0), frame_count=12, scale=(2.5 * data.size_fix.x, 2.5 * data.size_fix.x), duration=0.7, loop=False)
    data.background = pygame.transform.scale(pygame.image.load(os.path.abspath("./assets/background.jpg")).convert_alpha(), (engine.width, engine.height))
    
    bullet_surface = pygame.Surface((8, 4), pygame.SRCALPHA)
    pygame.draw.ellipse(bullet_surface, (255, 255, 0), (0, 0, 8, 4))
    data.bullet_sprite = bullet_surface
    
    if not os.path.exists("./leaderboard.json"):
        with open("./leaderboard.json", "w") as f:
            f.write('{"scores": []}')
            f.close()
            
    data.leaderboard = json.load(open("./leaderboard.json"))
    
    engine.add_scene("MainMenu", MainMenu)
    engine.add_scene("Game", Game)
    engine.add_scene("GameOver", GameOver)
    
    engine.set_scene("MainMenu")

    engine.run()
        
if __name__ == "__main__":
    main()