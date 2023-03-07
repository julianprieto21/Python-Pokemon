import random
import sys
import pygame as p
from pytmx.util_pygame import load_pygame
from settings import *


class Tile(p.sprite.Sprite):
    """
    Clase necesaria para mostrar el mapa en pantalla
    """
    def __init__(self, pos, surface, group):
        super().__init__(group)
        self.image = surface
        self.rect = self.image.get_rect(topleft=pos)


class Player(p.sprite.Sprite):
    """
    Clase encargada del sprite del usuario y de sus animaciones
    """
    sprite_path = DIR + "sprites_/over-world/trainer/gold_trainer.png"
    sprite_run_path = DIR + "sprites_/over-world/trainer/gold_trainer_run.png"
    sprite_width = 21
    sprite_height = 25
    sprite_size = (sprite_width, sprite_height)
    scaled_size = (sprite_width * 4, sprite_height * 4)

    def __init__(self, pos, group, rects):
        super().__init__(group)
        # Movimiento de personaje
        self.frame = 0
        self.speed = 10
        self.run = False
        self.direction = "down"
        #self.direction = p.math.Vector2(0, -1)
        self.delay = 0
        # Imágenes
        self.walk_images, self.run_images = self.load_sprite()
        self.image = self.walk_images["down"][0]
        self.rect = self.image.get_rect(center=pos)
        self.obstacles, self.battle_zones = rects

    def load_sprite(self):
        """
        Cargar los sprites necesarias para caminar y para correr en las 4 direcciones
        """
        walk = {"up": {}, "down": {}, "right": {}, "left": {}}
        walking_image = p.image.load(self.sprite_path)
        run = {"up": {}, "down": {}, "right": {}, "left": {}}
        running_image = p.image.load(self.sprite_run_path)
        for frame in range(0, 3):
            for direction in ("up", "down", "right", "left"):
                i = 0 if direction == "down" else 3 if direction == "up" else 6 if direction == "left" else 9
                walk[direction][frame] = walking_image.subsurface(
                    (*(self.sprite_width * (i + frame), 0), *self.sprite_size))
                walk[direction][frame] = p.transform.scale(walk[direction][frame], self.scaled_size)

                run[direction][frame] = running_image.subsurface(
                    (*(self.sprite_width * (i + frame), 0), *self.sprite_size))
                run[direction][frame] = p.transform.scale(run[direction][frame], self.scaled_size)
        return walk, run

    def update_sprite(self, direction, frame):
        """
        Devuelve el sprite correspondiente al frame y a la acción actual (correr o caminar)
        """
        if self.run:
            return self.run_images[direction][frame]
        elif not self.run:
            return self.walk_images[direction][frame]

    def input(self):
        """
        Actualiza el sprite según la tecla de movimiento presionada
        """
        keys = p.key.get_pressed()
        self.run = True if keys[p.K_LSHIFT] else False  # Run
        self.speed = 30 if self.run else 10

        if keys[p.K_LEFT] or keys[p.K_a]:  # Left
            self.move_left()
        elif keys[p.K_RIGHT] or keys[p.K_d]:  # Right
            self.move_right()
        elif keys[p.K_UP] or keys[p.K_w]:  # Up
            self.move_up()
        elif keys[p.K_DOWN] or keys[p.K_s]:  # Down
            self.move_down()
        else:
            self.stand_still()

    def stand_still(self):
        self.frame = 0
        self.image = self.update_sprite(self.direction, 0)

    def move_up(self):
        self.rect.centery -= self.speed
        self.image = self.update_sprite("up", self.frame)
        self.direction = "up"
        self.update_frame()

    def move_down(self):
        self.rect.centery += self.speed
        self.image = self.update_sprite("down", self.frame)
        self.direction = "down"
        self.update_frame()

    def move_left(self):
        self.rect.centerx -= self.speed
        self.image = self.update_sprite("left", self.frame)
        self.direction = "left"
        self.update_frame()

    def move_right(self):
        self.rect.centerx += self.speed
        self.image = self.update_sprite("right", self.frame)
        self.direction = "right"
        self.update_frame()

    def update(self):
        self.input()
        self.check_collision()
        self.check_zones_collision()

    def update_frame(self):
        """
        Actualiza el frame cada iteración para recrear la animación de movimiento
        """
        self.frame += 1
        self.frame = 0 if self.frame == 3 else self.frame

    def check_collision(self):
        for rect in self.obstacles:
            if self.rect.colliderect(rect):
                self.frame = 0
                if self.direction == "down":
                    self.rect.bottom = rect.top
                elif self.direction == "up":
                    self.rect.top = rect.bottom
                elif self.direction == "left":
                    self.rect.left = rect.right
                elif self.direction == "right":
                    self.rect.right = rect.left

    def check_zones_collision(self):
        for zone in self.battle_zones:
            if self.rect.colliderect(zone):
                i = random.randint(0, 100)
                if i == 5:
                    print("battle")


class CameraGroup(p.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = p.display.get_surface()
        # camera offset
        self.offset = p.math.Vector2()
        self.half_w = WINDOW_W // 2
        self.half_h = WINDOW_H // 2

    def center_target(self, target):
        self.offset.x = target.centerx - self.half_w
        self.offset.y = target.centery - self.half_h

    def custom_draw(self, player):
        self.center_target(player)
        for sprite in self.sprites():
            offset_position = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_position)


class Main:
    objects = p.image.load(DIR+"maps_/test/starting_map.png")
    objects = p.transform.scale(objects, (objects.get_width() * 4, objects.get_height() * 4))

    def __init__(self):
        p.init()
        self.running = True
        self.multiplier = 4
        self.screen = p.display.set_mode((WINDOW_W, WINDOW_H))
        self.clock = p.time.Clock()
        self.tmx_data = load_pygame("assets/maps_/test/starting_map.tmx")
        self.map_w = self.tmx_data.width * 16
        self.map_h = self.tmx_data.height * 16
        self.camera_group = CameraGroup()
        self.boundaries = []
        self.battle_zones = []
        self.player = None
        self.player_start_pos = self.get_starting_pos()

        self.frame_time = 1000 // FPS
        self.last_update_time = p.time.get_ticks()

    def get_starting_pos(self):
        for obj in self.tmx_data.objects:
            if obj.name == "Starting_pos":
                return obj.x * self.multiplier, obj.y * self.multiplier

    def initialize_player(self):
        self.player = Player(self.player_start_pos, self.camera_group, (self.boundaries, self.battle_zones))

    def initialize_map(self):
        for layer in self.tmx_data.visible_layers:
            if layer.name in ("Layer_1", "Layer_2"):
                for x, y, surface in layer.tiles():
                    pos = (x * 16 * self.multiplier, y * 16 * self.multiplier)
                    surface = p.transform.scale(surface, (surface.get_width() * self.multiplier,
                                                          surface.get_height() * self.multiplier))
                    Tile(pos, surface, self.camera_group)

    def initialize_rects(self):
        for obj in self.tmx_data.objects:
            if obj.name == "Rect":
                self.boundaries.append(p.Rect((obj.x * self.multiplier, obj.y * self.multiplier,
                                               obj.width * self.multiplier, obj.height * self.multiplier)))
            elif obj.name == "Zone":
                self.battle_zones.append(p.Rect((obj.x * self.multiplier, obj.y * self.multiplier,
                                                 obj.width * self.multiplier, obj.height * self.multiplier)))

    def draw_objects(self):
        self.screen.blit(self.objects, (WINDOW_W // 2 - self.player.rect.x - 42,
                                        WINDOW_H // 2 - self.player.rect.y - 50))

    def run(self):
        self.initialize_map()
        self.initialize_rects()
        self.initialize_player()
        while self.running:
            p.display.set_caption(f"PYTHON POKEMON-{self.clock.get_fps() :.1f}")
            for event in p.event.get():
                if event.type == p.QUIT:
                    self.running = False
                    sys.exit()
            self.screen.fill((0, 0, 0))
            self.camera_group.update()
            self.camera_group.custom_draw(self.player.rect)
            self.draw_objects()

            current_time = p.time.get_ticks()
            elapsed_time = current_time - self.last_update_time
            if elapsed_time < self.frame_time:
                p.time.wait(self.frame_time - elapsed_time)
            self.last_update_time = current_time

            self.clock.tick(FPS)
            p.display.flip()



