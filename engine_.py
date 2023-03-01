import random
import sqlite3
import numpy as np
import math
from settings_ import *


class Move:
    """
    Clase Movimientos
    """
    def __init__(self, _id):
        # Database
        self.db = sqlite3.connect(DIR + "pokemon_database.sqlite")
        self.cursor = self.db.cursor()
        # Stats
        self.id = _id
        self.name, self.type_id, self.power, self.pp, self.accuracy, \
            self.id_category, self.effect_id, self.effect_chance = self.get_move_stats()
        if not self.effect_chance:
            self.effect_chance = 100
        self.effect = self.get_effect_info()
        self.variation = random.randint(85, 100)
        self.critic_chance_index = 0.0625  # 0 Implementar indices para las chances de critico

    def get_move_stats(self):
        """
        Obtiene los stats del movimiento correspondiente de la base de datos
        :return:
        """
        self.cursor.execute(
            f"SELECT identifier, type_id, power, pp, accuracy, damage_class_id, effect_id, effect_chance "
            f"FROM moves WHERE id = {self.id}")
        stats = self.cursor.fetchall()[0]
        return stats

    def get_effect_info(self):
        """
        Obtiene la informacion de efecto del movimiento correspondiente
        :return:
        """
        self.cursor.execute(f"SELECT short_effect FROM move_effect_prose "
                            f"WHERE local_language_id = 9 AND move_effect_id = {self.effect_id}")
        return self.cursor.fetchall()[0][0].replace("regular damage", str(self.power))


class Pokemon:
    """
    Clase Pokemon
    """
    def __init__(self, nro, wild=True):
        # Info
        self.nro = nro
        self.wild = wild
        self.db = sqlite3.connect(DIR + "pokemon_database.sqlite")
        self.cursor = self.db.cursor()
        self.name = self.get_name()
        self.id_type = self.get_id_types()
        self.id_moves = self.get_id_moves()
        self.move = [Move(10), Move(random.choice(self.id_moves)), Move(254), Move(1)]  # Variable temporal
        # Base Stats
        self.base_xp = self.get_base_xp()
        self.base_hp, self.base_attack, self.base_defense, self.base_special_attack, \
            self.base_special_defense, self.base_speed, self.ev, self.growth_rate = self.get_base_stats()
        self.iv = np.random.randint(0, 32, size=6)
        self.current_id_moves = random.choices(self.id_moves, k=2)
        # Stats
        self.nature_stats = self.get_nature()
        self.level = 5
        self.xp_next_level = self.get_xp_growth_rate() - self.get_xp_growth_rate(self.level)
        self.current_xp = 0
        self.hp = self.get_stat(self.base_hp, self.iv[0], self.ev[0], hp=True)
        self.attack = self.get_stat(self.base_attack, self.iv[1], self.ev[1], self.nature_stats["attack"])
        self.defense = self.get_stat(self.base_defense, self.iv[2], self.ev[2], self.nature_stats["defense"])
        self.special_attack = self.get_stat(self.base_special_attack, self.iv[3], self.ev[3], self.nature_stats["sp_attack"])
        self.special_defense = self.get_stat(self.base_special_defense, self.iv[4], self.ev[4], self.nature_stats["sp_defense"])
        self.speed = self.get_stat(self.base_speed, self.iv[5], self.ev[5], self.nature_stats["speed"])
        self.accuracy = 1
        self.evasion = 1
        self.current_hp = self.hp

        self.db.close()

    def get_name(self):
        """
        Obtiene el nombre del pokemon segun su numero de la pokedex nacional
        :return: str
        """
        self.cursor.execute(f"SELECT identifier FROM pokemon WHERE id = {self.nro}")
        dt = self.cursor.fetchall()
        return dt[0][0]

    def get_id_types(self):
        """
        Obtiene los id del tipo de pokemon
        :return: list --> (int, ...)
        """
        types = []
        self.cursor.execute(f"SELECT type_id FROM pokemon_types WHERE pokemon_id = {self.nro}")
        id_types = self.cursor.fetchall()
        for i in range(len(id_types)):
            id_type = id_types[i][0]
            types.append(id_type)
        return types

    def get_id_moves(self):
        """
        Obtiene una lista de los id de los movimientos disponibles para el pokemon
        :return: list --> (int, ...)
        """
        moves = []
        self.cursor.execute(
            f"SELECT move_id FROM pokemon_moves WHERE pokemon_id = {self.nro} AND pokemon_move_method_id = 1 AND version_group_id = 10")
        id_moves = self.cursor.fetchall()
        for i in range(len(id_moves)):
            id_move = id_moves[i][0]
            moves.append(id_move)
        return moves

    def get_base_xp(self):
        """
        Obtiene la experiencia base del pokemon
        :return: int
        """
        self.cursor.execute(f"SELECT base_experience FROM pokemon WHERE id = {self.nro}")
        xp = self.cursor.fetchall()[0][0]
        return xp

    def get_base_stats(self):
        """
        Obtiene las stats bases del pokemon
        :return: int*8
        """
        self.cursor.execute(f"SELECT base_stat, effort FROM pokemon_stats WHERE pokemon_id ={self.nro}")
        stats = self.cursor.fetchall()
        hp = stats[0][0]
        attack = stats[1][0]
        defense = stats[2][0]
        sp_attack = stats[3][0]
        sp_defense = stats[4][0]
        speed = stats[5][0]
        ev = [stats[0][1], stats[1][1], stats[2][1], stats[3][1], stats[4][1], stats[5][1]]
        self.cursor.execute(f"SELECT growth_rate_id FROM pokemon_species WHERE id = {self.nro}")
        growth_rate_id = self.cursor.fetchall()[0][0]
        return hp, attack, defense, sp_attack, sp_defense, speed, ev, growth_rate_id

    def get_nature(self):
        """
        Obtiene la naturaleza del pokemon (aleatoria)
        :return: dict --> {str: int}
        """
        nature = {}
        id_nature = random.randint(1, 25)
        self.cursor.execute(f"SELECT identifier, decreased_stat_id, increased_stat_id FROM natures WHERE id = {id_nature}")
        nature_info = self.cursor.fetchall()[0]
        nature["name"] = nature_info[0]
        decreased_stat_id = nature_info[1]
        increased_stat_id = nature_info[2]
        stats = ["attack", "defense", "sp_attack", "sp_defense", "speed"]
        for stat, name in zip(range(2, 7), stats):
            if stat == decreased_stat_id and stat != increased_stat_id:
                nature[name] = 0.9
            elif stat == increased_stat_id:
                nature[name] = 1.1
            else:
                nature[name] = 1
        return nature

    def get_xp_growth_rate(self, lvl=None):
        """
        Calcula la experiencia necesaria para llegar al siguiente nivel (o  aun nivel n)
        :param lvl: Nivel a calcular
        :return: int
        """
        def p(i):
            x = 0 if i == 0 else 0.008 if i == 1 else 0.014
            return x

        n = self.level + 1 if not lvl else lvl

        match self.growth_rate:
            case 1:
                xp = (5 * (n ** 3)) / 4
            case 2:
                xp = n ** 3
            case 3:
                xp = (4 * (n ** 3)) / 5
            case 4:
                xp = (1.2 * (n ** 3)) - (15 * (n ** 2)) + 100 * n - 140
            case 5:
                if 0 < n <= 50:
                    xp = (n ** 3) * (2 - 0.02 * n)
                elif 51 <= n <= 68:
                    xp = (n ** 3) * (1.5 - 0.01 * n)
                elif 69 <= n <= 98:
                    xp = (n ** 3) * (1.274 - 0.02 * (n / 3) - p(n % 3))
                else:
                    xp = (n ** 3) * (1.6 - 0.01 * n)
            case 6:
                if 0 < n <= 15:
                    xp = (n ** 3) * (24 + (n + 1) / 3) / 50
                elif 16 <= n <= 35:
                    xp = (n ** 3) * (14 + n) / 50
                else:
                    xp = (n ** 3) * (32 + (n / 2)) / 50

        return math.floor(xp)

    def get_stat(self, base, iv, ev, nature=None, hp=False):
        """
        Obtiene las estadisticas del pokemon segun su nivel, naturaleza, iv, y ev
        :param base: estadistica base
        :param iv: fortalezas individuales (individual values)
        :param ev: puntos de esfuerzo (effort values)
        :param nature: naturaleza
        :param hp: flag. el hp se calcula de manera distinta al resto de estadisticas
        :return: int
        """
        if hp:
            return math.floor((((2*base)+iv+(ev/4)*self.level)/100)+self.level+10)
        else:
            return math.floor((((((2*base)+iv+(ev/4))*self.level)/100)+5)*nature)


class Battle:
    def __init__(self, ally, enemy):
        self.ally = ally
        self.enemy = enemy
        self.active = True
        self.ally_turn = True if self.ally.speed >= self.enemy.speed else False  # Determina de quien es el turno. En un inicio, ataca el pokemon mas rapido
        self.change = True  # Posibilidad de "ally" de cambiar de pokemon
        self.attempts_run = 0
        self.place = None  # Por el momentos el campo de batalla en es mismo (Hierba Alta)
        self.effect_chart = np.array([
            [1, 1, 1, 1, 1, .5, 1, 0, .5, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [2, 1, .5, .5, 1, 2, .5, 0, 2, 1, 1, 1, 1, .5, 2, 1, 2, .5],
            [1, 2, 1, 1, 1, .5, 2, 1, .5, 1, 1, 2, .5, 1, 1, 1, 1, 1],
            [1, 1, 1, .5, .5, .5, 1, .5, 0, 1, 1, 2, 1, 1, 1, 1, 1, 2],
            [1, 1, 0, 2, 1, 2, .5, 1, 2, 2, 1, .5, 2, 1, 1, 1, 1, 1],
            [1, .5, 2, 1, .5, 1, 2, 1, .5, 2, 1, 1, 1, 1, 2, 1, 1, 1],
            [1, .5, .5, .5, 1, 1, 1, .5, .5, .5, 1, 2, 1, 2, 1, 1, 2, .5],
            [0, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, .5, 1],
            [1, 1, 1, 1, 1, 2, 1, 1, .5, .5, .5, 1, .5, 1, 2, 1, 1, 2],
            [1, 1, 1, 1, 1, .5, 2, 1, 2, .5, .5, 2, 1, 1, 2, .5, 1, 1],
            [1, 1, 1, 1, 2, 2, 1, 1, 1, 2, .5, .5, 1, 1, 1, .5, 1, 1],
            [1, 1, .5, .5, 2, 2, .5, 1, .5, .5, 2, .5, 1, 1, 1, .5, 1, 1],
            [1, 1, 2, 1, 0, 1, 1, 1, 1, 1, 2, .5, .5, 1, 1, .5, 1, 1],
            [1, 2, 1, 2, 1, 1, 1, 1, .5, 1, 1, 1, 1, .5, 1, 1, 0, 1],
            [1, 1, 2, 1, 2, 1, 1, 1, .5, .5, .5, 2, 1, 1, .5, 2, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, .5, 1, 1, 1, 1, 1, 1, 2, 1, 0],
            [1, .5, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, .5, .5],
            [1, 2, 1, .5, 1, 1, 1, 1, .5, .5, 1, 1, 1, 1, 1, 2, 2, 1]])
        self.first_move_made = False
        self.move_made = False

    def get_turn(self):
        """
        Calcula quien ataca primero en el primer movimiento
        :return:
        """
        return True if self.ally.speed >= self.enemy.speed else False

    def can_run(self):
        """
        Calcula la posibilidad de un pokemon de huir de un combate. Calcula solo para "ally"
        :return:
        """
        a = self.ally.speed
        b = 1 if self.enemy.speed == 0 else self.enemy.speed
        self.attempts_run += 1
        f = ((a * 128) / b) + 30 * self.attempts_run
        n = random.randint(0, 255)
        return True if n < int(f) else False

    def get_damage(self, move):
        """
        Calcula el daño de un movimiento
        :param move:
        :return:
        """
        if move.id_category == 1:  # Por el momento no sirven los movimientos que provocan estados
            print("Movimiento de estado")
            return 0
        else:
            b, e = self.get_bonus_and_effectivity(move)
            v = random.randint(85, 100)
            n = self.ally.level if self.ally_turn else self.enemy.level
            if move.id_category == 2:
                a = self.ally.attack if self.ally_turn else self.enemy.attack
                d = self.ally.defense if not self.ally_turn else self.enemy.defense
            elif move.id_category == 3:
                a = self.ally.special_attack if self.ally_turn else self.enemy.special_attack
                d = self.ally.special_defense if not self.ally_turn else self.enemy.special_defense
            p = move.power
            damage = 0.01 * b * e * v * ((((0.2 * n + 1) * a * p)/(25 * d)) + 2)

            # Critic
            critic = np.random.choice((True, False), p=(move.critic_chance_index, 1-move.critic_chance_index))
            if critic:
                attacker = self.ally if self.ally_turn else self.enemy
                multiplier = (2 * attacker.level + 5) / (attacker.level + 5)
                damage = damage * multiplier
            return math.floor(damage)

    def get_bonus_and_effectivity(self, move):
        """
        Calcula dos valores necesarios para get_damage()
        :param move:
        :return:
        """
        attacker = self.ally if self.ally_turn else self.enemy
        defender = self.ally if not self.ally_turn else self.enemy
        if len(attacker.id_type) == 2:
            b = 1.5 if move.type_id == attacker.id_type[0] or move.type_id == attacker.id_type[1] else 1
        else:
            b = 1.5 if move.type_id == attacker.id_type[0] else 1
        e = self.effect_chart[move.type_id-1][defender.id_type[0]-1] # verifica con el primer tipo del pokemon. Ignora el posible segundo tipo
        return b, e

    def make_move(self, opponent, move):
        if not self.move_made:
            damage = self.get_damage(move)
            opponent.current_hp -= damage
            opponent.current_hp = 0 if opponent.current_hp <= 0 else opponent.current_hp
            print(f"{opponent.name.upper()} quedó con {opponent.current_hp}")
            self.move_made = True
            #if opponent.current_hp == 0:
            #    self.end_combat()

    def get_experience(self):
        """
        Calcula la experiencia ganado por el pokemon ganador
        :return:
        """
        e = self.enemy.base_xp  #self.ally.base_xp if self.ally_turn else self.enemy.base_xp
        l = self.enemy.level  #self.ally.level if self.ally_turn else self.enemy.level
        c = 1 if self.enemy.wild else 1.5  # tipo de combate. salvaje = 1, entrenador = 1.5
        xp = (e * l * c) / 7
        return math.floor(xp)

    def end_combat(self):
        """
        Funcion de finalizacion de combate
        :return:
        """
        winner = self.ally if self.enemy.current_hp == 0 else self.enemy if self.ally.current_hp == 0 else None
        if not winner.wild:
            print(winner.name.upper() + " ha ganado " + str(self.get_experience()) + " de xp!") ######################
            winner.current_xp += self.get_experience()
            if winner.current_xp >= winner.xp_next_level:
                winner.level += 1
                winner.current_xp = winner.xp_next_level - winner.current_xp
            self.active = False
        if winner.wild:
            self.active = False
