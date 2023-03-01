from settings_ import *
from engine_ import Pokemon, Battle
import pygame as p
import random
import numpy as np

global choice_rect
global battle_rect
global play_rect


class SpritePokemon(p.sprite.Sprite):
    def __init__(self, nro, front_view=False):
        p.sprite.Sprite.__init__(self)
        self.id_pokemons_array = np.arange(1, 505).reshape(18, 28)
        pos = np.where(self.id_pokemons_array == nro)
        c = pos[0][0]
        r = pos[1][0]
        if front_view:  # Imagen de frente (oponente)
            self.image = p.image.load(DIR+SPRITES+"sprites_front.png")
            h = c * self.image.get_width() / 28
            w = r * self.image.get_height() / 18
            self.image = self.image.subsurface((w, h, 80, 80))
            self.image = p.transform.scale(self.image, (256, 256))
            self.rect = self.image.get_rect()
            self.rect.x = SCREEN_WIDTH + 4
            self.rect.centery = SCREEN_HEIGHT / 2.5
            self.final_pos = (SCREEN_WIDTH - self.image.get_width() - 100, self.rect.centery)
            self.speed = -30

        else:  # Imagen de atrás (aliado)
            self.image = p.image.load(DIR+SPRITES+"sprites_back.png")
            h = c * self.image.get_width() / 28
            w = r * self.image.get_height() / 18
            self.image = self.image.subsurface((w, h, 80, 80))
            self.image = p.transform.scale(self.image, (256, 256))
            self.rect = self.image.get_rect()
            self.rect.x = -self.image.get_width() - 4
            self.rect.centery = SCREEN_HEIGHT - (self.image.get_height() / 2)
            self.final_pos = (100, self.rect.centery)
            self.speed = 30
        if not front_view:
            self.pokemon = Pokemon(nro, False)
        else:
            self.pokemon = Pokemon(nro)

    def update(self, pos):
        self.rect.x = pos


class Game:
    def __init__(self):
        # Display
        p.init()
        self.running = True
        self.clock = p.time.Clock()
        self.screen = p.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT + PANEL_HEIGHT))
        self.title_font = p.font.Font(DIR+GUI+"font.ttf", 100)
        self.button_font = p.font.Font(DIR+GUI+"font.ttf", 64)
        self.text_font = p.font.Font(DIR+GUI+"font.ttf", 32)
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

    def load_images(self):
        """
        Carga de imagenes general
        :return:
        """
        # Start
        self.images["ss"] = p.image.load(DIR + SPRITES + "spritesheet.png").convert_alpha()
        for nro in self.id_pokemons:
            pos = np.where(self.id_pokemons_array == nro)
            col = pos[0][0]
            row = pos[1][0]
            h = col * self.images["ss"].get_width() / 28
            w = row * self.images["ss"].get_height() / 18
            self.images[nro] = self.images["ss"].subsurface((w, h, 100, 100))
        self.images["op"] = p.image.load(DIR+GUI+"option.png")
        self.images["op"].set_alpha(120)

        # Battle
        self.images["battle_bg"] = p.image.load(DIR + GUI + "battle_bg.png")
        self.images["blue_bar"] = p.image.load(DIR+GUI+"blue_bar.png")
        self.images["options_bar"] = p.image.load(DIR+GUI+"options_bar.png")
        self.images["mouse"] = p.image.load(DIR+GUI+"mouse.png")
        self.images["info_ally"] = p.image.load(DIR+GUI+"info_ally.png")
        self.images["info_enemy"] = p.image.load(DIR + GUI + "info_enemy.png")
        self.images["fight"] = p.image.load(DIR + GUI + "fight.png")

    def check_events(self):
        """
        Verifica eventos
        :return:
        """
        for event in p.event.get():
            if event.type == p.QUIT:
                self.running = False
            elif event.type == p.MOUSEBUTTONDOWN:
                pos = p.mouse.get_pos()
                if event.dict["button"] == 1:
                    # Boton izquierdo
                    if self.interface == "start":
                        self.start_mouse_events(pos)
                    elif self.interface[0:6] == "battle":
                        self.battle_mouse_events(pos)
                elif event.dict["button"] == 3 and self.interface[:11] == "battle.main":
                    # Boton derecho y que estemos en etapa de enfrentamiento
                    self.interface = "battle.main"
            elif event.type == p.KEYDOWN:
                pass

    def draw_title(self):
        """
        Dibuja el titulo y subtitulo en la pantalla principal
        :return:
        """
        # Titulo
        title_obj = self.title_font.render("Batallas Pokemon", False, GREY)
        title_loc = p.Rect((0, 0, SCREEN_WIDTH, SCREEN_HEIGHT / 3)).move(
            SCREEN_WIDTH / 2 - title_obj.get_width() / 2, SCREEN_HEIGHT / 3 / 2 - title_obj.get_height() / 2)
        title_rect = p.Rect((SCREEN_WIDTH / 2 - title_obj.get_width() / 2 - 50,
                             SCREEN_HEIGHT / 3 / 2 - title_obj.get_height() / 2,
                             title_obj.get_width() + 100, title_obj.get_height() + 70))
        p.draw.rect(self.screen, p.Color("white"), title_rect)
        p.draw.rect(self.screen, p.Color(BLACK), title_rect, 2)
        self.screen.blit(title_obj, title_loc)
        title_obj = self.title_font.render("Batallas Pokemon", False, BLACK)
        title_loc = title_loc.move(-3, -3)
        self.screen.blit(title_obj, title_loc)
        # Subtitulo
        sub_obj = self.text_font.render("By JuliPrieto", False, GREY)
        sub_loc = p.Rect((0, title_obj.get_height(), SCREEN_WIDTH, SCREEN_HEIGHT / 3)).move(
            SCREEN_WIDTH / 2 - sub_obj.get_width() / 2, SCREEN_HEIGHT / 3 / 2 - sub_obj.get_height() / 2)
        self.screen.blit(sub_obj, sub_loc)
        sub_obj = self.text_font.render("By JuliPrieto", False, BLACK)
        sub_loc = sub_loc.move(-2, -2)
        self.screen.blit(sub_obj, sub_loc)

    def draw_start_buttons(self):
        """
        Dibuja los botones en pantalla de inicio
        :return:
        """
        p.draw.rect(self.screen, p.Color(BLUE), (SCREEN_WIDTH / 2 - 70,
                                                 SCREEN_HEIGHT / 2 + 110,
                                                 135, 80))
        p.draw.rect(self.screen, p.Color(YELLOW), (SCREEN_WIDTH / 2 - 70,
                                                   SCREEN_HEIGHT / 2 + 110,
                                                   135, 80), 8)
        p.draw.rect(self.screen, p.Color(DARK_GREY), (SCREEN_WIDTH / 2 - 70,
                                                      SCREEN_HEIGHT / 2 + 110,
                                                      135, 80), 5)
        self.draw_text("JUGAR", (0, 150), WHITE, is_button=True, is_centered=True)

        # aviso de que no se ha seleccionado ningun pokemon
        if not self.choice:
            warning_obj = self.text_font.render("Selecciona un pokemon para continuar", False, p.Color("red"))
            warning_loc = p.Rect(SCREEN_WIDTH / 2 - warning_obj.get_width() / 2,
                                 SCREEN_HEIGHT - warning_obj.get_height() - 5,
                                 warning_obj.get_width(), warning_obj.get_height())
            self.screen.blit(warning_obj, warning_loc)
        else:
            warning_obj = self.text_font.render(Pokemon(self.choice[0]).name.upper(), False, p.Color(GREY))
            warning_loc = p.Rect(SCREEN_WIDTH / 2 - warning_obj.get_width() / 2,
                                 SCREEN_HEIGHT - warning_obj.get_height() - 5,
                                 warning_obj.get_width(), warning_obj.get_height())
            self.screen.blit(warning_obj, warning_loc)
            warning_obj = self.text_font.render(Pokemon(self.choice[0]).name.upper(), False, p.Color(BLACK))
            warning_loc = warning_loc.move(-2, -2)
            self.screen.blit(warning_obj, warning_loc)

    def draw_battle_buttons(self):
        self.draw_text("LUCHA",
                       (SCREEN_WIDTH - self.images["options_bar"].get_width() + 60,
                        SCREEN_HEIGHT + PANEL_HEIGHT / 4 - 10), BLACK, is_button=True)
        self.draw_text("MOCHILA",
                       (SCREEN_WIDTH - self.images["options_bar"].get_width() / 2.5,
                        SCREEN_HEIGHT + PANEL_HEIGHT / 4 - 10), BLACK, is_button=True)
        self.draw_text("POKEMON",
                       (SCREEN_WIDTH - self.images["options_bar"].get_width() + 60,
                        SCREEN_HEIGHT + PANEL_HEIGHT / 2 + 10), BLACK, is_button=True)
        self.draw_text("HUIR",
                       (SCREEN_WIDTH - self.images["options_bar"].get_width() / 2.5,
                        SCREEN_HEIGHT + PANEL_HEIGHT / 2 + 10), BLACK, is_button=True)

    def draw_pokemons(self):
        """
        Dibuja los pokemones en la pantalla
        :return:
        """
        global choice_rect
        choice_rect = p.Rect((SCREEN_WIDTH - 768) / 2, SCREEN_HEIGHT, SCREEN_WIDTH - 96*2, 128)
        p.draw.rect(self.screen, p.Color("white"), choice_rect)
        p.draw.rect(self.screen, p.Color(BLACK), choice_rect, 2)
        p.draw.rect(self.screen, p.Color(BLACK), choice_rect, 2)
        for pok, i in zip(self.id_pokemons, range(0, len(self.id_pokemons))):
            self.screen.blit(self.images[pok], (128*i - 64 + (SCREEN_WIDTH - (self.images[pok].get_width()*6)) / 2,
                                                SCREEN_HEIGHT + 15))

    def draw_text(self, text, pos, color, is_button=False, is_centered=False):
        """
        Funcion para mostrar texto en pantalla
        :param text: texto a mostrar
        :param pos: posicion del texto en pantalla
        :param color: color de la fuente
        :param is_button: es boton o no
        :param is_centered: es centrado o no
        :return:
        """
        if color == BLACK:
            text_obj = self.button_font.render(text, False, p.Color(GREY))
        elif color == WHITE:
            text_obj = self.button_font.render(text, False, p.Color(PURPLE))
        else:
            return
        if is_centered:
            text_loc = p.Rect((SCREEN_WIDTH / 2 - text_obj.get_width() / 2 + pos[0],
                               SCREEN_HEIGHT / 2 - text_obj.get_height() / 2 + pos[1],
                               text_obj.get_width(), text_obj.get_height()))
        else:
            text_loc = p.Rect((pos[0], pos[1], text_obj.get_width(), text_obj.get_height()))
        self.screen.blit(text_obj, text_loc)
        text_obj = self.button_font.render(text, False, p.Color(color))
        text_loc = text_loc.move(-2, -2)
        self.screen.blit(text_obj, text_loc)

        if is_button:
            self.buttons[text] = text_loc

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
                if diff <= pos[0] <= diff + 128:
                    self.choice = (self.id_pokemons[0], diff)
                elif diff + 128 <= pos[0] <= diff + 128*2:
                    self.choice = (self.id_pokemons[1], diff + 128 * 1)
                elif diff + 128*2 <= pos[0] <= diff + 128*3:
                    self.choice = (self.id_pokemons[2], diff + 128 * 2)
                elif diff + 128*3 <= pos[0] <= diff + 128*4:
                    self.choice = (self.id_pokemons[3], diff + 128 * 3)
                elif diff + 128*4 <= pos[0] <= diff + 128*5:
                    self.choice = (self.id_pokemons[4], diff + 128 * 4)
                elif diff + 128*5 <= pos[0] <= diff + 128*6:
                    self.choice = (self.id_pokemons[5], diff + 128 * 5)

        if self.buttons["JUGAR"].colliderect(pos[0], pos[1], 1, 1):
            if self.choice:
                self.interface = "battle.pre"

    def battle_mouse_events(self, pos):
        """
        Encargada de los eventos del mouse en la pantalla de enfrentamiento
        :param pos:
        :return:
        """
        if self.interface == "battle.pre":
            if battle_rect.colliderect(pos[0], pos[1], 1, 1):
                self.interface = "battle.main"

        elif self.interface == "battle.main.move":
            if battle_rect.colliderect(pos[0], pos[1], 1, 1):
                if self.battle.first_move_made:
                    self.interface = "battle.main"
                    self.battle.first_move_made = False
                    self.battle.move_made = False
                    if self.battle.ally.current_hp == 0 or self.battle.enemy.current_hp == 0:
                        self.battle.end_combat()
                else:
                    self.battle.first_move_made = True
                    self.battle.move_made = False
                    if self.battle.ally.current_hp == 0 or self.battle.enemy.current_hp == 0:
                        self.battle.end_combat()

        elif self.interface == "battle.main":
            if self.buttons["LUCHA"].colliderect(pos[0], pos[1], 1, 1):
                self.interface = "battle.main.fight"

            elif self.buttons["MOCHILA"].colliderect(pos[0], pos[1], 1, 1):
                self.interface = "battle.main.bag"

            elif self.buttons["POKEMON"].colliderect(pos[0], pos[1], 1, 1):
                self.interface = "battle.main.pokemon"

            elif self.buttons["HUIR"].colliderect(pos[0], pos[1], 1, 1):
                if self.battle.can_run():
                    print(f"{self.battle.ally.name.capitalize()} a huido!")
                    self.running = False
                else:
                    print(f"{self.battle.ally.name.capitalize()} no ha podido huir!!")

        elif self.interface == "battle.main.fight":
            moves = self.battle.ally.move
            for move in moves:
                if self.buttons[move.name.upper()].colliderect(pos[0], pos[1], 1, 1):
                    self.ally_move = move
                    self.enemy_move = random.choice(self.battle.enemy.move)
                    self.interface = "battle.main.move"

    def draw_highlight(self):
        """
        Dibuja un seleccionado al hacer click
        :return:
        """
        w = self.choice[1]
        h = SCREEN_HEIGHT
        self.screen.blit(self.images["op"], (w, h))

    def sprite_animation(self, user, cpu):
        """
        Funcion principal para animar ambos sprites
        :param user: sprite user. Mueve hacia la derecha
        :param cpu: sprite cpu. Mueve hacia la izquierda
        :return:
        """
        # User animation (left tp right)
        delta_pos = abs(user.final_pos[0] - user.rect.x) // user.speed
        self.animation(user, delta_pos)
        # Cpu animation (right to left)
        delta_pos = abs(cpu.final_pos[0] - cpu.rect.x) // -cpu.speed
        self.animation(cpu, delta_pos)

    def animation(self, sprite, delta):
        """
        Funcion para animar los sprites
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

    def battle_stage(self):
        """
        Funcion principal de la pantalla de batalla
        :return:
        """
        global battle_rect
        battle_rect = p.Rect((0, 0, SCREEN_WIDTH, SCREEN_HEIGHT + PANEL_HEIGHT))  # Toda la pantalla
        self.screen.blit(self.images["battle_bg"], (0, 0))
        self.screen.blit(self.images["blue_bar"], (0, SCREEN_HEIGHT))
        if not self.battle:
            self.user_sprite = SpritePokemon(self.choice[0])
            self.cpu_sprite = SpritePokemon(self.enemy, True)
            self.current_sprites = p.sprite.Group(self.user_sprite, self.cpu_sprite)
            self.battle = Battle(Pokemon(self.choice[0], wild=False), Pokemon(self.enemy, wild=True))

        if self.interface == "battle.pre":
            self.battle_pre_stage()
        # Finalizado el movimiento, setear la posicion a la final_pos
        self.user_sprite.update(self.user_sprite.final_pos[0])
        self.cpu_sprite.update(self.cpu_sprite.final_pos[0])
        self.current_sprites.draw(self.screen)

        if self.interface[0:11] == "battle.main":
            self.battle_main_stage()

    def battle_pre_stage(self):
        """
        Funcion encargada de la pantalla de presentacion del enfrentamiento
        :return:
        """
        self.draw_text(F"A PELEAR CONTRA {self.battle.enemy.name.upper()} !",
                       (50, SCREEN_HEIGHT + PANEL_HEIGHT / 4 - 10), WHITE)
        self.screen.blit(p.transform.rotate(self.images["mouse"], 45), (810, 480))
        if not self.animation_made:
            self.sprite_animation(self.user_sprite, self.cpu_sprite)
            self.animation_made = True

    def battle_main_stage(self):
        """
        Funcion encargada del enfrentamiento
        :return:
        """
        # Texto
        self.screen.blit(self.images["options_bar"],
                         (SCREEN_WIDTH - self.images["options_bar"].get_width(), SCREEN_HEIGHT))
        self.draw_text(F"QUE DEBERIA HACER", (50, SCREEN_HEIGHT + PANEL_HEIGHT / 4 - 10), WHITE)
        self.draw_text(F"{self.battle.ally.name.upper()} ?", (50, SCREEN_HEIGHT + PANEL_HEIGHT / 2 + 10), WHITE)
        self.screen.blit(self.images["info_ally"], (SCREEN_WIDTH - self.images["options_bar"].get_width(),
                                                    SCREEN_HEIGHT - self.images["info_ally"].get_height() - 10))
        self.draw_text(self.battle.ally.name.upper(), (540, 300), BLACK)
        self.draw_text("Lv" + str(self.battle.ally.level), (800, 300), BLACK)
        self.draw_text(str(self.battle.ally.current_hp) + "/" + str(self.battle.ally.hp), (760, 369), BLACK)
        self.screen.blit(self.images["info_enemy"], (
            (SCREEN_WIDTH - self.images["options_bar"].get_width()) - self.images["info_enemy"].get_width(), 50))
        self.draw_text(self.battle.enemy.name.upper(), (104, 60), BLACK)
        self.draw_text("Lv" + str(self.battle.enemy.level), (364, 60), BLACK)
        # Botones
        self.draw_battle_buttons()

        # Vida y XP
        ############

        if self.interface == "battle.main.fight":
            self.screen.blit(self.images["fight"], (0, SCREEN_HEIGHT))
            x, y, z = 60, 4, -10
            for i in range(len(self.battle.ally.move)):
                self.draw_text(self.battle.ally.move[i].name.upper(),
                               (x, SCREEN_HEIGHT + PANEL_HEIGHT / y + z), BLACK, is_button=True)
                if i + 1 == 1 or i + 1 == 3:
                    x = 340
                elif i + 1 == 2:
                    x, y, z = 60, 2, 10

        if self.interface == "battle.main.move":
            turn = self.battle.get_turn()
            first = self.battle.ally if turn else self.battle.enemy
            second = self.battle.ally if not turn else self.battle.enemy

            if not self.battle.first_move_made:
                self.screen.blit(self.images["blue_bar"], (0, SCREEN_HEIGHT))
                move = self.ally_move if turn else self.enemy_move
                self.draw_text(f"{first.name.upper()} usó {move.name.upper()}", (50, SCREEN_HEIGHT + PANEL_HEIGHT / 4 - 10), WHITE)
                self.battle.make_move(second, move)
            else:
                self.screen.blit(self.images["blue_bar"], (0, SCREEN_HEIGHT))
                move = self.ally_move if not turn else self.enemy_move
                self.draw_text(f"{second.name.upper()} usó {move.name.upper()}", (50, SCREEN_HEIGHT + PANEL_HEIGHT / 4 - 10), WHITE)
                self.battle.make_move(first, move)

        elif self.interface == "battle.main.bag":
            print("MOCHILA")

        elif self.interface == "battle.main.pokemon":
            print("POKEMON")

    def main(self):
        """
        Funcion principal del juego
        :return:
        """
        p.display.set_caption(TITLE)
        self.load_images()
        while self.running:
            self.screen.fill(GREY)
            self.check_events()
            if self.interface == "start":
                self.draw_title()
                self.draw_pokemons()
                self.draw_start_buttons()
                if self.choice:
                    self.draw_highlight()
            if self.interface[0:6] == "battle":
                self.battle_stage()
                if not self.battle.active:
                    p.time.wait(5000)
                    self.running = False
                    #self.interface = "battle.main"

            self.clock.tick(FPS)
            p.display.flip()







