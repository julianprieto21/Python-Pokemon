import pygame as p
from game_battle import BattleGame
from settings_ import *
from pytmx.util_pygame import load_pygame


class Tile(p.sprite.Sprite):
    """
    Clase necesaria para mostrar el mapa en pantalla
    """
    def __init__(self, pos, surface, groups):
        super().__init__(groups)
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

    def __init__(self, x, y):
        super().__init__()
        # Animación
        self.frame = 0
        self.speed = 20
        self.run = False
        self.direction = "down"
        self.delay = 0
        # Imágenes
        self.walk_images, self.run_images = self.load_sprite()
        self.image = self.walk_images["down"][0]
        self.rect = self.image.get_rect()
        self.rect.center = x, y

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

    def update(self):
        """
        Actualiza el sprite según la tecla de movimiento presionada
        """
        keys = p.key.get_pressed()
        if keys[p.K_LSHIFT]:  # Run
            self.speed = 20
            self.delay = 20
            self.run = True
        else:
            self.speed = 10
            self.delay = 60
            self.run = False

        if keys[p.K_LEFT] or keys[p.K_a]:  # Left
            if self.rect.centerx <= 540:
                self.speed = 0
                self.frame = 0
            self.rect.centerx -= self.speed
            self.image = self.update_sprite("left", self.frame)
            self.direction = "left"

            self.update_frame()
        elif keys[p.K_RIGHT] or keys[p.K_d]:  # Right
            if self.rect.centerx >= 3400:
                self.speed = 0
                self.frame = 0
            self.rect.centerx += self.speed
            self.image = self.update_sprite("right", self.frame)
            self.direction = "right"
            self.update_frame()
        elif keys[p.K_UP] or keys[p.K_w]:  # Up
            if self.rect.centery <= 280:
                self.speed = 0
                self.frame = 0
            self.rect.centery -= self.speed
            self.image = self.update_sprite("up", self.frame)
            self.direction = "up"
            self.update_frame()
        elif keys[p.K_DOWN] or keys[p.K_s]:  # Down
            if self.rect.centery >= 2300:
                self.speed = 0
                self.frame = 0
            self.rect.centery += self.speed
            self.image = self.update_sprite("down", self.frame)
            self.direction = "down"
            self.update_frame()
        else:
            self.frame = 0
            self.image = self.update_sprite(self.direction, 0)
        p.time.delay(self.delay)

    def update_frame(self):
        """
        Actualiza el frame cada iteración para recrear la animación de movimiento
        """
        self.frame += 1
        self.frame = 0 if self.frame == 3 else self.frame


class Camera:
    """
    Clase encargada de la camara la cual sigue al jugador constantemente
    """
    def __init__(self, width, height, map_width, map_height):
        self.camera = p.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        """
        Devuelve el rect actual de la camara luego de ser actualizado
        """
        return entity.rect.move(self.camera.topleft)

    def update(self, target):
        """
        Actualiza el rect de la camara según la posición actual del jugador
        """
        x = -target.rect.x + SCREEN_WIDTH / 2
        y = -target.rect.y + SCREEN_HEIGHT / 2
        self.camera = p.Rect(x, y, self.width, self.height)


class MainGame:
    """
    Clase principal del juego. Muestra al jugador y al mapa en pantalla
    """
    def __init__(self):
        self.running = True
        self.multiplier = 3
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT + PANEL_HEIGHT
        self.screen = p.display.set_mode((self.width, self.height))
        self.player = Player(SCREEN_WIDTH / 2 * 4, (SCREEN_HEIGHT + PANEL_HEIGHT) / 2 * 4)
        self.clock = p.time.Clock()
        self.group = p.sprite.Group()
        self.tmx_data = load_pygame("assets/maps_/test/pokemon_map.tmx")
        self.camera = Camera(self.width, self.height, self.tmx_data.width, self.tmx_data.height)
        self.rects = {}

    def cycle(self):
        """
        Muestra en pantalla las diferentes capas del mapa
        """
        for layer in self.tmx_data.visible_layers:
            if hasattr(layer, "data"):
                for x, y, surface in layer.tiles():
                    pos = (x * 16 * self.multiplier, y * 16 * self.multiplier)
                    surface = p.transform.scale(surface, (surface.get_width() * self.multiplier, surface.get_height() * self.multiplier))
                    Tile(pos=pos, surface=surface, groups=self.group)

    def show_map_objects(self):
        """
        Muestra los diferentes objetos del mapa en pantalla
        """
        for obj in self.tmx_data.objects:
            pos = (obj.x * self.multiplier, obj.y * self.multiplier)
            if obj.name in ("House", "Tree", "Statue", "Clinic", "Grass", "Decoration"):
                surface = obj.image
                surface = p.transform.scale(surface, (surface.get_width() * self.multiplier,
                                                      surface.get_height() * self.multiplier))
                Tile(pos=pos, surface=surface, groups=self.group)
                if obj.name == "Grass":
                    self.rects[obj.name] = p.Rect((obj.x * self.multiplier + self.player.rect.width,
                                                   obj.y * self.multiplier,
                                                   obj.width * self.multiplier - self.player.rect.width,
                                                   obj.height * self.multiplier - self.player.rect.height))

    def check_collision(self):
        if self.player.rect.colliderect(self.rects["Grass"]):
            battle = BattleGame()
            battle.main()
            self.player.rect.center = SCREEN_WIDTH / 2 * 4, (SCREEN_HEIGHT + PANEL_HEIGHT) / 2 * 4

    def check_events(self):
        """
        Verifica los eventos de teclado
        """
        for event in p.event.get():
            if event.type == p.QUIT:
                self.running = False

    def main(self):
        """
        Función principal del juego
        """
        p.init()
        self.cycle()
        self.show_map_objects()
        self.group.add(self.player)
        while self.running:
            p.display.set_caption(f"PYTHON POKEMON-{self.clock.get_fps() :.1f}")
            self.check_events()
            self.group.draw(self.screen)
            self.player.update()
            self.camera.update(self.player)
            self.check_collision()
            self.screen.fill((0, 0, 0))

            for sprite in self.group:
                self.screen.blit(sprite.image, self.camera.apply(sprite))

            p.display.flip()
            self.clock.tick(FPS)
