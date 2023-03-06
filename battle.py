from settings import *
from engine import Pokemon, Battle
import pygame as p
import random
import numpy as np
from pathlib import Path

global choice_rect
global battle_rect
global play_rect


class SpritePokemon(p.sprite.Sprite):

    sprites_front = p.image.load(DIR + SPRITES + "sprites_front.png")
    sprites_back = p.image.load(DIR + SPRITES + "sprites_back.png")
    # Cálculos de posición
    sprite_width = sprites_front.get_width() // 28
    sprite_height = sprites_front.get_height() // 18
    sprite_size = (80, 80)
    scaled_size = (256, 256)

    def __init__(self, nro, front_view=False):
        super().__init__()
        self.id_pokemons_array = POK_ARRAY
        c, r = np.where(self.id_pokemons_array == nro)
        c = c[0]
        r = r[0]
        if front_view:  # Imagen de frente (oponente)
            self.image = self.sprites_front
            sprite_x = r * self.sprite_height
            sprite_y = c * self.sprite_width
            self.image = self.image.subsurface((sprite_x, sprite_y, *self.sprite_size))
            self.image = p.transform.scale(self.image, self.scaled_size)
            self.rect = self.image.get_rect()
            self.rect.x = SCREEN_WIDTH + 4
            self.rect.y = SCREEN_HEIGHT // 7
            self.final_x = SCREEN_WIDTH - self.image.get_width() - 100
            self.final_y = self.rect.y
            self.speed = -10

        else:  # Imagen de atrás (aliado)
            self.image = self.sprites_back
            sprite_x = r * self.sprite_height
            sprite_y = c * self.sprite_width
            self.image = self.image.subsurface((sprite_x, sprite_y, *self.sprite_size))
            self.image = p.transform.scale(self.image, self.scaled_size)
            self.rect = self.image.get_rect()
            self.rect.x = -self.image.get_width() - 4
            self.rect.y = SCREEN_HEIGHT - self.image.get_height()
            self.final_x = 100
            self.final_y = self.rect.y
            self.speed = 10

    def update(self, pos):
        self.rect.x = pos


class BattleMain:
    def __init__(self):
        # Display
        #p.init()  ########################
        self.running = True
        self.clock = p.time.Clock()
        self.screen = p.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT + PANEL_HEIGHT))
        self.fonts = {}
        self.images = {}
        self.buttons = {}
        # Game
        self.user_sprite = None
        self.cpu_sprite = None
        self.id_pokemons = random.sample(range(1, 494), 6)
        self.id_pokemons_array = np.arange(1, 505).reshape(18, 28)
        self.current_sprites = None
        self.choice = None
        self.enemy = random.randint(1, 493)
        self.battle = None
        # Events
        self.selected = None
        self.interface = "start"
        self.animation_made = False
        self.ally_move = None
        self.enemy_move = None

    # Cargar las fuentes necesarias
    def load_fonts(self):
        self.fonts = {
            "title": p.font.Font(DIR + GUI + "font.ttf", 100),
            "button": p.font.Font(DIR + GUI + "font.ttf", 64),
            "text": p.font.Font(DIR + GUI + "font.ttf", 32)

        }

    # Cargar imágenes necesarias
    def load_images(self):
        """
        Carga de imágenes general
        :return:
        """
        gui_path = Path(DIR) / GUI
        # Start

        self.images["ss"] = p.image.load(DIR + SPRITES + "spritesheet.png").convert_alpha()
        ss_width = self.images["ss"].get_width() / 28
        ss_height = self.images["ss"].get_height() / 18
        for nro in self.id_pokemons:
            pos = np.where(self.id_pokemons_array == nro)
            col = pos[0][0]
            row = pos[1][0]
            h = col * ss_width
            w = row * ss_height
            self.images[nro] = self.images["ss"].subsurface((w, h, 100, 100))
        self.images["op"] = p.image.load(DIR+GUI+"option.png")
        self.images["op"].set_alpha(120)

        # Battle
        self.images["battle_bg"] = p.image.load(str(gui_path / "battle_bg.png"))
        self.images["blue_bar"] = p.image.load(str(gui_path / "blue_bar.png"))
        self.images["options_bar"] = p.image.load(str(gui_path / "options_bar.png"))
        self.images["mouse"] = p.image.load(str(gui_path / "mouse.png"))
        self.images["info_ally"] = p.image.load(str(gui_path / "info_ally.png"))
        self.images["info_enemy"] = p.image.load(str(gui_path / "info_enemy.png"))
        self.images["fight"] = p.image.load(str(gui_path / "fight.png"))

    # Verificar eventos de teclado/mouse
    def check_events(self):
        """
        Verifica eventos
        :return:
        """
        LEFT_BUTTON = 1
        RIGHT_BUTTON = 3
        for event in p.event.get():
            if event.type == p.QUIT:
                self.running = False
            elif event.type == p.MOUSEBUTTONDOWN:
                pos = p.mouse.get_pos()
                if event.button == LEFT_BUTTON:
                    # Botón izquierdo
                    if self.interface == "start":
                        self.start_mouse_events(pos)
                    elif self.interface[0:6] == "battle":
                        self.battle_mouse_events(pos)
                elif event.button == RIGHT_BUTTON and self.interface[:11] == "battle.main" and not self.interface == "battle.main.move":
                    # Botón derecho y que estemos en etapa de enfrentamiento
                    self.interface = "battle.main"
            elif event.type == p.KEYDOWN:
                pass

    # Dibujar texto en pantalla con fuente mediana
    def draw_text(self, text, pos, color, font="button", is_button=False, is_centered=False):
        """
        Función para mostrar texto en pantalla
        :param text: texto a mostrar
        :param pos: posición del texto en pantalla
        :param color: color de la fuente
        :param font: fuente a usar
        :param is_button: es botón o no
        :param is_centered: es centrado o no
        :return:
        """
        font = self.fonts[font]
        if color == BLACK:
            text_obj = font.render(text, False, p.Color(GREY))
        elif color == WHITE:
            text_obj = font.render(text, False, p.Color(PURPLE))
        else:
            text_obj = font.render(text, False, p.Color(GREY))
        if is_centered:
            text_loc = p.Rect((SCREEN_WIDTH / 2 - text_obj.get_width() / 2 + pos[0],
                               SCREEN_HEIGHT / 2 - text_obj.get_height() / 2 + pos[1],
                               text_obj.get_width(), text_obj.get_height()))
        else:
            text_loc = p.Rect((pos[0], pos[1], text_obj.get_width(), text_obj.get_height()))
        self.screen.blit(text_obj, text_loc)
        text_obj = font.render(text, False, p.Color(color))
        text_loc = text_loc.move(-2, -2)
        self.screen.blit(text_obj, text_loc)

        if is_button:
            self.buttons[text] = text_loc

    # Dibujar título en pantalla de inicio
    def draw_title(self):
        """
        Dibuja el título y subtitulo en la pantalla principal
        :return:
        """
        title_rect = p.Rect((50, 50, SCREEN_WIDTH-100, SCREEN_HEIGHT//3))
        p.draw.rect(self.screen, p.Color("white"), title_rect)
        p.draw.rect(self.screen, p.Color(BLACK), title_rect, 2)
        self.draw_text("Batallas Pokemon", (0, -120), BLACK, "title", is_centered=True)
        self.draw_text("By Julian Prieto", (0, -50), BLACK, "text", is_centered=True)

    # Dibujar pokemons a elegir en pantalla de inicio
    def draw_pokemons(self):
        """
        Dibuja los pokemon en la pantalla
        :return:
        """
        global choice_rect
        choice_rect = p.Rect((SCREEN_WIDTH - 768) / 2, SCREEN_HEIGHT, SCREEN_WIDTH - 96*2, 128)
        p.draw.rect(self.screen, p.Color("white"), choice_rect)
        p.draw.rect(self.screen, p.Color(BLACK), choice_rect, 2)
        p.draw.rect(self.screen, p.Color(BLACK), choice_rect, 2)
        for i, pok in enumerate(self.id_pokemons):
            self.screen.blit(self.images[pok], (128*i - 64 + (SCREEN_WIDTH - (self.images[pok].get_width()*6)) / 2,
                                                SCREEN_HEIGHT + 15))

    # Remarcar el pokemon elegido por el usuario
    def draw_highlight(self):
        """
        Dibuja un seleccionado al hacer clic
        :return:
        """
        w, h = self.choice[1], SCREEN_HEIGHT
        self.screen.blit(self.images["op"], (w, h))

    # Dibujar los botones de la pantalla inicial
    def draw_start_buttons(self):
        """
        Dibuja los botones en pantalla de inicio
        :return:
        """
        button_rect = (SCREEN_WIDTH / 2 - 70, SCREEN_HEIGHT / 2 + 110, 135, 80)
        p.draw.rect(self.screen, p.Color(BLUE), button_rect)
        p.draw.rect(self.screen, p.Color(YELLOW), button_rect, 8)
        p.draw.rect(self.screen, p.Color(DARK_GREY), button_rect, 5)
        self.draw_text("JUGAR", (0, 150), WHITE, is_button=True, is_centered=True)

        # aviso de que no se ha seleccionado ningún pokemon
        if not self.choice:
            self.draw_text("Selecciona un pokemon para continuar", (0, 210), p.Color("red"), "text", is_centered=True)
        else:
            self.draw_text(Pokemon(self.choice[0]).name.upper(), (0, 210), p.Color("red"), "text", is_centered=True)

    # Verificar eventos en la pantalla inicial
    def start_mouse_events(self, pos):
        """
        Controla que pokemon fue elegido por el user
        :return:
        """
        diff = 96
        if choice_rect.colliderect(pos[0], pos[1], 1, 1):
            if pos[0] // 128 == self.selected:
                self.selected = None
                self.choice = None
            else:
                self.selected = pos[0] // 128
                for i, x in enumerate(range(diff, diff + 128 * 6 + 1, 128)):
                    if x <= pos[0] <= x + 128:
                        self.choice = (self.id_pokemons[i], x)
                        break
        if self.buttons["JUGAR"].colliderect(pos[0], pos[1], 1, 1):
            if self.choice:
                self.interface = "battle.pre"

    # Manejar las pantallas de enfrentamiento
    def battle_stage(self):
        """
        Función principal de la pantalla de batalla
        :return:
        """
        global battle_rect
        battle_rect = p.Rect((0, 0, SCREEN_WIDTH, SCREEN_HEIGHT + PANEL_HEIGHT))  # Toda la pantalla
        self.screen.blit(self.images["battle_bg"], (0, 0))
        self.screen.blit(self.images["blue_bar"], (0, SCREEN_HEIGHT))

        if self.battle is None:
            #self.current_sprites = p.sprite.Group(SpritePokemon(self.choice[0]), SpritePokemon(self.enemy, True))
            self.user_sprite = SpritePokemon(1)
            self.cpu_sprite = SpritePokemon(7, True)
            self.current_sprites = p.sprite.Group(self.user_sprite, self.cpu_sprite)
            # self.battle = Battle(Pokemon(self.choice[0], wild=False), Pokemon(self.enemy, wild=True))
            self.battle = Battle(Pokemon(1, wild=False), Pokemon(7, wild=True))

        if self.interface == "battle.pre":
            self.battle_pre_stage()

        if self.interface.startswith("battle.main"):
            # Finalizado el movimiento, setear la posición a la final_pos
            self.user_sprite.update(self.user_sprite.final_x)
            self.cpu_sprite.update(self.cpu_sprite.final_x)
            self.current_sprites.draw(self.screen)

            self.battle_main_stage()

    # Manejar las pantallas de enfrentamiento (animación inicial)
    def battle_pre_stage(self):
        """
        Función encargada de la pantalla de presentación del enfrentamiento
        :return:
        """
        if not self.animation_made:
            self.draw_text(f"A PELEAR CONTRA {self.battle.enemy.name.upper()}!",
                           (50, SCREEN_HEIGHT + PANEL_HEIGHT / 4 - 10), WHITE)
            self.screen.blit(p.transform.rotate(self.images["mouse"], 45), (810, 480))
            self.sprite_animation(self.user_sprite, self.cpu_sprite)
            self.animation_made = True
            self.interface = "battle.main"

    # Mandar a animar ambos pokemon
    def sprite_animation(self, user, cpu):
        """
        Función principal para animar ambos sprites
        :param user: sprite user. Mueve hacia la derecha
        :param cpu: sprite cpu. Mueve hacia la izquierda
        :return:
        """
        # User animation (left tp right)
        delta_pos = abs(user.final_x - user.rect.x) // user.speed
        self.animation(user, delta_pos)
        # Cpu animation (right to left)
        delta_pos = abs(cpu.final_x - cpu.rect.x) // -cpu.speed
        self.animation(cpu, delta_pos)

    # Animar un pokemon
    def animation(self, sprite, delta):
        """
        Función para animar los sprites
        :param sprite: sprite a animar
        :param delta: movimiento deseado
        :return:
        """
        for frame in range(delta):
            sprite.rect.move_ip(sprite.speed, 0)
            self.screen.blit(self.images["battle_bg"], (0, 0))
            self.current_sprites.draw(self.screen)
            p.display.flip()
            self.clock.tick(FPS)

    # Manejar las pantallas de enfrentamiento (principal)
    def battle_main_stage(self):
        """
        Función encargada del enfrentamiento
        :return:
        """
        # Barra de opciones
        self.screen.blit(self.images["options_bar"],
                         (SCREEN_WIDTH - self.images["options_bar"].get_width(), SCREEN_HEIGHT))
        # Texto
        self.draw_text(F"QUE DEBERIA HACER", (50, SCREEN_HEIGHT + PANEL_HEIGHT / 4 - 10), WHITE)
        self.draw_text(F"{self.battle.ally.name.upper()}?", (50, SCREEN_HEIGHT + PANEL_HEIGHT / 2 + 10), WHITE)
        # Info aliado
        self.screen.blit(self.images["info_ally"], (SCREEN_WIDTH - self.images["options_bar"].get_width(),
                                                    SCREEN_HEIGHT - self.images["info_ally"].get_height() - 10))
        self.draw_text(self.battle.ally.name.upper(), (540, 300), BLACK)
        self.draw_text("Lv" + str(self.battle.ally.level), (800, 300), BLACK)
        self.draw_text(str(self.battle.ally.current_hp) + "/" + str(self.battle.ally.stats["hp"]), (760, 369), BLACK)
        # Info enemigo
        self.screen.blit(self.images["info_enemy"], (
            (SCREEN_WIDTH - self.images["options_bar"].get_width()) - self.images["info_enemy"].get_width(), 50))
        self.draw_text(self.battle.enemy.name.upper(), (104, 60), BLACK)
        self.draw_text("Lv" + str(self.battle.enemy.level), (364, 60), BLACK)

        # Botones
        self.draw_battle_buttons()

        # Vida y XP
        self.show_info()

        if self.interface == "battle.main.fight":
            self.show_attacks()

        if self.interface == "battle.main.move":
            turn = self.battle.get_turn()
            first = self.battle.ally if turn else self.battle.enemy
            second = self.battle.ally if not turn else self.battle.enemy
            self.show_move(turn, first, second)

        elif self.interface == "battle.main.bag":
            print("MOCHILA")

        elif self.interface == "battle.main.pokemon":
            print("POKEMON")

    # Mostrar y actualizar la experiencia del usuario y la vida del usuario y oponente
    def show_info(self):
        """
        Actualiza la vida y experiencia mostradas en pantalla
        """
        xp = self.battle.ally.current_xp * 256 // self.battle.ally.xp_next_level
        xp_rect = p.Rect((608, 422, xp, 8))
        p.draw.rect(self.screen, p.Color(XP_COLOR), xp_rect)
        hp = self.battle.ally.current_hp * 196 // self.battle.ally.stats["hp"]
        hp_ally_rect = p.Rect((668, 358, hp, 12))
        p.draw.rect(self.screen, p.Color(HP_COLOR), hp_ally_rect)
        hp = self.battle.enemy.current_hp * 196 // self.battle.enemy.stats["hp"]
        hp_ally_rect = p.Rect((232, 118, hp, 12))
        p.draw.rect(self.screen, p.Color(HP_COLOR), hp_ally_rect)

    def show_attacks(self):
        self.screen.blit(self.images["fight"], (0, SCREEN_HEIGHT))
        x, y, z = 60, 4, -10
        for i in range(len(self.battle.ally.move)):
            self.draw_text(self.battle.ally.move[i].stats["name"].upper(),
                           (x, SCREEN_HEIGHT + PANEL_HEIGHT / y + z), BLACK, is_button=True)
            if i + 1 == 1 or i + 1 == 3:
                x = 340
            elif i + 1 == 2:
                x, y, z = 60, 2, 10

    def show_move(self, turn, first, second):

        if not self.battle.first_move_made:
            self.screen.blit(self.images["blue_bar"], (0, SCREEN_HEIGHT))
            move = self.ally_move if turn else self.enemy_move
            wild = "enemigo " if first.wild else ""
            self.draw_text(f"{first.name.upper()} {wild}usó ", (50, SCREEN_HEIGHT + PANEL_HEIGHT / 4 - 10), WHITE)
            self.draw_text(move.stats["name"].upper() + "!", (50, SCREEN_HEIGHT + PANEL_HEIGHT / 2 + 10), WHITE)
            self.battle.make_move(second, move)
        elif self.battle.first_move_made:
            self.screen.blit(self.images["blue_bar"], (0, SCREEN_HEIGHT))
            move = self.ally_move if not turn else self.enemy_move
            wild = "enemigo " if second.wild else ""
            self.draw_text(f"{second.name.upper()} {wild}usó ", (50, SCREEN_HEIGHT + PANEL_HEIGHT / 4 - 10), WHITE)
            self.draw_text(move.stats["name"].upper() + "!", (50, SCREEN_HEIGHT + PANEL_HEIGHT / 2 + 10), WHITE)
            self.battle.make_move(first, move)

    # Dibujar los botones en las pantallas de enfrentamiento
    def draw_battle_buttons(self):
        option_bar_width = self.images["options_bar"].get_width()
        self.draw_text("LUCHA",
                       (SCREEN_WIDTH - option_bar_width + 60,
                        SCREEN_HEIGHT + PANEL_HEIGHT / 4 - 10), BLACK, is_button=True)
        self.draw_text("MOCHILA",
                       (SCREEN_WIDTH - option_bar_width / 2.5,
                        SCREEN_HEIGHT + PANEL_HEIGHT / 4 - 10), BLACK, is_button=True)
        self.draw_text("POKEMON",
                       (SCREEN_WIDTH - option_bar_width + 60,
                        SCREEN_HEIGHT + PANEL_HEIGHT / 2 + 10), BLACK, is_button=True)
        self.draw_text("HUIR",
                       (SCREEN_WIDTH - option_bar_width / 2.5,
                        SCREEN_HEIGHT + PANEL_HEIGHT / 2 + 10), BLACK, is_button=True)

    # Verificar los eventos en las pantallas de enfrentamiento
    def battle_mouse_events(self, pos):
        """
        Encargada de los eventos del mouse en la pantalla de enfrentamiento
        :param pos:
        :return:
        """
        if self.interface == "battle.main":
            buttons = {"LUCHA": "battle.main.fight",
                       "MOCHILA": "battle.main.bag",
                       "POKEMON": "battle.main.pokemon",
                       "HUIR": None}
            for button, interface in buttons.items():
                if self.buttons[button].colliderect(pos[0], pos[1], 1, 1):
                    if interface is not None:
                        self.interface = interface
                    else:
                        if self.battle.can_run():
                            self.running = False

        elif self.interface == "battle.main.move":
            if battle_rect.colliderect(pos[0], pos[1], 1, 1):
                if not self.battle.first_move_made and self.battle.active:
                    self.battle.first_move_made = True
                    self.battle.move_made = False
                elif self.battle.first_move_made and self.battle.active:
                    self.battle.first_move_made = False
                    self.battle.move_made = False
                    self.interface = "battle.main"
                elif not self.battle.active:
                    self.interface = "battle.main"

        elif self.interface == "battle.main.fight":
            moves = self.battle.ally.move
            for move in moves:
                if self.buttons[move.stats["name"].upper()].colliderect(pos[0], pos[1], 1, 1):
                    self.ally_move = move
                    self.enemy_move = random.choice(self.battle.enemy.move)
                    self.interface = "battle.main.move"

    def handle_interface(self, interface):
        if interface == "start":
            self.draw_title()
            self.draw_pokemons()
            self.draw_start_buttons()
            if self.choice:
                self.draw_highlight()
        if interface.startswith("battle"):
            self.battle_stage()

    # Función Principal
    def main(self):
        """
        Función principal del juego
        :return:
        """
        p.init()
        p.display.set_caption(TITLE)
        self.load_images()
        self.load_fonts()
        while self.running:
            self.screen.fill(GREY)
            self.check_events()
            self.handle_interface(self.interface)
            self.clock.tick(FPS)
            p.display.flip()
