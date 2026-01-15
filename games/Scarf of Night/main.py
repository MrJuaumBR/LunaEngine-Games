from lunaengine.core import LunaEngine, Scene, Renderer, AudioSystem
from lunaengine.ui import *
from lunaengine.graphics import SpriteSheet, Animation, Camera, CameraMode, ParticleConfig, ParticleType
import pygame, os, random, time, json, sys

path_assets = os.path.abspath('./assets/')
path_font_ninja = os.path.join(path_assets, 'ninja_font.ttf')

DEBUG_MODE = '--debug' in sys.argv

class Data:
    def __init__(self):
        self.player_name = ""
        self.leaderboard = {"scores": []}
        self.player_animations = {}
        self.assets = {}
        self.ratio = pygame.Vector2(1, 1)
        self.total_time = 0.0
        self.current_level = 1
        self.levels_completed = []
        self.maps = {}
        
        self.load_leaderboard()
        self.load_maps()
    
    def load_leaderboard(self):
        try:
            if os.path.exists('./leaderboard.json'):
                with open('./leaderboard.json', 'r') as f:
                    self.leaderboard = json.load(f)
        except Exception as e:
            print(f"Erro ao carregar leaderboard: {e}")
            self.leaderboard = {"scores": []}
    
    def save_leaderboard(self):
        try:
            with open('./leaderboard.json', 'w') as f:
                json.dump(self.leaderboard, f, indent=2)
        except Exception as e:
            print(f"Erro ao salvar leaderboard: {e}")
                
    def load_maps(self):
        try:
            maps_path = os.path.join(path_assets, 'maps.json')
            if os.path.exists(maps_path):
                with open(maps_path, 'r') as f:
                    self.maps = json.load(f)
        except Exception as e:
            print(f"Erro ao carregar mapas: {e}")
            self.maps = {}
                
    def add_score(self, player_name, time_score):
        self.leaderboard["scores"].append({
            "name": player_name,
            "time": round(time_score, 2),
            "date": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        self.leaderboard["scores"].sort(key=lambda x: x["time"])
        self.leaderboard["scores"] = self.leaderboard["scores"][:10]
        self.save_leaderboard()
            
    def get_score_index(self, player_name):
        for i, score in enumerate(self.leaderboard["scores"]):
            if score["name"] == player_name:
                return i
        return -1
                
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
        
        try:
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
            
            # Carregar backgrounds JPG com parallax infinito
            self.assets['backgrounds'] = {}
            background_files = {
                1: 'background_1.jpg',  # Floresta
                2: 'background_1.jpg',  # Floresta  
                3: 'background_2.jpg',  # Cidade
                4: 'background_2.jpg',  # Cidade
                5: 'background_3.jpg'   # Casa
            }
            
            for level_num, bg_file in background_files.items():
                bg_path = os.path.join(path_assets, bg_file)
                if os.path.exists(bg_path):
                    try:
                        # Carrega a imagem
                        bg_image = pygame.image.load(bg_path)
                        self.assets['backgrounds'][f'level{level_num}'] = scaled_bg
                    except Exception as e:
                        print(f"Erro ao carregar background {bg_file}: {e}")
                        # Fallback: criar background colorido
                        if level_num in [1, 2]:
                            self.assets['backgrounds'][f'level{level_num}'] = None
                        elif level_num in [3, 4]:
                            self.assets['backgrounds'][f'level{level_num}'] = None
                        else:
                            self.assets['backgrounds'][f'level{level_num}'] = None
                else:
                    print(f"Arquivo de background não encontrado: {bg_file}")
                    self.assets['backgrounds'][f'level{level_num}'] = None
            
            enemy_ss = os.path.join(path_assets, 'enemies.png')
            self.assets['enemies'] = {
                'guard': {
                    'idle': Animation(enemy_ss, (32, 32), (0, 0), 4, 
                                    scale=(2*self.ratio.x, 2*self.ratio.y), duration=1.0, loop=True),
                    'walk': Animation(enemy_ss, (32, 32), (0, 32), 4, 
                                    scale=(2*self.ratio.x, 2*self.ratio.y), duration=0.6, loop=True)
                },
                'archer': {
                    'idle': Animation(enemy_ss, (32, 32), (0, 64), 4, 
                                    scale=(2*self.ratio.x, 2*self.ratio.y), duration=1.0, loop=True),
                    'walk': Animation(enemy_ss, (32, 32), (0, 96), 4, 
                                    scale=(2*self.ratio.x, 2*self.ratio.y), duration=0.6, loop=True)
                }
            }
            
            flag_path = os.path.join(path_assets, 'flag.png')
            if os.path.exists(flag_path):
                self.assets['flag'] = Animation(flag_path, (32, 32), (0, 0), 8, 
                                            scale=(2*self.ratio.x, 2*self.ratio.y), 
                                            duration=1.0, loop=True)
            else:
                print("Aviso: Arquivo da flag não encontrado")
                self.assets['flag'] = None
                
        except Exception as e:
            print(f"Erro ao carregar assets: {e}")
        
    def load_player_animations(self):
        try:
            player_ss = os.path.join(path_assets, 'player.png')
            self.player_animations = {
                'idle': Animation(player_ss, (32, 32), (0,0), 22, 
                                scale=(2*self.ratio.x, 2*self.ratio.y), duration=2.0, loop=True),
                'run': Animation(player_ss, (32, 32), (0,32), 11, 
                               scale=(2*self.ratio.x, 2*self.ratio.y), duration=0.7, loop=True),
                'jump': Animation(player_ss, (32, 32), (0,64), 10, 
                                scale=(2*self.ratio.x, 2*self.ratio.y), duration=1, loop=True),
                'attack_0': Animation(player_ss, (32, 32), (0,96), 18, 
                                    scale=(2*self.ratio.x, 2*self.ratio.y), duration=0.65, loop=True),
                'attack_1': Animation(player_ss, (32, 32), (0,128), 23, 
                                    scale=(2*self.ratio.x, 2*self.ratio.y), duration=0.65, loop=True),
            }
        except Exception as e:
            print(f"Erro ao carregar animações do player: {e}")

data = Data()

class ParallaxBackground:
    """Sistema de background com parallax infinito"""
    def __init__(self, background_surface, camera, speed_factor=0.5):
        self.background = background_surface
        self.camera = camera
        self.speed_factor = speed_factor  # 0.0 = estático, 1.0 = move com câmera
        self.bg_width = background_surface.get_width()
        self.bg_height = background_surface.get_height()
        
    def render(self, renderer):
        if not self.background:
            return
            
        # Calcula a posição base do background baseado na posição da câmera
        camera_x = self.camera.position.x
        camera_y = self.camera.position.y
        
        # Aplica o fator de velocidade do parallax
        parallax_x = camera_x * self.speed_factor
        parallax_y = camera_y * self.speed_factor
        
        # Calcula quantas cópias do background são necessárias
        start_x = int(parallax_x // self.bg_width) - 1
        end_x = int((parallax_x + self.camera.viewport_width) // self.bg_width) + 2
        
        start_y = int(parallax_y // self.bg_height) - 1
        end_y = int((parallax_y + self.camera.viewport_height) // self.bg_height) + 2
        
        # Renderiza todas as cópias necessárias
        for x in range(start_x, end_x):
            for y in range(start_y, end_y):
                bg_x = x * self.bg_width - parallax_x
                bg_y = y * self.bg_height - parallax_y
                
                # Verifica se está dentro da tela
                if (bg_x + self.bg_width > 0 and bg_x < self.camera.viewport_width and
                    bg_y + self.bg_height > 0 and bg_y < self.camera.viewport_height):
                    
                    renderer.blit(self.background, (bg_x, bg_y))

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
        
    def on_enter(self, previous_scene=None):
        self.engine.set_global_theme(ThemeType.DEEP_SPACE)
        self.clear_ui_elements()
        self.setup_ui()
        return super().on_enter(previous_scene)
    
    def setup_ui(self):
        self.add_ui_element(TextLabel(self.engine.width//2, 100*data.ratio.y, 
                                    'Missão Falhou!', 72, (200, 100, 100), 
                                    path_font_ninja, root_point=(0.5, 0)))
        
        time_str = f"{int(data.total_time//60)}:{int(data.total_time%60):02d}"
        self.time_label = TextLabel(self.engine.width//2, 200*data.ratio.y, 
                                  f'Tempo: {time_str}', 48, (200, 170, 100), 
                                  path_font_ninja, root_point=(0.5, 0))
        self.add_ui_element(self.time_label)
        
        self.menu_button = Button(self.engine.width//2, 350*data.ratio.y, 
                                250*data.ratio.x, 65*data.ratio.y, 
                                'Voltar ao Menu', 48, path_font_ninja, 
                                root_point=(0.5, 0))
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
        renderer.draw_rect(0, 0, self.engine.width, self.engine.height, 
                         ThemeManager.get_color('background'))

class VictoryScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        
    def on_enter(self, previous_scene=None):
        self.engine.set_global_theme(ThemeType.BUILDER)
        self.clear_ui_elements()
        self.setup_ui()
        
        if not hasattr(self, 'score_saved'):
            data.add_score(data.player_name, data.total_time)
            self.score_saved = True
            
        return super().on_enter(previous_scene)
    
    def setup_ui(self):
        self.add_ui_element(TextLabel(self.engine.width//2, 100*data.ratio.y, 
                                    'Missão Concluída!', 72, (100, 200, 100), 
                                    path_font_ninja, root_point=(0.5, 0)))
        
        time_str = f"{int(data.total_time//60)}:{int(data.total_time%60):02d}"
        self.time_label = TextLabel(self.engine.width//2, 200*data.ratio.y, 
                                  f'Tempo Total: {time_str}', 48, (200, 170, 100), 
                                  path_font_ninja, root_point=(0.5, 0))
        self.add_ui_element(self.time_label)
        
        player_position = data.get_score_index(data.player_name)
        if player_position >= 0:
            position_text = f'Posição no Ranking: #{player_position + 1}'
        else:
            position_text = 'Fora do Ranking'
            
        self.position_label = TextLabel(self.engine.width//2, 260*data.ratio.y, 
                                      position_text, 36, (200, 170, 100), 
                                      path_font_ninja, root_point=(0.5, 0))
        self.add_ui_element(self.position_label)
        
        self.menu_button = Button(self.engine.width//2, 350*data.ratio.y, 
                                250*data.ratio.x, 65*data.ratio.y, 
                                'Voltar ao Menu', 48, path_font_ninja, 
                                root_point=(0.5, 0))
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
        renderer.draw_rect(0, 0, self.engine.width, self.engine.height, 
                         ThemeManager.get_color('background'))

class MainMenu(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.setup_ui()
        
    def on_enter(self, previous_scene=None):
        self.engine.set_global_theme(ThemeType.DEEP_SPACE)
        self.update_leaderboard()
        return super().on_enter(previous_scene)
    
    def setup_ui(self):
        self.add_ui_element(TextLabel(self.engine.width//2, 30*data.ratio.y, 
                                    'Scarf of Night', 108, (200, 50, 50), 
                                    path_font_ninja, root_point=(0.5, 0)))
        
        self.play_button = Button(self.engine.width//2, 150*data.ratio.y, 
                                360*data.ratio.x, 58*data.ratio.y, 
                                'Iniciar Missão', 52, path_font_ninja, 
                                root_point=(0.5, 0))
        self.play_button.set_on_click(self.play)
        self.add_ui_element(self.play_button)
        
        self.exit_button = Button(self.engine.width//2, 220*data.ratio.y, 
                                160*data.ratio.x, 52*data.ratio.y, 
                                'Sair', 50, path_font_ninja, root_point=(0.5, 0))
        self.exit_button.set_on_click(self.quit)
        self.add_ui_element(self.exit_button)
        
        self.add_ui_element(TextLabel(self.engine.width//2, 275*data.ratio.y, 
                                    'Nome e Turma:', 26, (200, 170, 100), 
                                    path_font_ninja, root_point=(0.5, 0)))
        self.name_textbox = TextBox(self.engine.width//2, 315*data.ratio.y, 
                                  200*data.ratio.x, 30*data.ratio.y, 
                                  '', 24, path_font_ninja, root_point=(0.5, 0))
        self.add_ui_element(self.name_textbox)
        
        self.leaderboard_label = TextLabel(self.engine.width//2, 370*data.ratio.y, 
                                         'Leaderboard', 42, (200, 170, 100), 
                                         path_font_ninja, root_point=(0.5, 0))
        self.add_ui_element(self.leaderboard_label)
        
        self.leaderboard_frame = ScrollingFrame(self.engine.width//2, 
                                              int(430*data.ratio.y), 
                                              int(400*data.ratio.x), 
                                              int(200*data.ratio.y), 
                                              380*data.ratio.x, 400*data.ratio.y, 
                                              root_point=(0.5, 0))
        self.add_ui_element(self.leaderboard_frame)
        
    def update_leaderboard(self):
        self.leaderboard_frame.children.clear()
        
        if not data.leaderboard["scores"]:
            no_scores = TextLabel(190*data.ratio.x, 20*data.ratio.y, 
                                'Nenhuma pontuação ainda!', 24, (150, 150, 150), 
                                path_font_ninja, root_point=(0.5, 0))
            self.leaderboard_frame.add_child(no_scores)
            return
            
        for i, score_data in enumerate(data.leaderboard["scores"]):
            y_pos = 20 + (i * 35)
            time_str = f"{int(score_data['time']//60)}:{int(score_data['time']%60):02d}"
            rank_text = f"#{i+1} {score_data['name']} - {time_str}"
            score_label = TextLabel(10*data.ratio.x, y_pos*data.ratio.y, 
                                  rank_text, 20, (200, 170, 100), 
                                  path_font_ninja, root_point=(0, 0))
            self.leaderboard_frame.add_child(score_label)
        
    def update(self, dt):
        pass
        
    def play(self):
        if not self.name_textbox.text.strip():
            return
        data.player_name = self.name_textbox.text.strip()
        self.engine.set_scene("game")
        
    def quit(self):
        self.engine.shutdown()
        sys.exit()
        
    def render(self, renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))

class Player:
    def __init__(self):
        self.animations = data.player_animations
        self.current_state = 'idle'
        self.facing_right = True
        self.attack_index = 0
        
        # Sistema de física integrado - CORREÇÃO: Posição inicial zerada
        self.position = pygame.Vector2(0, 0)  # Será definida no carregamento do nível
        self.velocity = pygame.Vector2(0, 0)
        self.acceleration = pygame.Vector2(0, 0)
        
        # Constantes de física otimizadas
        self.GRAVITY = 1800
        self.HORIZONTAL_ACCELERATION = 1200
        self.MAX_VELOCITY_X = 400
        self.MAX_VELOCITY_Y = 800
        self.JUMP_VELOCITY = -775
        self.DASH_VELOCITY = 500
        self.WALL_JUMP_VELOCITY = -550
        self.WALL_JUMP_HORIZONTAL_VELOCITY = 350
        
        # Atrito
        self.GROUND_FRICTION = 0.85
        self.AIR_FRICTION = 0.98
        
        # Estados - CORREÇÃO: Inicializar todos como False
        self.on_ground = False
        self.wall_left = False
        self.wall_right = False
        self.direction = 1  # Começa virado para direita
        self.moving = False  # Nova variável para controle de movimento
        
        # Recursos
        self.stamina = 100
        self.state = "normal"
        self.dash_cooldown = 0
        self.wall_jump_cooldown = 0
        
        # Sistema de hitbox - CORREÇÃO: Tamanho base padrão
        self.rect = pygame.Rect(0, 0, 64, 64)  # Tamanho padrão
        self.hitbox = pygame.Rect(0, 0, 38, 51)  # 60% de 64, 80% de 64
        self.hitbox.center = self.rect.center
        
        # Sistema de combate
        self.attack_cooldown = 0
        self.attack_duration = 0
        self.is_attacking = False
        self.attack_hitbox = None
        self.health = 3
        self.iframes = 0
        
    def update_physics(self, dt):
        """Atualiza a física do player - CORREÇÃO: Movimento condicional"""
        # Aplica gravidade
        self.acceleration.y += self.GRAVITY
        
        # CORREÇÃO: Só aplica aceleração horizontal se estiver se movendo
        if self.moving:
            self.acceleration.x += self.HORIZONTAL_ACCELERATION * self.direction
        else:
            self.acceleration.x = 0  # Para movimento imediato
        
        # Atualiza velocidade
        self.velocity += self.acceleration * dt
        self.acceleration = pygame.Vector2(0, 0)
        
        # Aplica atrito
        if self.on_ground:
            self.velocity.x *= self.GROUND_FRICTION
        else:
            self.velocity.x *= self.AIR_FRICTION
        
        # Limita velocidade
        self.velocity.x = max(-self.MAX_VELOCITY_X, min(self.velocity.x, self.MAX_VELOCITY_X))
        self.velocity.y = max(-self.MAX_VELOCITY_Y, min(self.velocity.y, self.MAX_VELOCITY_Y))
        
        # Atualiza cooldowns
        if self.dash_cooldown > 0:
            self.dash_cooldown -= dt
        if self.wall_jump_cooldown > 0:
            self.wall_jump_cooldown -= dt
    
    def handle_movement(self, keys, dt):
        """Lida com todos os movimentos do player - CORREÇÃO: Controle de movimento"""
        # Movimento horizontal simples - CORREÇÃO: Variável moving controla se está se movendo
        moving_left = keys[pygame.K_a] or keys[pygame.K_LEFT]
        moving_right = keys[pygame.K_d] or keys[pygame.K_RIGHT]
        
        # CORREÇÃO: Define se está se movendo e a direção
        self.moving = moving_left or moving_right
        
        if moving_left and not moving_right:
            self.direction = -1
            self.facing_right = False
        elif moving_right and not moving_left:
            self.direction = 1
            self.facing_right = True
        # Se ambas as teclas estão pressionadas ou nenhuma, mantém a direção atual mas para movimento
        else:
            self.moving = False
        
        # Pulo
        jump_pressed = keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]
        if jump_pressed and self.on_ground:
            self.velocity.y = self.JUMP_VELOCITY
            self.on_ground = False
            self.current_state = 'jump'
        
        # Wall jump (pulo na parede)
        elif jump_pressed and self.wall_jump_cooldown <= 0 and (self.wall_left or self.wall_right):
            if self.wall_left:
                self.velocity.y = self.WALL_JUMP_VELOCITY
                self.velocity.x = self.WALL_JUMP_HORIZONTAL_VELOCITY
                self.direction = 1
                self.facing_right = True
                self.wall_jump_cooldown = 0.3
                self.current_state = 'jump'
            elif self.wall_right:
                self.velocity.y = self.WALL_JUMP_VELOCITY
                self.velocity.x = -self.WALL_JUMP_HORIZONTAL_VELOCITY
                self.direction = -1
                self.facing_right = False
                self.wall_jump_cooldown = 0.3
                self.current_state = 'jump'
        
        # Dash (teletransporte rápido)
        dash_pressed = keys[pygame.K_LSHIFT] or keys[pygame.K_LCTRL]
        if dash_pressed and self.dash_cooldown <= 0 and self.stamina >= 20:
            self.velocity.x = self.DASH_VELOCITY * self.direction
            self.dash_cooldown = 1.0
            self.stamina -= 20
            self.current_state = 'run'
    
    def update_attack(self, keys, engine, dt, current_anim):
        """Atualiza sistema de ataque"""
        attack_pressed = keys[pygame.K_f] or keys[pygame.K_j] or engine.input_state.mouse_buttons_pressed.left
        
        if attack_pressed and not self.is_attacking and self.on_ground:
            self.current_state = 'attack'
            self.is_attacking = True
            self.attack_index = (self.attack_index + 1) % 2
            self.attack_cooldown = time.time()
            self.attack_duration = current_anim.duration
            
            # Hitbox de ataque
            attack_width = 60 * data.ratio.x
            attack_height = 40 * data.ratio.y
            
            if self.facing_right:
                self.attack_hitbox = pygame.Rect(
                    self.hitbox.right, 
                    self.hitbox.centery - attack_height//2,
                    attack_width, attack_height
                )
            else:
                self.attack_hitbox = pygame.Rect(
                    self.hitbox.left - attack_width,
                    self.hitbox.centery - attack_height//2,
                    attack_width, attack_height
                )

        # Fim do ataque
        if self.is_attacking and time.time() - self.attack_cooldown >= self.attack_duration:
            self.is_attacking = False
            self.current_state = 'idle'
            self.attack_hitbox = None
            self.animations[f'attack_{self.attack_index}'].current_frame_index = 0
    
    def update_collision(self, platforms, dt):
        """Sistema de colisão otimizado"""
        # Reset estados
        self.on_ground = False
        self.wall_left = False
        self.wall_right = False
        
        # Movimento X primeiro
        new_x = self.position.x + self.velocity.x * dt
        test_rect_x = self.hitbox.copy()
        test_rect_x.x = new_x
        
        # Colisão X
        for platform in platforms:
            if test_rect_x.colliderect(platform):
                if self.velocity.x > 0:  # Direita
                    new_x = platform.left - self.hitbox.width
                    self.wall_right = True
                elif self.velocity.x < 0:  # Esquerda
                    new_x = platform.right
                    self.wall_left = True
                self.velocity.x = 0
        
        self.position.x = new_x
        
        # Movimento Y depois
        new_y = self.position.y + self.velocity.y * dt
        test_rect_y = self.hitbox.copy()
        test_rect_y.y = new_y
        
        # Colisão Y
        for platform in platforms:
            if test_rect_y.colliderect(platform):
                if self.velocity.y > 0:  # Caindo
                    new_y = platform.top - self.hitbox.height
                    self.velocity.y = 0
                    self.on_ground = True
                elif self.velocity.y < 0:  # Subindo
                    new_y = platform.bottom
                    self.velocity.y = 0
        
        self.position.y = new_y
        
        # Atualiza hitbox e rect
        self.hitbox.x = self.position.x
        self.hitbox.y = self.position.y
        self.rect.center = self.hitbox.center
    
    def update_animation_state(self):
        """Atualiza estado da animação baseado no estado físico"""
        if self.is_attacking:
            return  # Mantém estado de ataque
        
        if not self.on_ground:
            if self.wall_left or self.wall_right:
                self.current_state = 'jump'  # Poderia ser uma animação de wall slide
            else:
                self.current_state = 'jump'
        elif abs(self.velocity.x) > 50:
            self.current_state = 'run'
        else:
            self.current_state = 'idle'
    
    def update_resources(self, dt):
        """Atualiza recursos do player"""
        # Regenera stamina
        if self.on_ground or self.wall_left or self.wall_right:
            self.stamina = min(100, self.stamina + 25 * dt)
        else:
            self.stamina = min(100, self.stamina + 10 * dt)
    
    def update(self, dt, platforms, engine: LunaEngine):
        """Update principal do player"""
        if self.iframes > 0:
            self.iframes -= dt
        
        # Atualiza animação atual
        current_anim = self.animations[f'attack_{self.attack_index}' if self.current_state == 'attack' else self.current_state]
        current_anim.update()
        
        keys = pygame.key.get_pressed()
        
        # Processa todos os sistemas
        self.update_physics(dt)
        self.handle_movement(keys, dt)
        self.update_attack(keys, engine, dt, current_anim)
        self.update_collision(platforms, dt)
        self.update_animation_state()
        self.update_resources(dt)
        
        # Morte por queda
        if self.position.y > 2500:
            self.health = 0
    
    def take_damage(self):
        if self.iframes <= 0:
            self.health -= 1
            self.iframes = 1.0
            return True
        return False
    
    def render(self, renderer: Renderer, camera: Camera):
        if self.iframes > 0 and int(self.iframes * 10) % 2 == 0:
            return
            
        frame = self.animations[f'attack_{self.attack_index}' if self.current_state == 'attack' else self.current_state].get_current_frame()
        if not self.facing_right:
            frame = pygame.transform.flip(frame, True, False)
        
        screen_pos = camera.world_to_screen((self.hitbox.centerx, self.hitbox.centery))
        
        new_rect = pygame.Rect(0,0, self.rect.width, self.rect.height)
        new_rect.center = screen_pos.x, screen_pos.y + (self.hitbox.height - self.rect.height)/2
        renderer.blit(frame, new_rect)
        
        if DEBUG_MODE:
            # Debug visuals
            screen_rect = self.rect.copy()
            screen_rect.x, screen_rect.y = camera.world_to_screen(pygame.Vector2(screen_rect.x, screen_rect.y))
            renderer.draw_rect(screen_rect.x, screen_rect.y, screen_rect.width, screen_rect.height, (255, 0, 0, 0.3))
            
            screen_hitbox = self.hitbox.copy()
            screen_hitbox.x, screen_hitbox.y = camera.world_to_screen(pygame.Vector2(screen_hitbox.x, screen_hitbox.y))
            renderer.draw_rect(screen_hitbox.x, screen_hitbox.y, screen_hitbox.width, screen_hitbox.height, (0, 255, 0, 0.5))
            
            if self.is_attacking and self.attack_hitbox:
                screen_attack = self.attack_hitbox.copy()
                screen_attack.x, screen_attack.y = camera.world_to_screen(pygame.Vector2(screen_attack.x, screen_attack.y))
                renderer.draw_rect(screen_attack.x, screen_attack.y, screen_attack.width, screen_attack.height, (255, 255, 0, 0.5))
            
            # Mostrar recursos
            font = pygame.font.Font(None, 24)
            stamina_text = f"Stamina: {int(self.stamina)}"
            stamina_surface = font.render(stamina_text, True, (0, 255, 0))
            renderer.blit(stamina_surface, (10, 100))

class Enemy:
    def __init__(self, x, y, enemy_type):
        self.position = pygame.Vector2(x, y)
        self.type = enemy_type
        self.speed = 80 if enemy_type == 'guard' else 0
        self.direction = 1
        self.last_side = 'right'
        self.animations = data.assets['enemies'][enemy_type]
        
        frame = self.animations['idle'].get_current_frame()
        frame_width, frame_height = frame.get_size()
        
        self.rect = pygame.Rect(0, 0, 64 * data.ratio.x, 64 * data.ratio.y)
        self.rect.x = x
        self.rect.y = y
        
        self.velocity = pygame.Vector2(0, 0)
        self.gravity = 1200
        self.on_ground = False
        self.attack_cooldown = time.time()
        self.projectile_cooldown = time.time()
        self.current_state = 'idle'
        self.platform_bounds = None
        self.health = 1
        self.iframes = 0
    
    def set_platform_bounds(self, left, right):
        self.platform_bounds = (left, right)
            
    def update(self, dt, player, platforms, projectiles):
        if self.iframes > 0:
            self.iframes -= dt
            
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
            
            # Verificar borda da plataforma
            if not collision_x and self.on_ground:
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
        
        # Dano ao player por contato
        if self.rect.colliderect(player.hitbox) and time.time() - self.attack_cooldown >= 1:
            if self.type == 'guard':
                if player.take_damage():
                    self.attack_cooldown = time.time()
    
    def take_damage(self):
        if self.iframes <= 0:
            self.health -= 1
            self.iframes = 0.5
            return True
        return False
    
    def render(self, renderer: Renderer, camera: Camera):
        if self.iframes > 0 and int(self.iframes * 10) % 2 == 0:
            return
            
        frame = self.animations[self.current_state].get_current_frame()
        
        if self.last_side == 'left':
            frame = pygame.transform.flip(frame, True, False)
            
        screen_pos = camera.world_to_screen((self.rect.x, self.rect.y))
        new_rect = pygame.Rect(screen_pos.x-5*data.ratio.x, screen_pos.y-3*data.ratio.y, 
                             self.rect.width+10*data.ratio.x, self.rect.height+6*data.ratio.y)
        renderer.blit(frame, new_rect)
        
        if DEBUG_MODE:
            screen_rect = self.rect.copy()
            screen_rect.x, screen_rect.y = camera.world_to_screen(pygame.Vector2(screen_rect.x, screen_rect.y))
            renderer.draw_rect(screen_rect.x, screen_rect.y, screen_rect.width, screen_rect.height, (255, 0, 0, 0.5))

class GameScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.audio_system: AudioSystem = AudioSystem(16)
        self.background_music = None
        self.parallax_bg = None
        
        try:
            # Carregar efeitos sonoros
            self.audio_system.load_sound_effect('jump', os.path.join('assets', 'jump.wav'))
            self.audio_system.load_sound_effect('attack', os.path.join('assets', 'attack.wav'))
            self.audio_system.load_sound_effect('death', os.path.join('assets', 'death.wav'))
            self.audio_system.load_sound_effect('dash', os.path.join('assets', 'dash.wav'))
            
            # Carregar música de fundo
            music_path = os.path.join('assets', 'music.mp3')
            if os.path.exists(music_path):
                try:
                    pygame.mixer.music.load(music_path)
                    pygame.mixer.music.set_volume(0.5)
                    pygame.mixer.music.play(-1)  # -1 para loop infinito
                    print("Música de fundo carregada e tocando")
                except Exception as e:
                    print(f"Erro ao carregar música: {e}")
            else:
                print("Arquivo de música não encontrado")
                
        except Exception as e:
            print(f"Erro ao carregar sons: {e}")
    
    def on_enter(self, previous_scene=None):
        self.start_time = time.time()
        self.player = Player()
        self.projectiles = []
        self.setup_camera()
        self.setup_ui()
        self.load_level(data.current_level)
        data.register_custom_particles(self)
        
        # Configurar background parallax
        self.setup_parallax_background()
        
        if 'flag' in data.assets and data.assets['flag']:
            data.assets['flag'].current_frame_index = 0
        return super().on_enter(previous_scene)
    
    def setup_parallax_background(self):
        """Configura o sistema de parallax para o nível atual"""
        bg_key = f'level{data.current_level}'
        if bg_key in data.assets['backgrounds'] and data.assets['backgrounds'][bg_key] is not None:
            background_surface = data.assets['backgrounds'][bg_key]
            self.parallax_bg = ParallaxBackground(background_surface, self.camera, speed_factor=0.3)
            print(f"Background parallax configurado para {bg_key}")
        else:
            self.parallax_bg = None
            print(f"Usando fallback background para {bg_key}")
    
    def setup_camera(self):
        self.camera.set_target(self.player, CameraMode.PLATFORMER)
    
    def setup_ui(self):
        self.clear_ui_elements()
        
        self.health_display = TextLabel((15*data.ratio.x), (15*data.ratio.y), 
                                      'Vidas: 3', 30, (200, 50, 50), 
                                      path_font_ninja, root_point=(0, 0))
        self.add_ui_element(self.health_display)
        
        self.time_display = TextLabel(self.engine.width//2, (15*data.ratio.y), 
                                    'Tempo: 0:00', 30, (200, 200, 200), 
                                    path_font_ninja, root_point=(0.5, 0))
        self.add_ui_element(self.time_display)
        
        self.level_display = TextLabel(self.engine.width-(15*data.ratio.x), (15*data.ratio.y), 
                                     f'Fase {data.current_level}/5', 30, (200, 200, 200), 
                                     path_font_ninja, root_point=(1, 0))
        self.add_ui_element(self.level_display)
    
    def determine_tile_type(self, tile_map, x, y, tile_type):
        """Sistema melhorado para determinar o tipo de tile"""
        height = len(tile_map)
        width = len(tile_map[0])
        
        if tile_map[y][x] != 'W':
            return None
        
        # Verifica tiles vizinhos
        left = x > 0 and tile_map[y][x-1] == 'W'
        right = x < width - 1 and tile_map[y][x+1] == 'W'
        top = y > 0 and tile_map[y-1][x] == 'W'
        bottom = y < height - 1 and tile_map[y+1][x] == 'W'
        
        # Tile solitário
        if not any([left, right, top, bottom]):
            return 'type0'
        
        # Tile com todos os vizinhos
        if all([left, right, top, bottom]):
            return 'type0'
        
        # Transições horizontais
        if left and right and not top and not bottom:
            return 'type0'
        
        # Transições verticais
        if top and bottom and not left and not right:
            return 'type0'
        
        # Cantos e bordas - sistema simplificado
        # Para tiles com padrão mais simples
        zone_x = x // 2  # Zonas menores para mais variedade
        zone_y = y // 2
        
        # Padrão de xadrez simples
        if (zone_x + zone_y) % 2 == 0:
            return 'type0'
        else:
            return 'type1'
    
    def generate_level_tiles(self, level_num):
        """Gera os tiles do nível com sistema melhorado"""
        level_data = None
        for level in data.maps.get('levels', []):
            if level['level'] == level_num:
                level_data = level
                break
        
        if not level_data:
            return []
        
        tile_size = int(64 * data.ratio.x)
        map_height = len(level_data['tiles'])
        map_width = len(level_data['tiles'][0])
        
        # Determina o tema baseado no nível
        if level_num in [1, 2]:
            tile_type = 'forest'
        elif level_num in [3, 4]:
            tile_type = 'city'
        else:
            tile_type = 'house'
        
        tile_matrix = []
        for y in range(map_height):
            tile_row = []
            for x in range(map_width):
                char = level_data['tiles'][y][x]
                
                if char == 'W':
                    tile_key = self.determine_tile_type(level_data['tiles'], x, y, tile_type)
                    if tile_key and tile_key in data.assets['tiles'][tile_type]:
                        tile_sprite = data.assets['tiles'][tile_type][tile_key]
                        scaled_tile = pygame.transform.scale(tile_sprite, (tile_size, tile_size))
                        
                        tile_pos = (x * tile_size, y * tile_size)
                        tile_row.append((scaled_tile, tile_pos, tile_key, True))
                    else:
                        # Fallback para type0 se a chave não for encontrada
                        tile_sprite = data.assets['tiles'][tile_type]['type0']
                        scaled_tile = pygame.transform.scale(tile_sprite, (tile_size, tile_size))
                        tile_pos = (x * tile_size, y * tile_size)
                        tile_row.append((scaled_tile, tile_pos, 'type0', True))
                else:
                    tile_row.append((None, (x * tile_size, y * tile_size), None, False))
            
            tile_matrix.append(tile_row)
        
        return tile_matrix
    
    def load_level_from_map(self, level_num):
        self.platforms = []
        self.enemies = []
        self.goal = None
        self.level_tiles = []
        self.projectiles.clear()
        
        level_data = None
        for level in data.maps.get('levels', []):
            if level['level'] == level_num:
                level_data = level
                break
        
        if not level_data:
            print(f"Mapa do nível {level_num} não encontrado!")
            return
        
        tile_size = int(64 * data.ratio.x)
        
        player_spawned = False
        
        for y, row in enumerate(level_data['tiles']):
            for x, char in enumerate(row):
                if char == 'W':
                    platform_rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
                    self.platforms.append(platform_rect)
                    
                elif char == 'P' and not player_spawned:
                    spawn_x = x * tile_size
                    spawn_y = (y - 1) * tile_size
                    
                    self.player.position = pygame.Vector2(spawn_x, spawn_y)
                    self.player.hitbox.x = spawn_x
                    self.player.hitbox.y = spawn_y
                    self.player.rect.center = self.player.hitbox.center
                    
                    self.player.velocity = pygame.Vector2(0, 0)
                    self.player.acceleration = pygame.Vector2(0, 0)
                    self.player.on_ground = False
                    self.player.wall_left = False
                    self.player.wall_right = False
                    self.player.moving = False
                    self.player.current_state = 'idle'
                    
                    player_spawned = True
                    print(f"Player spawnado em: ({spawn_x}, {spawn_y})")
                    
                elif char == 'G':
                    enemy = Enemy(x * tile_size, (y - 1) * tile_size, 'guard')
                    self.enemies.append(enemy)
                    
                elif char == 'A':
                    enemy = Enemy(x * tile_size, (y - 1) * tile_size, 'archer')
                    self.enemies.append(enemy)
                    
                elif char == 'F':
                    self.goal = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
        
        self.level_tiles = self.generate_level_tiles(level_num)
        
        for enemy in self.enemies:
            if enemy.type == 'guard':
                for platform in self.platforms:
                    if (enemy.position.y + enemy.rect.height >= platform.top and 
                        enemy.position.y + enemy.rect.height <= platform.top + 10):
                        enemy.set_platform_bounds(platform.left, platform.right - enemy.rect.width)
                        break
        
        if not player_spawned:
            print("AVISO: Nenhum ponto de spawn 'P' encontrado no mapa! Usando posição padrão.")
            self.player.position = pygame.Vector2(100, 400)
        
        # Reconfigurar o background parallax para o novo nível
        self.setup_parallax_background()
    
    def load_level(self, level_num):
        if data.maps and 'levels' in data.maps:
            self.load_level_from_map(level_num)
        else:
            print("Nenhum mapa carregado!")
    
    def render(self, renderer:Renderer):
        # Renderizar background parallax
        if self.parallax_bg:
            self.parallax_bg.render(renderer)
        else:
            # Fallback: fundo colorido
            bg_key = f'level{data.current_level}'
            if data.current_level in [1, 2]:
                renderer.fill_screen((50, 120, 80))
            elif data.current_level in [3, 4]:
                renderer.fill_screen((80, 80, 120))
            else:
                renderer.fill_screen((100, 80, 60))
        
        # Renderizar tiles do nível
        for tile_row in self.level_tiles:
            for tile_data in tile_row:
                tile_sprite, tile_pos, tile_key, is_solid = tile_data
                if tile_sprite and is_solid:
                    screen_pos = self.camera.world_to_screen(pygame.Vector2(tile_pos[0], tile_pos[1]))
                    renderer.blit(tile_sprite, screen_pos)
        
        # Renderizar inimigos, projéteis, bandeira e player
        for enemy in self.enemies:
            enemy.render(renderer, self.camera)
        
        for projectile in self.projectiles:
            projectile.render(renderer, self.camera)
        
        if self.goal:
            if 'flag' in data.assets and data.assets['flag']:
                flag_frame = data.assets['flag'].get_current_frame()
                goal_pos = self.camera.world_to_screen(pygame.Vector2(self.goal.x, self.goal.y))
                flag_rect = pygame.Rect(goal_pos.x, goal_pos.y, self.goal.width, self.goal.height)
                renderer.blit(flag_frame, flag_rect)
            else:
                goal_pos = self.camera.world_to_screen(pygame.Vector2(self.goal.x, self.goal.y))
                renderer.draw_rect(goal_pos.x, goal_pos.y, self.goal.width, self.goal.height, (50, 200, 50))
            
            if DEBUG_MODE:
                goal_pos = self.camera.world_to_screen(pygame.Vector2(self.goal.x, self.goal.y))
                renderer.draw_rect(goal_pos.x, goal_pos.y, self.goal.width, self.goal.height, (0, 255, 0, 0.5))
        
        self.player.render(renderer, self.camera)
            
        if DEBUG_MODE:
            for platform in self.platforms:
                platform_pos = self.camera.world_to_screen(pygame.Vector2(platform.x, platform.y))
                renderer.draw_rect(platform_pos.x, platform_pos.y, platform.width, platform.height, (0, 0, 255, 0.5))
        
        # UI overlay
        renderer.draw_rect(0, 0, self.engine.width, 60*data.ratio.y, (0, 0, 0, 150))
    
    def update(self, dt):
        current_time = time.time() - self.start_time
        data.total_time = current_time
        
        time_str = f"{int(current_time//60)}:{int(current_time%60):02d}"
        self.time_display.set_text(f'Tempo: {time_str}')
        self.health_display.set_text(f'Vidas: {self.player.health}')
        
        self.player.update(dt, self.platforms, self.engine)
        
        # Verificar colisão do ataque do player com inimigos
        if self.player.is_attacking and self.player.attack_hitbox:
            for enemy in self.enemies[:]:
                if self.player.attack_hitbox.colliderect(enemy.rect):
                    if enemy.take_damage():
                        if enemy.health <= 0:
                            self.enemies.remove(enemy)
                        try:
                            self.audio_system.play_sound_effect('attack')
                        except:
                            pass
        
        for enemy in self.enemies:
            enemy.update(dt, self.player, self.platforms, self.projectiles)
        
        for projectile in self.projectiles[:]:
            projectile.update(dt)
            if not projectile.active:
                self.projectiles.remove(projectile)
            elif projectile.rect.colliderect(self.player.hitbox):
                if self.player.take_damage():
                    self.projectiles.remove(projectile)
        
        if 'flag' in data.assets and data.assets['flag'] and self.goal:
            data.assets['flag'].update()
        
        self.camera.update(dt)
        self.particle_system.update(dt, self.camera.position)
        
        if self.player.health <= 0:
            self.engine.set_scene("game_over")
            return
            
        if self.goal and self.player.hitbox.colliderect(self.goal):
            data.levels_completed.append(data.current_level)
            data.current_level += 1
            
            if data.current_level > 5:
                self.engine.set_scene("victory")
            else:
                self.load_level(data.current_level)
                self.level_display.set_text(f'Fase {data.current_level}/5')
                self.player.health = 3
                self.player.stamina = 100

def main():
    try:
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
        
    except Exception as e:
        print(f"Erro ao executar o jogo: {e}")
        import traceback
        traceback.print_exc()
    
if __name__ == "__main__":
    main()