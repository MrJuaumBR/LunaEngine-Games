from lunaengine.core import LunaEngine, Scene, Renderer, AudioSystem
from lunaengine.ui import *
from lunaengine.graphics import SpriteSheet, Animation, Camera, CameraMode, ParticleConfig, ParticleType
import pygame, os, random, time, json, sys

path_assets = os.path.abspath('./assets/')
path_font_ninja = os.path.join(path_assets, 'ninja_font.ttf')

DEBUG_MODE = '--debug' in sys.argv

class Data:
    player_name: str
    leaderboard: dict
    player_animations: dict
    assets: dict
    ratio: pygame.Vector2
    total_time: float = 0
    current_level: int = 1
    levels_completed: list = []
    maps: dict = {}
    
    def __init__(self):
        if not os.path.exists('./leaderboard.json'):
            self.leaderboard = {
                "scores": []
            }
            with open('./leaderboard.json', 'w') as f:
                json.dump(self.leaderboard, f)
                f.close()
        else:
            with open('./leaderboard.json', 'r') as f:
                self.leaderboard = json.load(f)
                f.close()
        
        self.load_maps()
                
    def load_maps(self):
        maps_path = os.path.join(path_assets, 'maps.json')
        if os.path.exists(maps_path):
            with open(maps_path, 'r') as f:
                self.maps = json.load(f)
                f.close()
                
    def add_score(self, player_name, time_score):
        self.leaderboard["scores"].append({
            "name": player_name,
            "time": time_score,
            "date": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        self.leaderboard["scores"].sort(key=lambda x: x["time"])
        self.leaderboard["scores"] = self.leaderboard["scores"][:10]
        
        with open('./leaderboard.json', 'w') as f:
            json.dump(self.leaderboard, f)
            f.close()
            
    def get_score_index(self, player_name):
        for i in range(len(self.leaderboard["scores"])):
            if self.leaderboard["scores"][i]["name"] == player_name:
                return i
                
    def register_custom_particles(self, scene: Scene):
        if not scene.particle_system.get_custom_particle('ninja_smoke'):
            scene.particle_system.register_custom_particle(
                'ninja_smoke', ParticleConfig(
                    color_start=(80, 80, 80),
                    color_end=(40, 40, 40),
                    size_start=4.0,
                    size_end=1.0,
                    lifetime=0.5
                )
            )
                
    def load_assets(self):
        self.assets = {}
        
        tile_ss = SpriteSheet(os.path.join(path_assets, 'tiles.png'))
        
        self.assets['tiles'] = {
            'forest': {
                'type0': tile_ss.get_sprite_at_rect(pygame.Rect(0, 0, 32, 32)),
                'type1': tile_ss.get_sprite_at_rect(pygame.Rect(32, 0, 32, 32)),
                'transition_0_1': tile_ss.get_sprite_at_rect(pygame.Rect(64, 0, 32, 32)),
                'transition_1_0': tile_ss.get_sprite_at_rect(pygame.Rect(96, 0, 32, 32))
            },
            'city': {
                'type0': tile_ss.get_sprite_at_rect(pygame.Rect(0, 32, 32, 32)),
                'type1': tile_ss.get_sprite_at_rect(pygame.Rect(32, 32, 32, 32)),
                'transition_0_1': tile_ss.get_sprite_at_rect(pygame.Rect(64, 32, 32, 32)),
                'transition_1_0': tile_ss.get_sprite_at_rect(pygame.Rect(96, 32, 32, 32))
            },
            'house': {
                'type0': tile_ss.get_sprite_at_rect(pygame.Rect(0, 64, 32, 32)),
                'type1': tile_ss.get_sprite_at_rect(pygame.Rect(32, 64, 32, 32)),
                'transition_0_1': tile_ss.get_sprite_at_rect(pygame.Rect(64, 64, 32, 32)),
                'transition_1_0': tile_ss.get_sprite_at_rect(pygame.Rect(96, 64, 32, 32))
            }
        }
        
        self.assets['backgrounds'] = {}
        for i in range(1, 6):
            bg_path = os.path.join(path_assets, f'level{i}.png')
            if os.path.exists(bg_path):
                bg_image = pygame.image.load(bg_path)
                self.assets['backgrounds'][f'level{i}'] = pygame.transform.scale(bg_image, (1280 * data.ratio.x, 720 * data.ratio.y))
        
        enemy_ss = os.path.join(path_assets, 'enemies.png')
        self.assets['enemies'] = {
            'guard': {
                'idle': Animation(enemy_ss, (32, 32), (0, 0), 4, scale=(2*data.ratio.x, 2*data.ratio.y), duration=1.0, loop=True),
                'walk': Animation(enemy_ss, (32, 32), (0, 32), 4, scale=(2*data.ratio.x, 2*data.ratio.y), duration=0.6, loop=True)
            },
            'archer': {
                'idle': Animation(enemy_ss, (32, 32), (0, 64), 4, scale=(2*data.ratio.x, 2*data.ratio.y), duration=1.0, loop=True),
                'walk': Animation(enemy_ss, (32, 32), (0, 96), 4, scale=(2*data.ratio.x, 2*data.ratio.y), duration=0.6, loop=True)
            }
        }
        
    def load_player_animations(self):
        f = os.path.join(path_assets, 'player.png')
        player_ss = os.path.join(path_assets, 'player.png')
        self.player_animations = {
            'idle': Animation(player_ss, (32, 32), (0,0), 22, scale=(2*data.ratio.x, 2*data.ratio.y), duration=2.0, loop=True),
            'run': Animation(player_ss, (32, 32), (0,32), 11, scale=(2*data.ratio.x, 2*data.ratio.y), duration=0.7, loop=True),
            'jump': Animation(player_ss, (32, 32), (0,64), 10, scale=(2*data.ratio.x, 2*data.ratio.y), duration=1, loop=True),
            'attack_0': Animation(player_ss, (32, 32), (0,96), 18, scale=(2*data.ratio.x, 2*data.ratio.y), duration=0.65, loop=True),
            'attack_1': Animation(player_ss, (32, 32), (0,128), 23, scale=(2*data.ratio.x, 2*data.ratio.y), duration=0.65, loop=True),
        }
        
data = Data()

class Projectile:
    def __init__(self, x, y, direction):
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(direction * 300, 0)
        self.rect = pygame.Rect(x, y, 16, 8)
        self.active = True
        
    def update(self, dt):
        self.position.x += self.velocity.x * dt
        self.position.y += self.velocity.y * dt
        self.rect.x = self.position.x
        self.rect.y = self.position.y
        
        if self.position.x < -100 or self.position.x > 2100:
            self.active = False
    
    def render(self, renderer: Renderer, camera: Camera):
        if self.active:
            screen_pos = camera.world_to_screen(self.position)
            renderer.draw_rect(screen_pos.x, screen_pos.y, 16, 8, (255, 255, 0))

class GameOverScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.final_time = 0
        
    def on_enter(self, previous_scene=None):
        self.engine.set_global_theme(ThemeType.DEEP_SPACE)
        self.clear_ui_elements()
        self.setup_ui()
        return super().on_enter(previous_scene)
    
    def setup_ui(self):
        self.add_ui_element(TextLabel(self.engine.width//2, 100*data.ratio.y, 'Missão Falhou!', 72, (200, 100, 100), path_font_ninja, root_point=(0.5, 0)))
        
        time_str = f"{int(data.total_time//60)}:{int(data.total_time%60):02d}"
        self.time_label = TextLabel(self.engine.width//2, 200*data.ratio.y, f'Tempo: {time_str}', 48, (200, 170, 100), path_font_ninja, root_point=(0.5, 0))
        self.add_ui_element(self.time_label)
        
        self.menu_button = Button(self.engine.width//2, 350*data.ratio.y, 250*data.ratio.x, 65*data.ratio.y, 'Voltar ao Menu', 48, path_font_ninja, root_point=(0.5, 0))
        self.menu_button.set_on_click(self.back_to_menu)
        self.add_ui_element(self.menu_button)
        
    def back_to_menu(self):
        data.total_time = 0
        data.current_level = 1
        data.levels_completed = []
        self.engine.set_scene("main")
        
    def update(self, dt):
        pass
        
    def render(self, renderer):
        renderer.draw_rect(0, 0, self.engine.width, self.engine.height, ThemeManager.get_color('background'))

class VictoryScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.final_time = 0
        
    def on_enter(self, previous_scene=None):
        self.engine.set_global_theme(ThemeType.BUILDER)
        self.clear_ui_elements()
        self.setup_ui()
        
        data.add_score(data.player_name, data.total_time)
        return super().on_enter(previous_scene)
    
    def setup_ui(self):
        self.add_ui_element(TextLabel(self.engine.width//2, 100*data.ratio.y, 'Missão Concluída!', 72, (100, 200, 100), path_font_ninja, root_point=(0.5, 0)))
        
        time_str = f"{int(data.total_time//60)}:{int(data.total_time%60):02d}"
        self.time_label = TextLabel(self.engine.width//2, 200*data.ratio.y, f'Tempo Total: {time_str}', 48, (200, 170, 100), path_font_ninja, root_point=(0.5, 0))
        self.add_ui_element(self.time_label)
        
        player_position = data.get_score_index(data.player_name) + 1
        self.position_label = TextLabel(self.engine.width//2, 260*data.ratio.y, f'Posição no Ranking: #{player_position}', 36, (200, 170, 100), path_font_ninja, root_point=(0.5, 0))
        self.add_ui_element(self.position_label)
        
        self.menu_button = Button(self.engine.width//2, 350*data.ratio.y, 250*data.ratio.x, 65*data.ratio.y, 'Voltar ao Menu', 48, path_font_ninja, root_point=(0.5, 0))
        self.menu_button.set_on_click(self.back_to_menu)
        self.add_ui_element(self.menu_button)
        
    def back_to_menu(self):
        data.total_time = 0
        data.current_level = 1
        data.levels_completed = []
        self.engine.set_scene("main")
        
    def update(self, dt):
        pass
        
    def render(self, renderer):
        renderer.draw_rect(0, 0, self.engine.width, self.engine.height, ThemeManager.get_color('background'))

class MainMenu(Scene):
    def on_enter(self, previous_scene=None):
        self.engine.set_global_theme(ThemeType.DEEP_SPACE)
        self.engine._update_all_ui_themes(ThemeType.DEEP_SPACE)
        self.update_leaderboard()
        return super().on_enter(previous_scene)
    
    def __init__(self, engine):
        super().__init__(engine)
        self.setup_ui()
        
    def setup_ui(self):
        self.add_ui_element(TextLabel(self.engine.width//2, 30*data.ratio.y, 'Scarf of Night', 108, (200, 50, 50), path_font_ninja, root_point=(0.5, 0)))
        
        self.play_button = Button(self.engine.width//2, 150*data.ratio.y, 360*data.ratio.x, 58*data.ratio.y, 'Iniciar Missão', 52, path_font_ninja, root_point=(0.5, 0))
        self.play_button.set_on_click(self.play)
        self.add_ui_element(self.play_button)
        
        self.exit_button = Button(self.engine.width//2, 220*data.ratio.y, 160*data.ratio.x, 52*data.ratio.y, 'Sair', 50, path_font_ninja, root_point=(0.5, 0))
        self.exit_button.set_on_click(self.quit)
        self.add_ui_element(self.exit_button)
        
        self.add_ui_element(TextLabel(self.engine.width//2, 275*data.ratio.y, 'Nome e Turma:', 26, (200, 170, 100), path_font_ninja, root_point=(0.5, 0)))
        self.name_textbox = TextBox(self.engine.width//2, 315*data.ratio.y, 200*data.ratio.x, 30*data.ratio.y, '', 24, path_font_ninja, root_point=(0.5, 0))
        self.add_ui_element(self.name_textbox)
        
        self.leaderboard_label = TextLabel(self.engine.width//2, 370*data.ratio.y, 'Leaderboard', 42, (200, 170, 100), path_font_ninja, root_point=(0.5, 0))
        self.add_ui_element(self.leaderboard_label)
        
        self.leaderboard_frame = ScrollingFrame(self.engine.width//2, int(430*data.ratio.y), int(400*data.ratio.x), int(200*data.ratio.y), 380*data.ratio.x, 400*data.ratio.y, root_point=(0.5, 0))
        self.add_ui_element(self.leaderboard_frame)
        
    def update_leaderboard(self):
        self.leaderboard_frame.children.clear()
        
        if not data.leaderboard["scores"]:
            no_scores = TextLabel(190*data.ratio.x, 20*data.ratio.y, 'Nenhuma pontuação ainda!', 24, (150, 150, 150), path_font_ninja, root_point=(0.5, 0))
            self.leaderboard_frame.add_child(no_scores)
            return
            
        for i, score_data in enumerate(data.leaderboard["scores"]):
            y_pos = 20 + (i * 35)
            time_str = f"{int(score_data['time']//60)}:{int(score_data['time']%60):02d}"
            rank_text = f"#{i+1} {score_data['name']} - {time_str}"
            score_label = TextLabel(10*data.ratio.x, y_pos*data.ratio.y, rank_text, 20, (200, 170, 100), path_font_ninja, root_point=(0, 0))
            self.leaderboard_frame.add_child(score_label)
        
    def update(self, dt):
        pass
        
    def play(self):
        if self.name_textbox.text == '': return
        data.player_name = self.name_textbox.text
        self.engine.set_scene("game")
        
    def quit(self):
        self.engine.shutdown()
        exit()
        
    def render(self, renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))

class Player:
    def __init__(self):
        self.animations = data.player_animations
        self.current_state = 'idle'
        self.facing_right = True
        self.attack_index = 0
        
        self.position = pygame.Vector2(100, 400)
        self.velocity = pygame.Vector2(0, 0)
        self.speed = 300
        self.jump_force = -500
        self.gravity = 1200
        self.on_ground = False
        
        # Pegar o tamanho do primeiro frame da animação idle
        idle_frame = self.animations['idle'].get_current_frame()
        frame_width, frame_height = idle_frame.get_size()
        
        # Criar rect com o tamanho real da sprite
        self.rect = pygame.Rect(self.position.x, self.position.y, frame_width, frame_height)
        
        # Criar hitbox menor para colisões
        hitbox_width = frame_width * 0.6   # 60% da largura
        hitbox_height = frame_height * 0.8  # 80% da altura
        
        self.hitbox = pygame.Rect(0, 0, hitbox_width, hitbox_height)
        self.hitbox.center = self.rect.center
        
        self.attack_cooldown = time.time()
        self.health = 3
        
    def update(self, dt, platforms, engine: LunaEngine):
        self.animations[f'attack_{self.attack_index}' if self.current_state == 'attack' else self.current_state].update()
        
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_a]:
            self.velocity.x = -self.speed
            self.facing_right = False
            if self.on_ground and self.current_state != 'attack':
                self.current_state = 'run'
        elif keys[pygame.K_d]:
            self.velocity.x = self.speed
            self.facing_right = True
            if self.on_ground and self.current_state != 'attack':
                self.current_state = 'run'
        else:
            self.velocity.x = 0
            if self.on_ground and self.current_state != 'attack' and self.current_state != 'jump':
                self.current_state = 'idle'
        
        if keys[pygame.K_SPACE] and self.on_ground and self.current_state != 'attack':
            self.velocity.y = self.jump_force
            self.current_state = 'jump'
            self.on_ground = False
            
        if (keys[pygame.K_f] or engine.input_state.mouse_buttons_pressed.left) and (time.time() - self.attack_cooldown >= self.animations[f'attack_{self.attack_index}'].duration*1.02) and self.current_state != 'attack':
            self.current_state = 'attack'
            self.attack_index = (self.attack_index + 1) % 2
            self.attack_cooldown = time.time()

        if self.current_state == 'attack' and self.attack_cooldown + self.animations[f'attack_{self.attack_index}'].duration * 1.02 <= time.time():
            self.current_state = 'idle'
            self.animations[f'attack_{self.attack_index}'].current_frame_index = 0
        
        self.velocity.y += self.gravity * dt
        
        # Atualizar posição do rect principal
        current_frame = self.animations[f'attack_{self.attack_index}' if self.current_state == 'attack' else self.current_state].get_current_frame()
        frame_width, frame_height = current_frame.get_size()
    
        old_center = self.rect.center
        self.rect.width = frame_width
        self.rect.height = frame_height
        self.rect.center = old_center
        
        # Atualizar hitbox para seguir o centro do player
        self.hitbox.centerx = self.rect.centerx
        self.hitbox.centery = self.rect.centery
        
        # Movimento Y primeiro
        new_y = self.position.y + self.velocity.y * dt
        test_rect_y = self.hitbox.copy()
        test_rect_y.y = new_y
        
        self.on_ground = False
        
        # Colisão Y
        for platform in platforms:
            if test_rect_y.colliderect(platform):
                if self.velocity.y > 0:  # Caindo
                    new_y = platform.top - self.hitbox.height
                    self.velocity.y = 0
                    self.on_ground = True
                    if self.current_state == 'jump' and self.current_state != 'attack':
                        self.current_state = 'idle'
                elif self.velocity.y < 0:  # Pulando
                    new_y = platform.bottom
                    self.velocity.y = 0
        
        self.position.y = new_y
        self.hitbox.y = self.position.y
        self.rect.centery = self.hitbox.centery
        
        # Movimento X
        new_x = self.position.x + self.velocity.x * dt
        test_rect_x = self.hitbox.copy()
        test_rect_x.x = new_x
        
        # Colisão X
        collision_occurred = False
        for platform in platforms:
            if test_rect_x.colliderect(platform):
                if self.velocity.x > 0:  # Movendo para direita
                    new_x = platform.left - self.hitbox.width
                    collision_occurred = True
                    self.velocity.x = 0
                elif self.velocity.x < 0:  # Movendo para esquerda
                    new_x = platform.right
                    collision_occurred = True
                    self.velocity.x = 0
        
        if not collision_occurred:
            self.position.x = new_x
            self.hitbox.x = self.position.x
        else:
            self.hitbox.x = self.position.x
            
        # Atualizar rect principal para seguir a hitbox
        self.rect.centerx = self.hitbox.centerx
        self.rect.centery = self.hitbox.centery
        
        if self.position.y > 2500:
            self.health = 0
    
    def render(self, renderer: Renderer, camera: Camera):
        frame = self.animations[f'attack_{self.attack_index}' if self.current_state == 'attack' else self.current_state].get_current_frame()
        if not self.facing_right:
            frame = pygame.transform.flip(frame, True, False)
        
        screen_pos = camera.world_to_screen((self.hitbox.centerx, self.hitbox.centery))
        
        # CORREÇÃO: Use o rect normal sem offsets
        new_rect = pygame.Rect(0,0, self.rect.width, self.rect.height)
        new_rect.center = screen_pos.x, screen_pos.y + (self.hitbox.height - self.rect.height)/2
        renderer.blit(frame, new_rect)
        
        if DEBUG_MODE:
            # Mostrar rect principal
            screen_rect = self.rect.copy()
            screen_rect.x, screen_rect.y = camera.world_to_screen(pygame.Vector2(screen_rect.x, screen_rect.y))
            renderer.draw_rect(screen_rect.x, screen_rect.y, screen_rect.width, screen_rect.height, (255, 0, 0, 0.3))
            
            # Mostrar hitbox
            screen_hitbox = self.hitbox.copy()
            screen_hitbox.x, screen_hitbox.y = camera.world_to_screen(pygame.Vector2(screen_hitbox.x, screen_hitbox.y))
            renderer.draw_rect(screen_hitbox.x, screen_hitbox.y, screen_hitbox.width, screen_hitbox.height, (0, 255, 0, 0.5))

class Enemy:
    def __init__(self, x, y, enemy_type):
        self.position = pygame.Vector2(x, y)
        self.type = enemy_type
        self.speed = 80 if enemy_type == 'guard' else 0
        self.direction = 1
        self.last_side = 'right'
        self.animations = data.assets['enemies'][enemy_type]
        
        # Hitbox fixa baseada na escala
        self.rect = pygame.Rect(0, 0, 64 * data.ratio.x, 64 * data.ratio.y)
        self.rect.x = x
        self.rect.y = y
        
        self.velocity = pygame.Vector2(0, 0)
        self.gravity = 1200
        self.on_ground = False
        self.attack_cooldown = time.time()
        self.projectile_cooldown = time.time()
        self.current_state = 'idle'
        self.platform_rect = None
        self.platform_bounds = None  # Para definir limites da plataforma
    
    def set_platform_bounds(self, left, right):
        self.platform_bounds = (left, right)
            
    def set_platform_rect(self, platform_rect):
        self.platform_rect = platform_rect
        
    def update(self, dt, player, platforms, projectiles):
        self.animations[self.current_state].update()
        
        if self.type == 'guard':
            self.velocity.x = self.speed * self.direction
            
            if self.direction > 0:
                self.last_side = 'right'
            else:
                self.last_side = 'left'
            
            self.velocity.y += self.gravity * dt
            
            # Movimento X
            new_x = self.position.x + self.velocity.x * dt
            test_rect_x = self.rect.copy()
            test_rect_x.x = new_x
            
            # Movimento Y
            new_y = self.position.y + self.velocity.y * dt
            test_rect_y = self.rect.copy()
            test_rect_y.y = new_y
            
            self.on_ground = False
            
            # Colisão Y primeiro
            for platform in platforms:
                if test_rect_y.colliderect(platform):
                    if self.velocity.y > 0:  # Caindo
                        new_y = platform.top - self.rect.height
                        self.velocity.y = 0
                        self.on_ground = True
                    elif self.velocity.y < 0:  # Pulando
                        new_y = platform.bottom
                        self.velocity.y = 0
            
            # Colisão X depois
            collision_x = False
            for platform in platforms:
                if test_rect_x.colliderect(platform):
                    collision_x = True
                    if self.velocity.x > 0:  # Direita
                        new_x = platform.left - self.rect.width
                        self.direction *= -1
                    elif self.velocity.x < 0:  # Esquerda
                        new_x = platform.right
                        self.direction *= -1
            
            # Verificar borda da plataforma apenas se não houver colisão lateral
            if not collision_x and self.on_ground:
                # Verificar se há plataforma à frente
                check_distance = 20
                edge_check = pygame.Rect(
                    new_x + (self.rect.width * 0.5 * self.direction) + (check_distance * self.direction), 
                    new_y + self.rect.height - 5, 
                    10, 10
                )
                
                found_platform = False
                for platform in platforms:
                    if edge_check.colliderect(platform):
                        found_platform = True
                        break
                
                if not found_platform:
                    self.direction *= -1
            
            self.position.x = new_x
            self.position.y = new_y
            self.rect.x = self.position.x
            self.rect.y = self.position.y
            
            if abs(self.velocity.x) > 0:
                self.current_state = 'walk'
            else:
                self.current_state = 'idle'
                
        elif self.type == 'archer':
            self.velocity.y += self.gravity * dt
            
            new_y = self.position.y + self.velocity.y * dt
            test_rect_y = self.rect.copy()
            test_rect_y.y = new_y
            
            self.on_ground = False
            for platform in platforms:
                if test_rect_y.colliderect(platform):
                    if self.velocity.y > 0:  # Caindo
                        new_y = platform.top - self.rect.height
                        self.velocity.y = 0
                        self.on_ground = True
            
            self.position.y = new_y
            self.rect.y = self.position.y
            
            player_distance = abs(player.position.x - self.position.x)
            if player_distance < 250:
                self.current_state = 'idle'
                if player.position.x < self.position.x:
                    self.last_side = 'left'
                else:
                    self.last_side = 'right'
                    
                if time.time() - self.projectile_cooldown >= 2.0:
                    direction = -1 if self.last_side == 'left' else 1
                    projectile = Projectile(self.position.x, self.rect.centery, direction)
                    projectiles.append(projectile)
                    self.projectile_cooldown = time.time()
            else:
                self.current_state = 'idle'
        
        if self.rect.colliderect(player.hitbox) and time.time() - self.attack_cooldown >= 1:
            if self.type == 'guard':
                player.health -= 1
                self.attack_cooldown = time.time()
    
    def render(self, renderer: Renderer, camera: Camera):
        frame = self.animations[self.current_state].get_current_frame()
        
        if self.last_side == 'left':
            frame = pygame.transform.flip(frame, True, False)
            
        screen_pos = camera.world_to_screen((self.rect.x, self.rect.y))
        new_rect = pygame.Rect(screen_pos.x-5*data.ratio.x, screen_pos.y-3*data.ratio.y, self.rect.width+10*data.ratio.x, self.rect.height+6*data.ratio.y)
        renderer.blit(frame, new_rect)
        
        if DEBUG_MODE:
            # Mostrar rect do inimigo
            screen_rect = self.rect.copy()
            screen_rect.x, screen_rect.y = camera.world_to_screen(pygame.Vector2(screen_rect.x, screen_rect.y))
            renderer.draw_rect(screen_rect.x, screen_rect.y, screen_rect.width, screen_rect.height, (255, 0, 0, 0.5))

class GameScene(Scene):
    def on_enter(self, previous_scene=None):
        self.start_time = time.time()
        self.player = Player()
        self.projectiles = []
        self.setup_camera()
        self.setup_ui()
        self.load_level(data.current_level)
        data.register_custom_particles(self)
        return super().on_enter(previous_scene)
    
    def on_exit(self, next_scene=None):
        return super().on_exit(next_scene)
    
    def __init__(self, engine):
        super().__init__(engine)
        self.audio_system: AudioSystem = AudioSystem(16)
        self.audio_system.load_sound_effect('jump', os.path.join('assets', 'jump.wav'))
        self.audio_system.load_sound_effect('attack', os.path.join('assets', 'attack.wav'))
        self.audio_system.load_sound_effect('death', os.path.join('assets', 'death.wav'))
    
    def setup_camera(self):
        self.camera.set_target(self.player, CameraMode.PLATFORMER)
    
    def setup_ui(self):
        self.clear_ui_elements()
        
        self.health_display = TextLabel((15*data.ratio.x), (15*data.ratio.y), 'Vidas: 3', 30, (200, 50, 50), path_font_ninja, root_point=(0, 0))
        self.add_ui_element(self.health_display)
        
        self.time_display = TextLabel(self.engine.width//2, (15*data.ratio.y), 'Tempo: 0:00', 30, (200, 200, 200), path_font_ninja, root_point=(0.5, 0))
        self.add_ui_element(self.time_display)
        
        self.level_display = TextLabel(self.engine.width-(15*data.ratio.x), (15*data.ratio.y), f'Fase {data.current_level}/5', 30, (200, 200, 200), path_font_ninja, root_point=(1, 0))
        self.add_ui_element(self.level_display)
    
    def generate_platform_tiles(self, platform_rect, tile_type):
        tiles = []
        platform_width_tiles = int(platform_rect.width // (64 * data.ratio.x))
        platform_height_tiles = int(platform_rect.height // (64 * data.ratio.y))
        
        for y in range(platform_height_tiles):
            row_tiles = []
            for x in range(platform_width_tiles):
                # Para a linha superior (y == 0)
                if y == 0:
                    if x == 0:
                        # Primeiro tile sempre tipo 0
                        tile_key = 'type0'
                    elif x == platform_width_tiles - 1:
                        # Último tile sempre tipo 1  
                        tile_key = 'type1'
                    else:
                        # Tiles do meio: alternam entre transições
                        prev_tile = row_tiles[x-1][0] if x > 0 else 'type0'
                        
                        if prev_tile == 'type0':
                            # Se anterior é tipo 0, pode ser type0 ou transition_0_1
                            if random.random() < 0.7:  # 70% chance de continuar type0
                                tile_key = 'type0'
                            else:  # 30% chance de transição para type1
                                tile_key = 'transition_0_1'
                        elif prev_tile == 'transition_0_1':
                            # Após transição 0->1, deve ser type1
                            tile_key = 'type1'
                        elif prev_tile == 'type1':
                            # Se anterior é tipo 1, pode ser type1 ou transition_1_0
                            if random.random() < 0.7:  # 70% chance de continuar type1
                                tile_key = 'type1'
                            else:  # 30% chance de transição para type0
                                tile_key = 'transition_1_0'
                        elif prev_tile == 'transition_1_0':
                            # Após transição 1->0, deve ser type0
                            tile_key = 'type0'
                else:
                    # Para linhas inferiores, usa mesma lógica mas com mais aleatoriedade
                    if x == 0:
                        tile_key = 'type0' if random.random() < 0.5 else 'type1'
                    elif x == platform_width_tiles - 1:
                        tile_key = 'type0' if random.random() < 0.5 else 'type1'
                    else:
                        tile_key = 'type0' if random.random() < 0.5 else 'type1'
                
                tile_sprite = data.assets['tiles'][tile_type][tile_key]
                scaled_tile = pygame.transform.scale(tile_sprite, (64 * data.ratio.x, 64 * data.ratio.y))
                tile_pos = (platform_rect.x + x * (64 * data.ratio.x), platform_rect.y + y * (64 * data.ratio.y))
                row_tiles.append((scaled_tile, tile_pos))
            
            tiles.append(row_tiles)
        
        return tiles
    
    def load_level_from_map(self, level_num):
        self.platforms = []
        self.enemies = []
        self.goal = None
        self.platform_tiles = []
        self.projectiles.clear()
        
        level_data = None
        for level in data.maps.get('levels', []):
            if level['level'] == level_num:
                level_data = level
                break
        
        if not level_data:
            self.load_level(level_num)
            return
        
        tile_size = int(64 * data.ratio.x)
        map_width = len(level_data['tiles'][0]) * tile_size
        map_height = len(level_data['tiles']) * tile_size
        
        player_spawned = False
        
        for y, row in enumerate(level_data['tiles']):
            for x, char in enumerate(row):
                if char == 'W':
                    platform_rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
                    self.platforms.append(platform_rect)
                    
                elif char == 'P' and not player_spawned:
                    self.player.position = pygame.Vector2(x * tile_size, (y - 1) * tile_size)
                    player_spawned = True
                    
                elif char == 'G':
                    enemy = Enemy(x * tile_size, (y - 1) * tile_size, 'guard')
                    self.enemies.append(enemy)
                    
                elif char == 'A':
                    enemy = Enemy(x * tile_size, (y - 1) * tile_size, 'archer')
                    self.enemies.append(enemy)
                    
                elif char == 'F':
                    self.goal = pygame.Rect(x * tile_size, (y - 1) * tile_size, tile_size, tile_size)
        
        tile_type = 'forest' if level_num in [1, 2] else 'city' if level_num in [3, 4] else 'house'
        self.platform_tiles = []
        for platform in self.platforms:
            platform_tiles = self.generate_platform_tiles(platform, tile_type)
            self.platform_tiles.append(platform_tiles)
            
        for enemy in self.enemies:
            if enemy.type == 'guard':
                # Encontrar a plataforma onde o inimigo está
                for platform in self.platforms:
                    if (enemy.position.y + enemy.rect.height >= platform.top and 
                        enemy.position.y + enemy.rect.height <= platform.top + 10):  # Está em cima da plataforma
                        enemy.set_platform_bounds(platform.left, platform.right - enemy.rect.width)
                        break
    
    def load_level(self, level_num):
        if data.maps and 'levels' in data.maps:
            self.load_level_from_map(level_num)
    
    def update(self, dt):
        current_time = time.time() - self.start_time
        data.total_time = current_time
        
        time_str = f"{int(current_time//60)}:{int(current_time%60):02d}"
        self.time_display.set_text(f'Tempo: {time_str}')
        self.health_display.set_text(f'Vidas: {self.player.health}')
        
        self.player.update(dt, self.platforms, self.engine)
        
        for enemy in self.enemies:
            enemy.update(dt, self.player, self.platforms, self.projectiles)
        
        for projectile in self.projectiles[:]:
            projectile.update(dt)
            if not projectile.active:
                self.projectiles.remove(projectile)
            elif projectile.rect.colliderect(self.player.hitbox):
                self.player.health -= 1
                self.projectiles.remove(projectile)
        
        self.camera.update(dt)
        self.particle_system.update(dt, self.camera.position)
        
        if self.player.health <= 0:
            self.engine.set_scene("game_over")
            return
            
        if self.goal and self.player.rect.colliderect(self.goal):
            data.levels_completed.append(data.current_level)
            data.current_level += 1
            
            if data.current_level > 5:
                self.engine.set_scene("victory")
            else:
                self.load_level(data.current_level)
                self.level_display.set_text(f'Fase {data.current_level}/5')
                self.player.position = pygame.Vector2(100, 400)
                self.player.health = 3
    
    def render(self, renderer:Renderer):
        bg_key = f'level{data.current_level}'
        if bg_key in data.assets['backgrounds']:
            renderer.blit(data.assets['backgrounds'][bg_key], (0, 0))
        else:
            if data.current_level in [1, 2]:
                renderer.fill_screen((50, 120, 80))
            elif data.current_level in [3, 4]:
                renderer.fill_screen((80, 80, 120))
            else:
                renderer.fill_screen((100, 80, 60))
        
        for i, platform_tiles in enumerate(self.platform_tiles):
            for row in platform_tiles:
                for tile_sprite, tile_pos in row:
                    screen_pos = self.camera.world_to_screen(pygame.Vector2(tile_pos[0], tile_pos[1]))
                    renderer.blit(tile_sprite, screen_pos)
        
        for enemy in self.enemies:
            enemy.render(renderer, self.camera)
        
        for projectile in self.projectiles:
            projectile.render(renderer, self.camera)
        
        if self.goal:
            goal_pos = self.camera.world_to_screen(pygame.Vector2(self.goal.x, self.goal.y))
            renderer.draw_rect(goal_pos.x, goal_pos.y, self.goal.width, self.goal.height, (50, 200, 50))
            if DEBUG_MODE:
                renderer.draw_rect(goal_pos.x, goal_pos.y, self.goal.width, self.goal.height, (0, 255, 0, 0.5))
        
        self.player.render(renderer, self.camera)
        
        if DEBUG_MODE:
            for platform in self.platforms:
                platform_pos = self.camera.world_to_screen(pygame.Vector2(platform.x, platform.y))
                renderer.draw_rect(platform_pos.x, platform_pos.y, platform.width, platform.height, (0, 0, 255, 0.5))
        
        renderer.draw_rect(0, 0, self.engine.width, 60*data.ratio.y, (0, 0, 0, 150))

def main():
    engine = LunaEngine("Scarf of Night", 1280, 720, True)
    engine.initialize()
    
    data.ratio = pygame.Vector2(engine.width / 1280, engine.height / 720)
    
    engine.add_scene("main", MainMenu)
    engine.add_scene("game", GameScene)
    engine.add_scene("game_over", GameOverScene)
    engine.add_scene("victory", VictoryScene)
    
    engine.set_scene("main")
    
    data.load_assets()
    data.load_player_animations()
    
    engine.run()
    
if __name__ == "__main__":
    main()