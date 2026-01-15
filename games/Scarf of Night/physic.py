import pygame
import math
from typing import List, Tuple, Optional

# Constantes do sistema - AUMENTEI a aceleração e velocidades
GRAVITY = 1800
HORIZONTAL_ACCELERATION = 1200  # Aumentei de 800 para 1200
MAX_VELOCITY_X = 400  # Aumentei de 300 para 400
MAX_VELOCITY_Y = 800  # Aumentei de 600 para 800

# Constantes de movimento ninja
JUMP_VELOCITY = -600  # Aumentei o pulo
WALL_JUMP_VELOCITY = -500
WALL_JUMP_HORIZONTAL_VELOCITY = 300  # Aumentei
CLIMB_VELOCITY = 200  # Aumentei
DASH_VELOCITY = 700  # Aumentei
GLIDE_FALL_VELOCITY = 150

# Novas constantes para wall slide
WALL_SLIDE_ACCELERATION = 400  # Aceleração ao deslizar na parede
MAX_WALL_SLIDE_VELOCITY = 200  # Velocidade máxima de descida na parede

# Constantes de atrito
GROUND_FRICTION = 0.85  # Um pouco menos de atrito para deslizar mais
AIR_FRICTION = 0.98  # Menos atrito no ar para mais controle
SLIDE_FRICTION = 0.6

# Constantes de recursos
WALL_JUMP_COST = 8  # Reduzi um pouco o custo
WALL_RUN_COST = 4
DASH_COST = 20
GLIDE_COST = 6
STAMINA_REGEN = 25  # Aumentei a regeneração
CHAKRA_REGEN = 20

# Outras constantes
MIN_WALLRUN_VELOCITY = 150
DASH_COOLDOWN = 0.8  # Reduzi o cooldown
PLAYER_WIDTH = 32
PLAYER_HEIGHT = 64
WALL_DETECTION_DISTANCE = 15

class Vector2:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    
    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar: float):
        return Vector2(self.x * scalar, self.y * scalar)
    
    def __truediv__(self, scalar: float):
        return Vector2(self.x / scalar, self.y / scalar)
    
    def magnitude(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y)
    
    def normalized(self):
        mag = self.magnitude()
        if mag == 0:
            return Vector2(0, 0)
        return Vector2(self.x / mag, self.y / mag)

class Rectangle:
    def __init__(self, x: float, y: float, width: float, height: float):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    @property
    def left(self):
        return self.x
    
    @property
    def right(self):
        return self.x + self.width
    
    @property
    def top(self):
        return self.y
    
    @property
    def bottom(self):
        return self.y + self.height
    
    def collides_with(self, other: 'Rectangle') -> bool:
        return (self.left < other.right and 
                self.right > other.left and 
                self.top < other.bottom and 
                self.bottom > other.top)
    
    def copy(self):
        return Rectangle(self.x, self.y, self.width, self.height)

class Collision:
    def __init__(self, type: str, direction: str, correction: Vector2, tile: Rectangle = None):
        self.type = type
        self.direction = direction
        self.correction = correction
        self.tile = tile

class CollisionSystem:
    def __init__(self):
        self.collidable_tiles = []
        self.camera_offset = Vector2(0, 0)
    
    def set_camera_offset(self, offset: Vector2):
        self.camera_offset = offset
    
    def set_collidable_tiles(self, tiles: List[Rectangle]):
        self.collidable_tiles = tiles
    
    def detect_collisions(self, player_rect: Rectangle) -> List[Collision]:
        collisions = []
        
        for tile in self.collidable_tiles:
            world_tile = self._apply_camera_offset(tile)
            if player_rect.collides_with(world_tile):
                collision = self._calculate_collision_response(player_rect, world_tile)
                if collision:
                    collisions.append(collision)
        
        return collisions
    
    def _apply_camera_offset(self, tile: Rectangle) -> Rectangle:
        return Rectangle(
            tile.x - self.camera_offset.x,
            tile.y - self.camera_offset.y,
            tile.width,
            tile.height
        )
    
    def _calculate_collision_response(self, player_rect: Rectangle, tile: Rectangle) -> Optional[Collision]:
        # Calcular sobreposições em todos os lados
        overlap_left = player_rect.right - tile.left
        overlap_right = tile.right - player_rect.left
        overlap_top = player_rect.bottom - tile.top
        overlap_bottom = tile.bottom - player_rect.top
        
        # Só considerar sobreposições positivas (real sobreposição)
        if overlap_left <= 0 or overlap_right <= 0 or overlap_top <= 0 or overlap_bottom <= 0:
            return None
        
        # Encontrar a menor sobreposição para determinar a direção principal
        min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)
        
        # Determinar direção da colisão baseada na menor sobreposição
        if min_overlap == overlap_top:
            return Collision("vertical", "top", Vector2(0, -overlap_top), tile)
        elif min_overlap == overlap_bottom:
            return Collision("vertical", "bottom", Vector2(0, overlap_bottom), tile)
        elif min_overlap == overlap_left:
            return Collision("horizontal", "left", Vector2(-overlap_left, 0), tile)
        elif min_overlap == overlap_right:
            return Collision("horizontal", "right", Vector2(overlap_right, 0), tile)
        
        return None

class NinjaPlayer:
    def __init__(self, x: float, y: float):
        self.position = Vector2(x, y)
        self.velocity = Vector2(0, 0)
        self.acceleration = Vector2(0, 0)
        
        self.on_ground = False
        self.wall_left = False
        self.wall_right = False
        self.direction = 1  # 1 para direita, -1 para esquerda
        
        # Recursos do ninja
        self.chakra = 100
        self.stamina = 100
        self.max_velocity = Vector2(MAX_VELOCITY_X, MAX_VELOCITY_Y)
        
        # Estados
        self.state = "normal"  # normal, sliding, climbing, gliding, dashing, wall_sliding
        self.dash_cooldown = 0
        self.wall_slide_timer = 0
        self.wall_slide_direction = 0
        
        # Sistema de colisão
        self.collision_system = CollisionSystem()
        self.size = Vector2(PLAYER_WIDTH, PLAYER_HEIGHT)
        
        # Debug
        self.last_collisions = []
    
    def get_rect(self) -> Rectangle:
        return Rectangle(self.position.x, self.position.y, self.size.x, self.size.y)
    
    def update(self, delta_time: float, inputs: dict):
        self._process_inputs(inputs, delta_time)
        self._update_physics(delta_time)
        
        # Atualizar posição primeiro
        self.position += self.velocity * delta_time
        
        # Depois detectar e resolver colisões
        self._resolve_collisions()
        
        self._limit_velocity()
        self._update_resources(delta_time)
        self._update_wall_slide(delta_time)
        
        if self.dash_cooldown > 0:
            self.dash_cooldown -= delta_time
    
    def _update_resources(self, delta_time: float):
        # Regenerar stamina no chão ou na parede
        if self.on_ground or self.state == "wall_sliding":
            self.stamina = min(100, self.stamina + STAMINA_REGEN * delta_time)
        
        # Regenerar chakra sempre
        self.chakra = min(100, self.chakra + CHAKRA_REGEN * delta_time)
    
    def _process_inputs(self, inputs: dict, delta_time: float):
        # Movimento horizontal - MAIS RÁPIDO
        if self.state in ["normal", "gliding", "wall_sliding"]:
            if inputs.get("left"):
                self.acceleration.x -= HORIZONTAL_ACCELERATION
                self.direction = -1
            if inputs.get("right"):
                self.acceleration.x += HORIZONTAL_ACCELERATION
                self.direction = 1
        
        # Escalar paredes - MAIS RÁPIDO
        if self.state == "climbing":
            if inputs.get("up"):
                self.velocity.y = -CLIMB_VELOCITY
            elif inputs.get("down"):
                self.velocity.y = CLIMB_VELOCITY
            else:
                self.velocity.y = 0
        
        # Pulo - MAIS ALTO
        if inputs.get("jump_pressed"):
            if self.on_ground:
                self._jump()
            elif (self.wall_left or self.wall_right) and self.stamina > 0:
                self._wall_jump()
        
        # Dash - MAIS RÁPIDO
        if inputs.get("dash") and self.dash_cooldown <= 0 and self.chakra >= DASH_COST:
            self._dash()
        
        # Planar
        if inputs.get("glide") and self.stamina > 0 and not self.on_ground:
            self._glide(delta_time)
        elif self.state == "gliding":
            self.state = "normal"
        
        # Deslizar
        if inputs.get("slide") and self.on_ground:
            self.state = "sliding"
        elif self.state == "sliding" and (not inputs.get("slide") or not self.on_ground):
            self.state = "normal"
    
    def _update_physics(self, delta_time: float):
        # Aplicar gravidade
        if self.state not in ["climbing", "gliding", "wall_sliding"]:
            self.acceleration.y += GRAVITY
        elif self.state == "gliding":
            self.acceleration.y += GRAVITY * 0.3
        elif self.state == "wall_sliding":
            # Gravidade reduzida durante wall slide
            self.acceleration.y += GRAVITY * 0.6
        
        # Atualizar velocidade com aceleração
        self.velocity += self.acceleration * delta_time
        self.acceleration = Vector2(0, 0)
        
        # Aplicar atrito - MENOS ATRITO PARA MAIS VELOCIDADE
        if self.on_ground:
            if self.state == "sliding":
                self.velocity.x *= SLIDE_FRICTION
            else:
                self.velocity.x *= GROUND_FRICTION
        else:
            self.velocity.x *= AIR_FRICTION
    
    def _update_wall_slide(self, delta_time: float):
        # Sistema de wall slide - descer gradualmente na parede
        if (self.wall_left or self.wall_right) and not self.on_ground and self.state != "climbing":
            if self.state != "wall_sliding":
                self.state = "wall_sliding"
                self.wall_slide_timer = 0
                self.wall_slide_direction = -1 if self.wall_left else 1
            
            # Aumentar velocidade de descida gradualmente
            self.wall_slide_timer += delta_time
            slide_speed = min(MAX_WALL_SLIDE_VELOCITY, WALL_SLIDE_ACCELERATION * self.wall_slide_timer)
            
            # Aplicar velocidade de descida
            if self.velocity.y > 0:  # Só acelera se estiver caindo
                self.velocity.y = slide_speed
            
            # Manter o jogador próximo à parede
            if self.wall_left:
                self.velocity.x = max(self.velocity.x, 0)
            elif self.wall_right:
                self.velocity.x = min(self.velocity.x, 0)
        
        elif self.state == "wall_sliding" and (not self.wall_left and not self.wall_right or self.on_ground):
            self.state = "normal"
            self.wall_slide_timer = 0
    
    def _resolve_collisions(self):
        player_rect = self.get_rect()
        collisions = self.collision_system.detect_collisions(player_rect)
        self.last_collisions = collisions
        
        # Resetar estados
        was_on_ground = self.on_ground
        self.on_ground = False
        self.wall_left = False
        self.wall_right = False
        
        for collision in collisions:
            self._process_collision(collision)
        
        # Detectar paredes para wall slide
        self._detect_walls()
    
    def _process_collision(self, collision: Collision):
        # Aplicar correção de posição
        self.position += collision.correction
        
        if collision.direction == "top":  # Colisão com chão
            self.on_ground = True
            self.velocity.y = 0  # Parar completamente a velocidade vertical
            if self.state != "sliding":
                self.state = "normal"
            self.wall_slide_timer = 0  # Resetar wall slide
            
        elif collision.direction == "bottom":  # Colisão com teto
            self.velocity.y = 0  # Parar movimento para cima
            
        elif collision.direction == "left":  # Colisão com parede direita
            self.wall_right = True
            self.velocity.x = max(0, self.velocity.x)  # Só para movimento para a direita
            
        elif collision.direction == "right":  # Colisão com parede esquerda
            self.wall_left = True
            self.velocity.x = min(0, self.velocity.x)  # Só para movimento para a esquerda
    
    def _detect_walls(self):
        # Detecção adicional de paredes para wall slide
        if not self.on_ground:
            player_rect = self.get_rect()
            
            # Raycast para esquerda
            left_ray = Rectangle(player_rect.left - 2, player_rect.top + 5, 5, player_rect.height - 10)
            for tile in self.collision_system.collidable_tiles:
                world_tile = self.collision_system._apply_camera_offset(tile)
                if left_ray.collides_with(world_tile):
                    self.wall_left = True
                    break
            
            # Raycast para direita
            right_ray = Rectangle(player_rect.right - 3, player_rect.top + 5, 5, player_rect.height - 10)
            for tile in self.collision_system.collidable_tiles:
                world_tile = self.collision_system._apply_camera_offset(tile)
                if right_ray.collides_with(world_tile):
                    self.wall_right = True
                    break
        
        # Parar de escalar se não há mais parede
        if self.state == "climbing" and not self.wall_left and not self.wall_right:
            self.state = "normal"
            self.velocity.y = 0
    
    def _jump(self):
        self.velocity.y = JUMP_VELOCITY
        self.on_ground = False
    
    def _wall_jump(self):
        self.stamina -= WALL_JUMP_COST
        self.velocity.y = WALL_JUMP_VELOCITY
        
        if self.wall_left:
            self.velocity.x = WALL_JUMP_HORIZONTAL_VELOCITY
            self.direction = 1  # Virar para longe da parede
        elif self.wall_right:
            self.velocity.x = -WALL_JUMP_HORIZONTAL_VELOCITY
            self.direction = -1  # Virar para longe da parede
        
        self.state = "normal"
        self.wall_slide_timer = 0
    
    def _start_wall_run(self, wall_direction: str):
        if self.stamina > WALL_RUN_COST:
            self.state = "climbing"
            self.velocity.y = 0
    
    def _dash(self):
        self.chakra -= DASH_COST
        dash_direction = Vector2(self.direction, 0)
        self.velocity = dash_direction * DASH_VELOCITY
        self.state = "dashing"
        self.dash_cooldown = DASH_COOLDOWN
    
    def _glide(self, delta_time: float):
        self.state = "gliding"
        self.stamina -= GLIDE_COST * delta_time
        # Limitar velocidade de queda
        if self.velocity.y > 0:
            self.velocity.y *= 0.3  # Planagem mais eficiente
    
    def _limit_velocity(self):
        self.velocity.x = max(-self.max_velocity.x, min(self.velocity.x, self.max_velocity.x))
        self.velocity.y = max(-self.max_velocity.y, min(self.velocity.y, self.max_velocity.y))
    
    def draw(self, screen):
        # Desenhar jogador
        color = (255, 0, 0)  # Vermelho
        if self.state == "sliding":
            color = (255, 128, 0)  # Laranja
        elif self.state == "climbing":
            color = (0, 255, 0)  # Verde
        elif self.state == "gliding":
            color = (0, 128, 255)  # Azul
        elif self.state == "dashing":
            color = (255, 0, 255)  # Magenta
        elif self.state == "wall_sliding":
            color = (255, 255, 0)  # Amarelo para wall slide
        
        rect = pygame.Rect(
            self.position.x - self.collision_system.camera_offset.x,
            self.position.y - self.collision_system.camera_offset.y,
            self.size.x,
            self.size.y
        )
        pygame.draw.rect(screen, color, rect)
        
        # Desenhar direção
        direction_line = [
            (rect.centerx, rect.centery),
            (rect.centerx + self.direction * 20, rect.centery)
        ]
        pygame.draw.line(screen, (255, 255, 255), direction_line[0], direction_line[1], 2)
        
        # Debug: desenhar colisões
        for collision in self.last_collisions:
            if collision.tile:
                tile_rect = pygame.Rect(
                    collision.tile.x - self.collision_system.camera_offset.x,
                    collision.tile.y - self.collision_system.camera_offset.y,
                    collision.tile.width,
                    collision.tile.height
                )
                pygame.draw.rect(screen, (255, 255, 0), tile_rect, 3)

# O resto do código (TileManager e Game) permanece igual...

class TileManager:
    def __init__(self):
        self.tiles = []
        self.camera_offset = Vector2(0, 0)
    
    def set_camera_offset(self, offset: Vector2):
        self.camera_offset = offset
    
    def add_tile(self, x: float, y: float, width: float, height: float, collidable: bool = True):
        tile = Rectangle(x, y, width, height)
        self.tiles.append((tile, collidable))
    
    def get_visible_collidable_tiles(self) -> List[Rectangle]:
        visible_tiles = []
        
        for tile, collidable in self.tiles:
            if collidable:
                # Verificar se o tile está dentro da viewport da câmera
                world_tile_x = tile.x - self.camera_offset.x
                world_tile_y = tile.y - self.camera_offset.y
                
                if (world_tile_x + tile.width > 0 and world_tile_x < 1280 and
                    world_tile_y + tile.height > 0 and world_tile_y < 768):
                    visible_tiles.append(tile)
        
        return visible_tiles
    
    def draw(self, screen):
        for tile, collidable in self.tiles:
            screen_pos = Vector2(
                tile.x - self.camera_offset.x,
                tile.y - self.camera_offset.y
            )
            
            # Verificar se o tile está visível na tela
            if (screen_pos.x + tile.width > 0 and screen_pos.x < 1280 and
                screen_pos.y + tile.height > 0 and screen_pos.y < 768):
                
                color = (100, 100, 100) if collidable else (200, 200, 200)
                rect = pygame.Rect(screen_pos.x, screen_pos.y, tile.width, tile.height)
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, (50, 50, 50), rect, 1)

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1280, 768))
        pygame.display.set_caption("Ninja Platformer - MAIS RÁPIDO com Wall Slide")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Sistemas
        self.tile_manager = TileManager()
        self.player = NinjaPlayer(100, 300)
        
        # Conectar sistemas
        self.player.collision_system.set_camera_offset(Vector2(0, 0))
        
        # Variáveis de input
        self.jump_pressed = False
        
        # Criar nível de exemplo
        self._create_test_level()
    
    def _create_test_level(self):
        # Chão principal
        for i in range(0, 2000, 64):
            self.tile_manager.add_tile(i, 700, 64, 68)
        
        # Plataformas de teste
        self.tile_manager.add_tile(300, 600, 200, 32)
        self.tile_manager.add_tile(600, 500, 150, 32)
        self.tile_manager.add_tile(900, 400, 100, 32)
        self.tile_manager.add_tile(1200, 300, 100, 32)
        
        # Paredes altas para testar wall slide
        self.tile_manager.add_tile(200, 400, 50, 300)
        self.tile_manager.add_tile(500, 200, 50, 500)
        self.tile_manager.add_tile(1000, 100, 50, 600)
    
    def run(self):
        while self.running:
            delta_time = self.clock.tick(60) / 1000.0
            
            # Processar eventos
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.jump_pressed = True
            
            # Obter inputs
            inputs = self._get_inputs()
            
            # Atualizar offset da câmera (seguir jogador)
            camera_x = max(0, self.player.position.x - 640)
            self.tile_manager.set_camera_offset(Vector2(camera_x, 0))
            self.player.collision_system.set_camera_offset(Vector2(camera_x, 0))
            
            # Atualizar tiles colidíveis visíveis
            visible_tiles = self.tile_manager.get_visible_collidable_tiles()
            self.player.collision_system.set_collidable_tiles(visible_tiles)
            
            # Atualizar jogador
            self.player.update(delta_time, inputs)
            
            # Resetar jump_pressed
            self.jump_pressed = False
            
            # Renderizar
            self.screen.fill((30, 30, 50))
            self.tile_manager.draw(self.screen)
            self.player.draw(self.screen)
            
            # Desenhar UI
            self._draw_ui()
            
            pygame.display.flip()
        
        pygame.quit()
    
    def _get_inputs(self) -> dict:
        keys = pygame.key.get_pressed()
        return {
            "left": keys[pygame.K_LEFT] or keys[pygame.K_a],
            "right": keys[pygame.K_RIGHT] or keys[pygame.K_d],
            "up": keys[pygame.K_UP] or keys[pygame.K_w],
            "down": keys[pygame.K_DOWN] or keys[pygame.K_s],
            "jump_pressed": self.jump_pressed,
            "dash": keys[pygame.K_LSHIFT],
            "glide": keys[pygame.K_LCTRL],
            "slide": keys[pygame.K_z]
        }
    
    def _draw_ui(self):
        # Barra de stamina
        stamina_width = 200
        stamina_height = 20
        stamina_rect = pygame.Rect(10, 10, stamina_width, stamina_height)
        pygame.draw.rect(self.screen, (50, 50, 50), stamina_rect)
        
        fill_width = int((self.player.stamina / 100) * stamina_width)
        fill_rect = pygame.Rect(10, 10, fill_width, stamina_height)
        pygame.draw.rect(self.screen, (0, 255, 0), fill_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), stamina_rect, 2)
        
        # Barra de chakra
        chakra_rect = pygame.Rect(10, 40, stamina_width, stamina_height)
        pygame.draw.rect(self.screen, (50, 50, 50), chakra_rect)
        
        fill_width = int((self.player.chakra / 100) * stamina_width)
        fill_rect = pygame.Rect(10, 40, fill_width, stamina_height)
        pygame.draw.rect(self.screen, (0, 128, 255), fill_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), chakra_rect, 2)
        
        # Estado do jogador
        font = pygame.font.Font(None, 36)
        state_text = font.render(f"State: {self.player.state}", True, (255, 255, 255))
        self.screen.blit(state_text, (10, 70))
        
        # Posição do jogador (para debug)
        pos_text = font.render(f"Pos: ({int(self.player.position.x)}, {int(self.player.position.y)})", True, (255, 255, 255))
        self.screen.blit(pos_text, (10, 110))
        
        # Velocidade do jogador (para debug)
        vel_text = font.render(f"Vel: ({int(self.player.velocity.x)}, {int(self.player.velocity.y)})", True, (255, 255, 255))
        self.screen.blit(vel_text, (10, 150))
        
        # Wall Slide Timer (para debug)
        slide_text = font.render(f"Wall Slide: {self.player.wall_slide_timer:.1f}s", True, (255, 255, 255))
        self.screen.blit(slide_text, (10, 190))

if __name__ == "__main__":
    game = Game()
    game.run()