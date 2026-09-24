# main.py – Updated for LunaEngine 0.2.5
from lunaengine.core import LunaEngine, Scene, Renderer
from lunaengine.ui import *
from lunaengine.graphics import SpriteSheet, Animation, Camera, CameraMode, ParticleConfig
import pygame, os, random, time, json, sys
from pygame import Rect

path_assets = os.path.dirname(__file__) + '/assets/'
path_font_jersey = os.path.join(path_assets, 'Jersey.ttf')
path_font_roboto = os.path.join(path_assets, 'RobotoMono.ttf')

class Data:
    player_name: str
    leaderboard: dict
    player_animations: dict
    assets: dict
    ratio: pygame.Vector2
    score: int = 0

    def __init__(self):
        if not os.path.exists(f'{os.path.dirname(__file__)}/leaderboard.json'):
            self.leaderboard = {"scores": []}
            with open(f'{os.path.dirname(__file__)}/leaderboard.json', 'w') as f:
                json.dump(self.leaderboard, f)
        else:
            with open(f'{os.path.dirname(__file__)}/leaderboard.json', 'r') as f:
                self.leaderboard = json.load(f)

    def add_score(self, player_name, score):
        self.leaderboard["scores"].append({
            "name": player_name,
            "score": score,
            "date": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        self.leaderboard["scores"].sort(key=lambda x: x["score"], reverse=True)
        self.leaderboard["scores"] = self.leaderboard["scores"][:10]
        with open(f'{os.path.dirname(__file__)}/leaderboard.json', 'w') as f:
            json.dump(self.leaderboard, f)

    def get_score_index(self, player_name):
        for i, s in enumerate(self.leaderboard["scores"]):
            if s["name"] == player_name:
                return i
        return -1

    def register_custom_particles(self, scene: Scene):
        scene.particle_system.register_custom_particle(
            'tree_destroy', ParticleConfig(
                color_start=(180, 230, 180),
                color_end=(160, 215, 160),
                size_start=5.0,
                size_end=2.5,
                lifetime=0.75
            )
        )
        scene.particle_system.register_custom_particle(
            'rock_destroy', ParticleConfig(
                color_start=(120, 120, 120),
                color_end=(90, 90, 90),
                size_start=5.0,
                size_end=2.5,
                lifetime=0.75
            )
        )

    def load_assets(self):
        ss = SpriteSheet(os.path.join(path_assets, 'plants.png'))
        ps = SpriteSheet(os.path.join(path_assets, 'props.png'))
        bs = SpriteSheet(os.path.join(path_assets, 'builds.png'))
        self.assets = {}
        self.assets['plants'] = {
            'carrot': ss.get_sprites_at_regions([pygame.Rect(0, 64, 32, 32), pygame.Rect(32, 64, 32, 32), pygame.Rect(64, 64, 32, 32)]),
            'wheat': ss.get_sprites_at_regions([pygame.Rect(0, 32, 32, 32), pygame.Rect(32, 32, 32, 32), pygame.Rect(64, 32, 32, 32)]),
        }
        self.assets['bases'] = ss.get_sprites_at_regions([pygame.Rect(0, 0, 32, 32), pygame.Rect(32, 0, 32, 32), pygame.Rect(64, 0, 32, 32)])
        self.assets['props'] = {
            'rocks': ps.get_sprites_at_regions([(0, 0, 32, 32), (32, 0, 32, 32), (64, 0, 32, 32)]),
            'trees': ps.get_sprites_at_regions([(0, 32, 32, 32), (32, 32, 32, 32), (64, 32, 32, 32)]),
        }
        self.assets['builds'] = {
            'seed': bs.get_sprite_at_rect((0, 0, 64, 64)),
            'sell': bs.get_sprite_at_rect((64, 0, 64, 64))
        }

    def load_player_animations(self):
        f = os.path.join(path_assets, 'player.png')
        self.player_animations = {}
        self.player_animations['idle'] = Animation(
            spritesheet_file=f, size=(32, 32), start_pos=(0, 0),
            frame_count=7, scale=(2 * data.ratio.x, 2 * data.ratio.y),
            duration=0.8, loop=True
        )
        self.player_animations['walk_up'] = Animation(
            f, (32, 32), (0, 32), 4, (0, 0), (0, 0),
            (2 * data.ratio.x, 2 * data.ratio.y), 0.4, True
        )
        self.player_animations['walk_side'] = Animation(
            f, (32, 32), (0, 64), 4, (0, 0), (0, 0),
            (2 * data.ratio.x, 2 * data.ratio.y), 0.4, True
        )
        self.player_animations['walk_down'] = Animation(
            f, (32, 32), (0, 96), 4, (0, 0), (0, 0),
            (2 * data.ratio.x, 2 * data.ratio.y), 0.4, True
        )

data = Data()


# ----------------------------------------------------------------------
# GameOverScene
# ----------------------------------------------------------------------
class GameOverScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.final_score = 0
        self.player_position = 0

        # Create UI elements (they are hidden initially)
        self.title_label = TextLabel(
            self.engine.width // 2, 100 * data.ratio.y,
            'Tempo Esgotado!', 72, (200, 100, 100),
            path_font_jersey, pivot=(0.5, 0)
        )
        self.add_ui_element(self.title_label)

        self.score_label = TextLabel(
            self.engine.width // 2, 200 * data.ratio.y,
            f'Final Score: ${data.score}', 48, (200, 170, 100),
            path_font_jersey, pivot=(0.5, 0)
        )
        self.add_ui_element(self.score_label)

        self.position_label = TextLabel(
            self.engine.width // 2, 260 * data.ratio.y,
            'Rank Position: #0', 36, (200, 170, 100),
            path_font_jersey, pivot=(0.5, 0)
        )
        self.add_ui_element(self.position_label)

        self.menu_button = Button(
            self.engine.width // 2, 350 * data.ratio.y,
            280 * data.ratio.x, 65 * data.ratio.y,
            'Return to Menu', 48, path_font_jersey, pivot=(0.5, 0)
        )
        self.menu_button.set_on_click(self.back_to_menu)
        self.add_ui_element(self.menu_button)

    def on_enter(self, previous_scene_name=None):
        self.engine.set_global_theme(ThemeType.BUILDER)
        # Update dynamic texts
        data.add_score(data.player_name, data.score)
        pos = data.get_score_index(data.player_name) + 1
        self.position_label.set_text(f'Rank Position: #{pos}')
        self.score_label.set_text(f'Final Score: ${data.score}')

    def back_to_menu(self):
        self.engine.set_scene("main")

    def update(self, dt):
        pass  # No manual camera/particle updates needed

    def render(self, renderer):
        renderer.draw_rect(0, 0, self.engine.width, self.engine.height, ThemeManager.get_color('background'))


# ----------------------------------------------------------------------
# MainMenu
# ----------------------------------------------------------------------
class MainMenu(Scene):
    def __init__(self, engine):
        super().__init__(engine)

        self.title_label = TextLabel(
            self.engine.width // 2, 30 * data.ratio.y,
            'Farming', 126, (200, 170, 100),
            path_font_jersey, pivot=(0.5, 0)
        )
        self.add_ui_element(self.title_label)

        self.play_button = Button(
            self.engine.width // 2, 150 * data.ratio.y,
            250 * data.ratio.x, 65 * data.ratio.y,
            'Play', 68, path_font_jersey, pivot=(0.5, 0)
        )
        self.play_button.set_on_click(self.play)
        self.add_ui_element(self.play_button)

        self.exit_button = Button(
            self.engine.width // 2, 220 * data.ratio.y,
            200 * data.ratio.x, 50 * data.ratio.y,
            'Quit', 60, path_font_jersey, pivot=(0.5, 0)
        )
        self.exit_button.set_on_click(self.quit)
        self.add_ui_element(self.exit_button)

        self.name_hint = TextLabel(
            self.engine.width // 2, 275 * data.ratio.y,
            'Name:', 26, (200, 170, 100),
            path_font_jersey, pivot=(0.5, 0)
        )
        self.add_ui_element(self.name_hint)

        self.name_textbox = TextBox(
            self.engine.width // 2, 300 * data.ratio.y,
            200 * data.ratio.x, 28 * data.ratio.y,
            '', 26, path_font_jersey, pivot=(0.5, 0)
        )
        self.add_ui_element(self.name_textbox)

        self.name_warning = TextLabel(
            self.engine.width // 2, 330 * data.ratio.y,
            '* This name are going to be used in leaderboard', 16,
            (200, 100, 100), path_font_jersey, pivot=(0.5, 0)
        )
        self.add_ui_element(self.name_warning)

        self.leaderboard_label = TextLabel(
            self.engine.width // 2, 370 * data.ratio.y,
            'Leaderboard', 42, (200, 170, 100),
            path_font_jersey, pivot=(0.5, 0)
        )
        self.add_ui_element(self.leaderboard_label)

        self.leaderboard_frame = ScrollingFrame(
            self.engine.width // 2, int(430 * data.ratio.y),
            int(400 * data.ratio.x), int(200 * data.ratio.y),
            380 * data.ratio.x, 400 * data.ratio.y, pivot=(0.5, 0)
        )
        self.add_ui_element(self.leaderboard_frame)

    def on_enter(self, previous_scene_name=None):
        self.engine.set_global_theme(ThemeType.BUILDER)
        self.update_leaderboard()

    def update_leaderboard(self):
        self.leaderboard_frame.clear_children()
        if not data.leaderboard["scores"]:
            no_scores = TextLabel(
                190 * data.ratio.x, 20 * data.ratio.y,
                'No scores!', 24,
                (150, 150, 150), path_font_jersey, pivot=(0.5, 0)
            )
            self.leaderboard_frame.add_child(no_scores)
            return
        for i, score_data in enumerate(data.leaderboard["scores"]):
            y_pos = 20 + (i * 35)
            rank_text = f"#{i+1} {score_data['name']} - ${score_data['score']}"
            score_label = TextLabel(
                10 * data.ratio.x, y_pos * data.ratio.y,
                rank_text, 20, (200, 170, 100),
                path_font_jersey, pivot=(0, 0)
            )
            self.leaderboard_frame.add_child(score_label)

    def play(self):
        if self.name_textbox.text == '':
            return
        data.player_name = self.name_textbox.text
        self.engine.set_scene("game")

    def quit(self):
        self.engine.shutdown()

    def update(self, dt):
        pass

    def render(self, renderer):
        renderer.draw_rect(0, 0, self.engine.width, self.engine.height, ThemeManager.get_color('background'))


# ----------------------------------------------------------------------
# Player (game logic)
# ----------------------------------------------------------------------
class Player:
    rect: pygame.Rect
    animations: dict
    last_side: str
    current_tool: str
    current_state: str
    inventory: dict
    direction: pygame.Vector2 = pygame.Vector2(0, 0)
    equipped_tool: int = 0
    tools: list = ['axe', 'pickaxe', 'scythe', 'sow']
    seeds: list = ['wheat', 'carrot']
    current_seed: int = 0
    left_click_cooldown: float

    def __init__(self):
        self.animations = data.player_animations
        self.current_state = 'idle'
        self.last_side = 'left'

        self.inventory = {
            'wheat_seeds': 0,
            'carrot_seeds': 0,
            'money': 0,
            'wheat': 0,
            'carrot': 0,
            'wood': 0,
            'stone': 0
        }
        self.current_seed = 0
        self.rect = pygame.Rect(0, 0, 64, 64)

        self.left_click_cooldown = time.time()

    def update(self, dt):
        self.animations[self.current_state].update()

    def render(self, renderer: Renderer, engine: LunaEngine, camera: Camera):
        frame = self.animations[self.current_state].get_current_frame()
        if self.last_side == 'left':
            frame = pygame.transform.flip(frame, True, False)
        renderer.blit(frame, camera.world_to_screen(self.rect.topleft))


# ----------------------------------------------------------------------
# GameScene
# ----------------------------------------------------------------------
class ShopItem:
    def __init__(self, name, price, quantity=1):
        self.name = name
        self.price = price
        self.quantity = quantity


class GameScene(Scene):
    start_playing: float = None
    max_time_playing: float = 180
    player: Player
    world_size: int = 1200

    def __init__(self, engine):
        super().__init__(engine)

        # Load audio
        self.audio_manager.load_sound('music', f'{path_assets}/music.mp3', category='music')
        self.audio_manager.load_sound('tree_hit', f'{path_assets}/hit-tree.wav')
        self.audio_manager.load_sound('rock_hit', f'{path_assets}/hit-rock.wav')

        # UI elements – created once here
        self.money_display = TextLabel(
            15 * data.ratio.x, self.engine.height - (40 * data.ratio.y),
            '$ 0', 30, (120, 200, 130), path_font_jersey, pivot=(0, 1.0)
        )
        self.add_ui_element(self.money_display)

        self.tool_display = TextLabel(
            15 * data.ratio.x, self.engine.height - (20 * data.ratio.y),
            '(Axe)', 25, (160, 150, 90), path_font_jersey, pivot=(0, 1.0)
        )
        self.add_ui_element(self.tool_display)

        # Controls info
        controls = [
            ('Controls', 24, (200, 140, 0)),
            ('WASD - Movment', 18, (200, 140, 0)),
            ('1 - Axe', 18, (200, 140, 0)),
            ('2 - Pickaxe', 18, (200, 140, 0)),
            ('3 - Scythe', 18, (200, 140, 0)),
            ('4 - Sow', 18, (200, 140, 0)),
            ('E/Q - Seed Type', 18, (200, 140, 0)),
            ('F - Interact', 18, (200, 140, 0)),
        ]
        for i, (text, size, color) in enumerate(controls):
            y = self.engine.height - (246 - i * 20) * data.ratio.y
            lbl = TextLabel(8 * data.ratio.x, y, text, size, color, path_font_jersey, pivot=(0, 0))
            self.add_ui_element(lbl)

        self.seed_display = TextLabel(
            130 * data.ratio.x, self.engine.height - (25 * data.ratio.y),
            'Wheat(?x), Carrot(?x)', int(20 * data.ratio.y),
            (200, 170, 100), path_font_jersey, pivot=(0, 1.0)
        )
        self.add_ui_element(self.seed_display)

        self.inventory_display = TextLabel(
            self.engine.width // 2, self.engine.height - (25 * data.ratio.y),
            'Inventory: Wheat(0) Carrot(0) Wood(0) Rock(0)',
            20, (200, 170, 100), path_font_jersey, pivot=(0.5, 1.0)
        )
        self.add_ui_element(self.inventory_display)

        self.time_display = TextLabel(
            self.engine.width // 2, 30 * data.ratio.y,
            's', 20, (230, 200, 130), path_font_jersey, pivot=(0.5, 0)
        )
        self.add_ui_element(self.time_display)

        # ---- Sell shop UI ----
        self.sell_shop_items = [
            ShopItem("Wheat", 20),
            ShopItem("Carrot", 25),
            ShopItem("Wood", 5),
            ShopItem("Rock", 8)
        ]
        self.sell_market_ui = []
        self.sell_market_open = False

        self.sell_title = TextLabel(
            self.engine.width // 2, 150 * data.ratio.y,
            'Sell Items', 36, (160, 200, 180),
            path_font_jersey, pivot=(0.5, 0)
        )
        self.sell_title.visible = False
        self.sell_market_ui.append(self.sell_title)
        self.add_ui_element(self.sell_title)

        self.sell_dropdown = Dropdown(
            self.engine.width // 2, 200 * data.ratio.y,
            300 * data.ratio.x, 40 * data.ratio.y,
            ["Wheat - $20", "Carrot - $25", "Wood - $5", "Rock - $8"],
            24, path_font_jersey, (0.5, 0)
        )
        self.sell_dropdown.visible = False
        self.sell_market_ui.append(self.sell_dropdown)
        self.add_ui_element(self.sell_dropdown)

        self.sellValueDisplay = TextLabel(
            self.engine.width // 2, 250 * data.ratio.y,
            '0', 32, (40, 35, 0), path_font_jersey, pivot=(0.5, 0)
        )
        self.sellValueDisplay.visible = False
        self.sell_market_ui.append(self.sellValueDisplay)
        self.add_ui_element(self.sellValueDisplay)
        self.sell_dropdown.set_on_selection_changed(self.sell_dropdown_changed)

        self.sell_button = Button(
            self.engine.width // 2, 280 * data.ratio.y,
            200 * data.ratio.x, 50 * data.ratio.y,
            'Sell', 30, path_font_jersey, pivot=(0.5, 0)
        )
        self.sell_button.set_on_click(self.sell_selected)
        self.sell_button.visible = False
        self.sell_market_ui.append(self.sell_button)
        self.add_ui_element(self.sell_button)

        self.sell_all_button = Button(
            self.engine.width // 2, 340 * data.ratio.y,
            200 * data.ratio.x, 50 * data.ratio.y,
            'Sell All', 30, path_font_jersey, pivot=(0.5, 0)
        )
        self.sell_all_button.set_on_click(self.sell_all)
        self.sell_all_button.visible = False
        self.sell_market_ui.append(self.sell_all_button)
        self.add_ui_element(self.sell_all_button)

        self.sell_close_button = Button(
            120 * data.ratio.x, 100 * data.ratio.y,
            100 * data.ratio.x, 40 * data.ratio.y,
            'Close (ESC)', 20, path_font_jersey, pivot=(0, 0)
        )
        self.sell_close_button.set_on_click(self.close_sell_shop)
        self.sell_close_button.visible = False
        self.sell_market_ui.append(self.sell_close_button)
        self.add_ui_element(self.sell_close_button)

        self.sell_money_label = TextLabel(
            self.engine.width // 2, 120 * data.ratio.y,
            f"Money: $0", 24, (200, 200, 100),
            path_font_jersey, pivot=(0.5, 0)
        )
        self.sell_money_label.visible = False
        self.sell_market_ui.append(self.sell_money_label)
        self.add_ui_element(self.sell_money_label)

        # ---- Seed shop UI ----
        self.seed_shop_items = [
            ShopItem("Wheat Seeds", 10),
            ShopItem("Carrot Seeds", 15)
        ]
        self.seed_market_ui = []
        self.seed_market_open = False

        self.seed_title = TextLabel(
            self.engine.width // 2, 150 * data.ratio.y,
            'Seed Shop', 36, (160, 200, 180),
            path_font_jersey, pivot=(0.5, 0)
        )
        self.seed_title.visible = False
        self.seed_market_ui.append(self.seed_title)
        self.add_ui_element(self.seed_title)

        self.seed_dropdown = Dropdown(
            self.engine.width // 2, 200 * data.ratio.y,
            300 * data.ratio.x, 40 * data.ratio.y,
            ["Wheat Seeds - $10", "Carrot Seeds - $15"],
            24, path_font_jersey, (0.5, 0)
        )
        self.seed_dropdown.visible = False
        self.seed_market_ui.append(self.seed_dropdown)
        self.add_ui_element(self.seed_dropdown)

        self.seedValueDisplay = TextLabel(
            self.engine.width // 2, 250 * data.ratio.y,
            '$0', 32, (40, 35, 0), path_font_jersey, pivot=(0.5, 0)
        )
        self.seedValueDisplay.visible = False
        self.seed_market_ui.append(self.seedValueDisplay)
        self.add_ui_element(self.seedValueDisplay)
        self.seed_dropdown.set_on_selection_changed(self.seed_dropdown_changed)

        self.buy_button = Button(
            self.engine.width // 2, 280 * data.ratio.y,
            200 * data.ratio.x, 50 * data.ratio.y,
            'Buy', 30, path_font_jersey, pivot=(0.5, 0)
        )
        self.buy_button.set_on_click(self.purchase_seed_item)
        self.buy_button.visible = False
        self.seed_market_ui.append(self.buy_button)
        self.add_ui_element(self.buy_button)

        self.buy_all_button = Button(
            self.engine.width // 2, 340 * data.ratio.y,
            200 * data.ratio.x, 50 * data.ratio.y,
            'Buy all', 30, path_font_jersey, pivot=(0.5, 0)
        )
        self.buy_all_button.set_on_click(self.purchase_all_seed_item)
        self.buy_all_button.visible = False
        self.seed_market_ui.append(self.buy_all_button)
        self.add_ui_element(self.buy_all_button)

        self.seed_close_button = Button(
            120 * data.ratio.x, 100 * data.ratio.y,
            100 * data.ratio.x, 40 * data.ratio.y,
            'Close (ESC)', 20, path_font_jersey, pivot=(0, 0)
        )
        self.seed_close_button.set_on_click(self.close_seed_shop)
        self.seed_close_button.visible = False
        self.seed_market_ui.append(self.seed_close_button)
        self.add_ui_element(self.seed_close_button)

        self.seed_money_label = TextLabel(
            self.engine.width // 2, 120 * data.ratio.y,
            f"Money: $0", 24, (200, 200, 100),
            path_font_jersey, pivot=(0.5, 0)
        )
        self.seed_money_label.visible = False
        self.seed_market_ui.append(self.seed_money_label)
        self.add_ui_element(self.seed_money_label)

    # ------------------------------------------------------------------
    # Scene lifecycle
    # ------------------------------------------------------------------
    def on_enter(self, previous_scene_name=None):
        self.audio_manager.play_music('music', 0.7, 1.0, True)

        self.start_playing = time.time()
        self.player = Player()
        self.camera.set_target(self.player)   # new camera API

        self.trees = []
        self.rocks = []
        self.plant_boxes = []
        self.sell_market = None
        self.seed_market = None

        self.sell_market_open = False
        self.seed_market_open = False

        data.register_custom_particles(self)
        self.generate_world()

        # Hide shop overlays
        for ui in self.sell_market_ui:
            ui.visible = False
        for ui in self.seed_market_ui:
            ui.visible = False

        # Reset visible UI
        for ui in self.ui_elements:
            if ui not in self.sell_market_ui and ui not in self.seed_market_ui:
                ui.visible = True

        # Update initial tool display
        self.tool_display.set_text(f'({self.player.tools[self.player.equipped_tool].capitalize()})')

    def on_exit(self, next_scene_name=None):
        self.audio_manager.stop_all()

    # ------------------------------------------------------------------
    # Shop helper callbacks
    # ------------------------------------------------------------------
    def sell_dropdown_changed(self, index, value):
        self.sellValueDisplay.set_text(f"{self.sell_shop_items[index].name} - ${self.sell_shop_items[index].price}")

    def seed_dropdown_changed(self, index, value):
        self.seedValueDisplay.set_text(f"{self.seed_shop_items[index].name} - ${self.seed_shop_items[index].price}")

    # ------------------------------------------------------------------
    # Input handling
    # ------------------------------------------------------------------
    def input_handle(self, dt):
        if self.start_playing is None:
            self.start_playing = time.time()
        remaining_time = self.max_time_playing - (time.time() - self.start_playing)
        if remaining_time <= 0:
            data.score = self.player.inventory.get('money', 0)
            self.engine.set_scene("game_over")
            return

        keys = pygame.key.get_pressed()

        # Close shops with ESC
        if self.sell_market_open and keys[pygame.K_ESCAPE]:
            self.close_sell_shop()
        if self.seed_market_open and keys[pygame.K_ESCAPE]:
            self.close_seed_shop()

        # Player movement
        not_moved = True
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

        # Tool selection
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

        if self.player.equipped_tool == 3 and keys[pygame.K_q]:
            self.player.current_seed = 0
        elif self.player.equipped_tool == 3 and keys[pygame.K_e]:
            self.player.current_seed = 1

        if self.engine.input_state.mouse_buttons_pressed.left and time.time() - self.player.left_click_cooldown > 0.2:
            self.player.left_click_cooldown = time.time()
            self.player_interact()

        if keys[pygame.K_f]:
            self.interact_shop()

        # Apply movement
        if self.player.direction.x != 0 or self.player.direction.y != 0:
            self.player.direction = self.player.direction.normalize()
            self.player.rect.x += self.player.direction.x * (200 * data.ratio.x) * dt
            self.player.rect.y += self.player.direction.y * (200 * data.ratio.y) * dt

    # ------------------------------------------------------------------
    # Interactions
    # ------------------------------------------------------------------
    def player_interact(self):
        m_pos = self.engine.input_state.mouse_pos
        m_pos = self.camera.screen_to_world(m_pos)
        player_range = pygame.Rect(0, 0, 96 * data.ratio.x, 96 * data.ratio.y)
        player_range.center = self.player.rect.center

        if self.player.equipped_tool == 0:  # axe
            for tree in self.trees:
                if tree['rect'].collidepoint(m_pos) and tree['rect'].colliderect(player_range):
                    if tree['health'] > 0:
                        self.audio_manager.play('tree_hit')
                        self.particle_system.emit(tree['rect'].centerx, tree['rect'].centery, 'tree_destroy', 50, spread=30.0)
                        tree['health'] -= 1
                        if tree['health'] == 0:
                            self.player.inventory['wood'] = self.player.inventory.get('wood', 0) + 2
                            self.trees.remove(tree)
                            break
        elif self.player.equipped_tool == 1:  # pickaxe
            for rock in self.rocks:
                if rock['rect'].collidepoint(m_pos) and rock['rect'].colliderect(player_range):
                    if rock['health'] > 0:
                        self.audio_manager.play('rock_hit')
                        self.particle_system.emit(rock['rect'].centerx, rock['rect'].centery, 'rock_destroy', 50, spread=30.0)
                        rock['health'] -= 1
                        if rock['health'] == 0:
                            self.player.inventory['stone'] = self.player.inventory.get('stone', 0) + 2
                            self.rocks.remove(rock)
                            break
        elif self.player.equipped_tool == 2:  # sickle
            for plant_box in self.plant_boxes:
                if plant_box['rect'].collidepoint(m_pos) and plant_box['rect'].colliderect(player_range):
                    if plant_box['plant'] is not None and plant_box['plant']['state'] == 2:
                        plant_type = 'wheat' if plant_box['plant']['sprites'] == data.assets['plants']['wheat'] else 'carrot'
                        self.player.inventory[plant_type] = self.player.inventory.get(plant_type, 0) + 1
                        plant_box['plant'] = None
        elif self.player.equipped_tool == 3:  # seed
            for plant_box in self.plant_boxes:
                if plant_box['rect'].collidepoint(m_pos) and plant_box['rect'].colliderect(player_range):
                    if plant_box['plant'] is None:
                        p = ''
                        if self.player.current_seed == 0:
                            p = 'wheat_seeds'
                        elif self.player.current_seed == 1:
                            p = 'carrot_seeds'
                        if p != '' and self.player.inventory.get(p, 0) > 0:
                            plant_box['plant'] = {
                                'sprites': data.assets['plants']['wheat' if p == 'wheat_seeds' else 'carrot'],
                                'state': 0,
                                'growth_timer': time.time()
                            }
                            self.player.inventory[p] -= 1

    def interact_shop(self):
        m_pos = self.engine.input_state.mouse_pos
        m_pos = self.camera.screen_to_world(m_pos)
        player_range = pygame.Rect(0, 0, 96 * data.ratio.x, 96 * data.ratio.y)
        player_range.center = self.player.rect.center

        if self.sell_market['rect'].collidepoint(m_pos) and self.sell_market['rect'].colliderect(player_range):
            if self.sell_market_open:
                self.close_sell_shop()
            else:
                self.open_sell_shop()
        elif self.seed_market['rect'].collidepoint(m_pos) and self.seed_market['rect'].colliderect(player_range):
            if self.seed_market_open:
                self.close_seed_shop()
            else:
                self.open_seed_shop()

    # ------------------------------------------------------------------
    # Shop open/close
    # ------------------------------------------------------------------
    def open_sell_shop(self):
        self.sell_market_open = True
        for ui in self.ui_elements:
            if ui not in self.sell_market_ui:
                ui.visible = False
        for ui in self.sell_market_ui:
            ui.visible = True
        self.sell_money_label.set_text(f"Money: ${self.player.inventory.get('money', 0)}")

    def close_sell_shop(self):
        self.sell_market_open = False
        for ui in self.ui_elements:
            ui.visible = True
        for ui in self.sell_market_ui:
            ui.visible = False
        for ui in self.seed_market_ui:
            ui.visible = False

    def open_seed_shop(self):
        self.seed_market_open = True
        for ui in self.ui_elements:
            if ui not in self.seed_market_ui:
                ui.visible = False
        for ui in self.seed_market_ui:
            ui.visible = True
        self.seed_money_label.set_text(f"Money: ${self.player.inventory.get('money', 0)}")

    def close_seed_shop(self):
        self.seed_market_open = False
        for ui in self.ui_elements:
            ui.visible = True
        for ui in self.sell_market_ui:
            ui.visible = False
        for ui in self.seed_market_ui:
            ui.visible = False

    # ------------------------------------------------------------------
    # Shop actions
    # ------------------------------------------------------------------
    def purchase_seed_item(self):
        idx = self.seed_dropdown.selected_index
        if idx is None:
            return
        item = self.seed_shop_items[idx]
        money = self.player.inventory.get('money', 0)
        if money >= item.price:
            self.player.inventory['money'] = money - item.price
            if item.name == "Wheat Seeds":
                self.player.inventory['wheat_seeds'] = self.player.inventory.get('wheat_seeds', 0) + 1
            elif item.name == "Carrot Seeds":
                self.player.inventory['carrot_seeds'] = self.player.inventory.get('carrot_seeds', 0) + 1
            self.seed_money_label.set_text(f"Money: ${self.player.inventory.get('money', 0)}")

    def purchase_all_seed_item(self):
        idx = self.seed_dropdown.selected_index
        if idx is None:
            return
        item = self.seed_shop_items[idx]
        money = self.player.inventory.get('money', 0)
        amount = money // item.price
        if amount > 0:
            self.player.inventory['money'] = money - (amount * item.price)
            if item.name == "Wheat Seeds":
                self.player.inventory['wheat_seeds'] = self.player.inventory.get('wheat_seeds', 0) + amount
            elif item.name == "Carrot Seeds":
                self.player.inventory['carrot_seeds'] = self.player.inventory.get('carrot_seeds', 0) + amount
            self.seed_money_label.set_text(f"Money: ${self.player.inventory.get('money', 0)}")

    def sell_selected(self):
        idx = self.sell_dropdown.selected_index
        if idx is None:
            return
        item = self.sell_shop_items[idx]
        resource_map = {
            "Wheat": "wheat",
            "Carrot": "carrot",
            "Wood": "wood",
            "Rock": "stone"
        }
        if item.name in resource_map:
            res = resource_map[item.name]
            qty = self.player.inventory.get(res, 0)
            if qty > 0:
                self.player.inventory[res] = qty - 1
                self.player.inventory['money'] = self.player.inventory.get('money', 0) + item.price
                self.sell_money_label.set_text(f"Money: ${self.player.inventory.get('money', 0)}")

    def sell_all(self):
        idx = self.sell_dropdown.selected_index
        if idx is None:
            return
        item = self.sell_shop_items[idx]
        resource_map = {
            "Wheat": "wheat",
            "Carrot": "carrot",
            "Wood": "wood",
            "Rock": "stone"
        }
        if item.name in resource_map:
            res = resource_map[item.name]
            qty = self.player.inventory.get(res, 0)
            if qty > 0:
                self.player.inventory[res] = 0
                self.player.inventory['money'] = self.player.inventory.get('money', 0) + (qty * item.price)
                self.sell_money_label.set_text(f"Money: ${self.player.inventory.get('money', 0)}")

    # ------------------------------------------------------------------
    # World generation
    # ------------------------------------------------------------------
    def generate_world(self):
        for y in range(1, 6):
            for x in range(1, 6):
                self.plant_boxes.append({
                    'rect': pygame.Rect(
                        128 + (x * (64 * data.ratio.x)),
                        128 + (y * (64 * data.ratio.y)),
                        64 * data.ratio.x, 64 * data.ratio.y
                    ),
                    'base': pygame.transform.scale(
                        random.choice(data.assets['bases']),
                        (64 * data.ratio.x, 64 * data.ratio.y)
                    ),
                    'plant': None,
                    'health': 0
                })

        for _ in range(8):
            x, y = random.randint(0, self.world_size), random.randint(0, self.world_size)
            self.trees.append({
                'rect': pygame.Rect(x, y, 64 * data.ratio.x, 64 * data.ratio.y),
                'sprite': pygame.transform.scale(
                    random.choice(data.assets['props']['trees']),
                    (int(64 * data.ratio.x), int(64 * data.ratio.y))
                ),
                'health': 2
            })

        for _ in range(8):
            x, y = random.randint(0, self.world_size), random.randint(0, self.world_size)
            self.rocks.append({
                'rect': pygame.Rect(x, y, 64 * data.ratio.x, 64 * data.ratio.y),
                'sprite': pygame.transform.scale(
                    random.choice(data.assets['props']['rocks']),
                    (int(64 * data.ratio.x), int(64 * data.ratio.y))
                ),
                'health': 2
            })

        self.seed_market = {
            'rect': pygame.Rect(0, -64, 192 * data.ratio.x, 192 * data.ratio.y),
            'sprite': pygame.transform.scale(
                data.assets['builds']['seed'],
                (192 * data.ratio.x, 192 * data.ratio.y)
            ),
            'health': 0
        }

        self.sell_market = {
            'rect': pygame.Rect(256, -64, 192 * data.ratio.x, 192 * data.ratio.y),
            'sprite': pygame.transform.scale(
                data.assets['builds']['sell'],
                (192 * data.ratio.x, 192 * data.ratio.y)
            ),
            'health': 0
        }

    # ------------------------------------------------------------------
    # Update & Render
    # ------------------------------------------------------------------
    def update(self, dt):
        # Engine handles camera and particle updates automatically
        self.input_handle(dt)
        self.player.update(dt)

        # Update timer
        if self.start_playing is not None:
            remaining_time = self.max_time_playing - (time.time() - self.start_playing)
            if remaining_time > 60:
                minutes = int(remaining_time // 60)
                seconds = int(remaining_time % 60)
                time_text = f"Time Remaining: {minutes}min {seconds}s"
            else:
                time_text = f"Time Remaining: {int(remaining_time)}s"
            self.time_display.set_text(time_text)

        # Plant growth
        for plant_box in self.plant_boxes:
            if plant_box['plant'] is not None and plant_box['plant']['state'] < 2:
                if time.time() - plant_box['plant']['growth_timer'] > 5:
                    plant_box['plant']['state'] += 1
                    plant_box['plant']['growth_timer'] = time.time()

    def render_world(self, renderer):
        render_list = self.plant_boxes.copy()
        render_list.extend(self.trees)
        render_list.extend(self.rocks)
        render_list.append(self.seed_market)
        render_list.append(self.sell_market)
        render_list.sort(key=lambda x: x['rect'].y)

        for r in render_list:
            if r in self.trees or r in self.rocks:
                renderer.blit(r['sprite'], self.camera.world_to_screen(r['rect'].topleft))
            elif r in self.plant_boxes:
                renderer.blit(r['base'], self.camera.world_to_screen(r['rect'].topleft))
                if r['plant'] is not None:
                    sprite = pygame.transform.scale(
                        r['plant']['sprites'][r['plant']['state']],
                        (64 * data.ratio.x, 64 * data.ratio.y)
                    )
                    renderer.blit(sprite, self.camera.world_to_screen(r['rect'].topleft))
            else:
                renderer.blit(r['sprite'], self.camera.world_to_screen(r['rect'].topleft))

    def render(self, renderer):
        renderer.fill_screen((100, 190, 120))

        self.render_world(renderer)
        self.player.render(renderer, self.engine, self.camera)

        # UI background panels
        renderer.draw_rect(
            5 * data.ratio.x, self.engine.height - 70 * data.ratio.y,
            self.engine.width - 10 * data.ratio.x, 65 * data.ratio.y,
            ThemeManager.get_color('background')
        )
        renderer.draw_rect(
            5 * data.ratio.x, self.engine.height - 250 * data.ratio.y,
            165 * data.ratio.x, 175 * data.ratio.y,
            ThemeManager.get_color('background')
        )

        # Update HUD texts
        self.money_display.set_text(f'$ {self.player.inventory.get("money", 0)}')
        self.seed_display.set_text(
            f'Wheat({self.player.inventory.get("wheat_seeds", 0)}x), '
            f'Carrot({self.player.inventory.get("carrot_seeds", 0)}x)'
        )
        inv_text = (
            f"Inventory: Wheat({self.player.inventory.get('wheat', 0)}) "
            f"Carrot({self.player.inventory.get('carrot', 0)}) "
            f"Wood({self.player.inventory.get('wood', 0)}) "
            f"Rock({self.player.inventory.get('stone', 0)})"
        )
        self.inventory_display.set_text(inv_text)

        # Highlight selected seed
        renderer.draw_rect(
            (127 + (80 * self.player.current_seed)) * data.ratio.x,
            self.engine.height - 22 * data.ratio.y,
            len(self.player.seeds[self.player.current_seed]) * 15 * data.ratio.x,
            22 * data.ratio.y,
            (150, 160, 90, 0.35),
            pivot=(0.0, 1.0)
        )

        # Dark overlay for shops
        if self.sell_market_open or self.seed_market_open:
            renderer.draw_rect(
                100 * data.ratio.x, 75 * data.ratio.y,
                self.engine.width - 200 * data.ratio.x,
                self.engine.height - 150 * data.ratio.y,
                ThemeManager.get_color('background2'),
                pivot=(0.0, 0.0)
            )


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    fullscreen = False
    if len(sys.argv) >= 2 and sys.argv[1] == "--fullscreen":
        fullscreen = True

    engine = LunaEngine("Farming", 1280, 720, fullscreen=fullscreen, debug=True)
    pygame.display.set_icon(pygame.image.load(f"{os.path.dirname(__file__)}/assets/icon.png"))
    engine.initialize()

    data.ratio = pygame.Vector2(engine.width / 1280, engine.height / 720)

    # Add scenes (classes are instantiated by engine)
    engine.add_scene("main", MainMenu)
    engine.add_scene("game", GameScene)
    engine.add_scene("game_over", GameOverScene)

    engine.set_scene("main")

    data.load_assets()
    data.load_player_animations()

    engine.run()


if __name__ == "__main__":
    main()