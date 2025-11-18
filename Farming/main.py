from lunaengine.core import LunaEngine, Scene, Renderer
from lunaengine.ui import *
from lunaengine.graphics import SpriteSheet, Animation, Camera, CameraMode
import pygame, os, random, time, json

path_assets = os.path.abspath('./assets/')
path_font_jersey = os.path.join(path_assets, 'Jersey.ttf')
path_font_roboto = os.path.join(path_assets, 'RobotoMono.ttf')

class Data:
    player_name:str
    leaderboard:dict
    player_animations:dict
    assets:dict
    ratio:pygame.Vector2
    
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
                
    def load_assets(self):
        ss = SpriteSheet(os.path.join(path_assets, 'plants.png'))
        ps = SpriteSheet(os.path.join(path_assets, 'props.png'))
        self.assets = {}
        self.assets['plants'] = {
            'carrot': ss.get_sprites_at_regions([pygame.Rect(0,64,32,32), pygame.Rect(32,64,32,32), pygame.Rect(64,64,32,32)]),
            'wheat': ss.get_sprites_at_regions([pygame.Rect(0,32,32,32), pygame.Rect(32,32,32,32), pygame.Rect(64,32,32,32)]),
        }
        self.assets['bases'] = ss.get_sprites_at_regions([pygame.Rect(0,0,32,32), pygame.Rect(32,0,32,32), pygame.Rect(64,0,32,32)])
        self.assets['props'] = {
            'rocks': ps.get_sprites_at_regions([(0, 0, 32, 32), (32, 0, 32, 32), (64, 0, 32, 32)]),
            'trees': ps.get_sprites_at_regions([(0, 32, 32, 32), (32, 32, 32, 32), (64, 32, 32, 32)]),
        }
        
    def load_player_animations(self):
        f = os.path.join(path_assets, 'player.png')
        self.player_animations = {}
        self.player_animations['idle'] = Animation(spritesheet_file=str(f), size=(32, 32), start_pos=(0,0), frame_count=7, scale=(2*data.ratio.x, 2*data.ratio.y),  duration=0.8, loop=True)
        self.player_animations['walk_up'] = Animation(f, (32, 32), (0,32), 4, (0,0), (0,0), (2*data.ratio.x, 2*data.ratio.y), 0.4, True)
        self.player_animations['walk_side'] = Animation(f, (32, 32), (0,64), 4, (0,0), (0,0), (2*data.ratio.x, 2*data.ratio.y),  0.4, True)
        self.player_animations['walk_down'] = Animation(f, (32, 32), (0,96), 4, (0,0), (0,0), (2*data.ratio.x, 2*data.ratio.y),  0.4, True)
        
data = Data()

class MainMenu(Scene):
    def on_enter(self, previous_scene = None):
        self.engine.set_global_theme(ThemeType.BUILDER)
        self.engine._update_all_ui_themes(ThemeType.BUILDER)
        return super().on_enter(previous_scene)
    
    def on_exit(self, next_scene = None):
        return super().on_exit(next_scene)
    
    def __init__(self, engine):
        super().__init__(engine)
        
        self.setup_ui()
        
    def setup_ui(self):
        self.add_ui_element(TextLabel(self.engine.width//2, 120*data.ratio.y, 'Fazendinha', 126, (200, 170, 100), path_font_jersey, root_point=(0.5, 0)))
        
        self.play_button = Button(self.engine.width//2, 300*data.ratio.y,  250*data.ratio.x, 65*data.ratio.y, 'Jogar', 68, path_font_jersey, root_point=(0.5, 0))
        self.play_button.set_on_click(self.play)
        self.add_ui_element(self.play_button)
        
        self.exit_button = Button(self.engine.width//2, 375*data.ratio.y,  200*data.ratio.x, 50*data.ratio.y, 'Sair', 60, path_font_jersey, root_point=(0.5, 0))
        self.exit_button.set_on_click(self.quit)
        self.add_ui_element(self.exit_button)
        
    def update(self, dt):
        pass
        
    def play(self):
        self.engine.set_scene("game")
        
    def quit(self):
        self.engine.shutdown()
        exit()
        
    def render(self, renderer):
        renderer.draw_rect(0, 0, self.engine.width, self.engine.height, ThemeManager.get_color('background'))
        
class Player:
    rect:pygame.Rect
    animations:dict
    last_side:str
    current_tool:str
    current_state:str
    inventory:dict
    direction:pygame.Vector2 = pygame.Vector2(0,0)
    equipped_tool:int = 0
    tools:list = ['machado', 'picareta', 'foice', 'semear']
    def __init__(self):
        self.animations = data.player_animations
        self.current_state = 'idle'
        self.last_side = 'left'
        
        self.rect = pygame.Rect(0, 0, 64, 64)
        
    def update(self, dt):
        self.animations[self.current_state].update()
    
    def render(self, renderer:Renderer, engine:LunaEngine):
        frame = self.animations[self.current_state].get_current_frame()
        if self.last_side == 'left':
            frame = pygame.transform.flip(frame, True, False)
        
        r = pygame.Rect(engine.width//2, engine.height//2, *frame.get_size())
        renderer.blit(frame, r)
        
class GameScene(Scene):
    start_playing:float = None
    max_time_playing:float = 300 # In Seconds
    player:Player
    world_size:int = 1200
    def on_enter(self, previous_scene = None):
        self.start_playing = time.time()
        self.player = Player()
        self.setup_camera()
        self.setup_ui()
        
        self.trees = []
        self.rocks = []
        self.plant_boxes = []
        
        self.generate_world()
        return super().on_enter(previous_scene)
    
    def setup_camera(self):
        self.camera.set_target(self.player, CameraMode.FOLLOW)
    
    def setup_ui(self):
        self.clear_ui_elements()
        
        self.money_display = TextLabel((15*data.ratio.x), self.engine.height-(40*data.ratio.y), '$ 0', 30, (120, 200, 130), path_font_jersey, root_point=(0, 1.0))
        self.add_ui_element(self.money_display)
        
        self.tool_display = TextLabel((15*data.ratio.x), self.engine.height-(20*data.ratio.y), '(Machado)', 25, (160, 150, 90), path_font_jersey, root_point=(0, 1.0))
        self.add_ui_element(self.tool_display)
        
        self.add_ui_element(TextLabel(8*data.ratio.x, self.engine.height-(246*data.ratio.y), 'Controles', 24, (200, 140, 0), path_font_jersey, root_point=(0, 0)))
        self.add_ui_element(TextLabel(8*data.ratio.x, self.engine.height-(220*data.ratio.y), 'WASD - Movimento', 18, (200, 140, 0), path_font_jersey, root_point=(0, 0)))
        self.add_ui_element(TextLabel(8*data.ratio.x, self.engine.height-(200*data.ratio.y), '1 - Machado', 18, (200, 140, 0), path_font_jersey, root_point=(0, 0)))
        self.add_ui_element(TextLabel(8*data.ratio.x, self.engine.height-(180*data.ratio.y), '2 - Picareta', 18, (200, 140, 0), path_font_jersey, root_point=(0, 0)))
        self.add_ui_element(TextLabel(8*data.ratio.x, self.engine.height-(160*data.ratio.y), '3 - Foice', 18, (200, 140, 0), path_font_jersey, root_point=(0, 0)))
        self.add_ui_element(TextLabel(8*data.ratio.x, self.engine.height-(140*data.ratio.y), '4 - Semear', 18, (200, 140, 0), path_font_jersey, root_point=(0, 0)))
        self.add_ui_element(TextLabel(8*data.ratio.x, self.engine.height-(120*data.ratio.y), 'E/Q - Tipo de semente', 18, (200, 140, 0), path_font_jersey, root_point=(0, 0)))
    
    def on_exit(self, next_scene = None):
        return super().on_exit(next_scene)
    
    def __init__(self, engine):
        super().__init__(engine)

    def input_handle(self, dt):
        if self.start_playing == None:
            self.start_playing = time.time()
        if time.time() - self.start_playing > self.max_time_playing:
            pass
        
        keys = pygame.key.get_pressed()
        not_moved:bool = True
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.player.direction.y = -1
            self.player.current_state = 'walk_down'
            not_moved = False
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.player.direction.y = 1
            self.player.current_state = 'walk_up'
            not_moved = False
        else:
            self.player.direction.y = 0
        
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.player.direction.x = -1
            self.player.current_state = 'walk_side'
            self.player.last_side = 'left'
            not_moved = False
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.player.direction.x = 1
            self.player.current_state = 'walk_side'
            self.player.last_side = 'right'
            not_moved = False
        else:
            self.player.direction.x = 0
        
        if not_moved:
            self.player.current_state = 'idle'
            
        if keys[pygame.K_1]:
            self.player.equipped_tool = 0
            self.tool_display.set_text(f'({self.player.tools[self.player.equipped_tool].capitalize()})')
        elif keys[pygame.K_2]:
            self.player.equipped_tool = 1
            self.tool_display.set_text(f'({self.player.tools[self.player.equipped_tool].capitalize()})')
        elif keys[pygame.K_3]:
            self.player.equipped_tool = 2
            self.tool_display.set_text(f'({self.player.tools[self.player.equipped_tool].capitalize()})')
        elif keys[pygame.K_4]:
            self.player.equipped_tool = 3
            self.tool_display.set_text(f'({self.player.tools[self.player.equipped_tool].capitalize()})')
        
        if self.player.direction.x != 0 or self.player.direction.y != 0:
            self.player.direction = self.player.direction.normalize()
            
            self.player.rect.x += self.player.direction.x * (200*data.ratio.x) * dt
            self.player.rect.y += self.player.direction.y * (200*data.ratio.y) * dt
        
        
        
    def update(self, dt):
        self.input_handle(dt)
        
        self.player.update(dt)
        
        self.camera.update(dt)
    
    def generate_world(self):
        # Generate plant box
        for y in range(1,6):
            for x in range(1,6):
                self.plant_boxes.append({
                    'rect':pygame.Rect(128+(x * (64 * data.ratio.x)), 128+(y * (64 * data.ratio.y)), (64 * data.ratio.x), (64 * data.ratio.y)),
                    'base':pygame.transform.scale(random.choice(data.assets['bases']), (64 * data.ratio.x, 64 * data.ratio.y)),
                    'plant':None
                })
                
        for _ in range(8):
            x, y = random.randint(0, self.world_size), random.randint(0, self.world_size)
            self.trees.append({
                'rect':pygame.Rect(x, y, 64*data.ratio.x, 64*data.ratio.y),
                'sprite':pygame.transform.scale(random.choice(data.assets['props']['trees']), (int(64 * data.ratio.x), int(64 * data.ratio.y)))
            })
        
        for _ in range(8):
            x, y = random.randint(0, self.world_size), random.randint(0, self.world_size)
            self.rocks.append({
                'rect':pygame.Rect(x, y, 64*data.ratio.x, 64*data.ratio.y),
                'sprite':pygame.transform.scale(random.choice(data.assets['props']['rocks']), (int(64 * data.ratio.x), int(64 * data.ratio.y)))
            })
    
    def render_world(self, renderer):
        for plant_box in self.plant_boxes:
            renderer.blit(plant_box['base'], self.camera.world_to_screen(plant_box['rect'].topleft))
            if plant_box['plant'] != None:
                pass
        
        for tree in self.trees:
            renderer.blit(tree['sprite'], self.camera.world_to_screen(tree['rect'].topleft))
            
        for rock in self.rocks:
            renderer.blit(rock['sprite'], self.camera.world_to_screen(rock['rect'].topleft))
            
    
    def render(self, renderer):
        renderer.fill_screen((180, 180, 255))
        
        self.render_world(renderer)
        
        renderer.draw_rect((5*data.ratio.x), self.engine.height-(70*data.ratio.y), self.engine.width-(10*data.ratio.x), (65*data.ratio.y), ThemeManager.get_color('background'))
        renderer.draw_rect((5*data.ratio.x), self.engine.height-(250*data.ratio.y), (165*data.ratio.x), (175*data.ratio.y), ThemeManager.get_color('background'))
        
        self.player.render(renderer, self.engine)

def main():
    engine = LunaEngine("Farming", 1280, 720, True)
    engine.initialize()
    
    data.ratio = pygame.Vector2(engine.width / 1280, engine.height / 720)
    
    engine.add_scene("main", MainMenu)
    engine.add_scene("game", GameScene)
    
    engine.set_scene("main")
    
    data.load_assets()
    data.load_player_animations()
    
    engine.run()
    
if __name__ == "__main__":
    main()