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
        with sqlite3.connect(DIR + "pokemon_database.sqlite") as db:
            self.cursor = db.cursor()
            # Stats
            self.id = _id
            self.stats = self.get_move_stats()
            if not self.stats["effect_chance"]:
                self.stats["effect_chance"] = 100
            # self.variation = random.randint(85, 100)
            self.critic_chance_index = 0.0625  # Implementar índices para las chances de crítico

    # Obtener estadísticas del movimiento
    def get_move_stats(self):
        """
        Obtiene los stats del movimiento correspondiente de la base de datos
        :return:
        """
        self.cursor.execute(
            f"SELECT identifier, type_id, power, pp, accuracy, damage_class_id, effect_id, effect_chance "
            f"FROM moves WHERE id = {self.id}")
        stats_info = self.cursor.fetchall()[0]
        stats = {}
        for stat, i in zip(["name", "id_type", "power", "pp", "accuracy", "category", "id_effect", "effect_chance"], range(0, 8)):
            stats[stat] = stats_info[i]
        return stats


class Pokemon:
    """
    Clase Pokemon
    """
    def __init__(self, nro, wild=True):
        # Info
        with sqlite3.connect(DIR + "pokemon_database.sqlite") as db:
            self.nro = nro
            self.wild = wild
            self.cursor = db.cursor()
            self.fetch_data()
            self.initialize_stats()

    def fetch_data(self):
        self.cursor.execute(f"SELECT identifier FROM pokemon WHERE id = {self.nro}")
        self.name = self.cursor.fetchone()[0]

        self.cursor.execute(f"SELECT type_id FROM pokemon_types WHERE pokemon_id = {self.nro}")
        self.id_types = [row[0] for row in self.cursor.fetchall()]

        self.cursor.execute(f"SELECT move_id FROM pokemon_moves WHERE pokemon_id={self.nro} "
                            f"AND pokemon_move_method_id = 1 AND version_group_id = 10")
        self.id_moves = [row[0] for row in self.cursor.fetchall()]

    def initialize_stats(self):
        self.base_xp = self.get_base_xp()
        self.base_stats, self.ev, self.growth_rate = self.get_base_stats()
        self.iv = np.random.randint(0, 32, size=6)
        self.current_id_moves = random.choices(self.id_moves, k=2)

        # Stats
        self.nature_stats = self.get_nature()
        self.level = 5
        self.xp_next_level = self.get_xp_growth_rate() - self.get_xp_growth_rate(self.level)
        self.current_xp = 0
        self.stats = {"hp": self.get_stat(self.base_stats["hp"], self.iv[self.get_stat_index("hp")],
                                          self.ev[self.get_stat_index("hp")], hp=True)}
        for stat in ["attack", "defense", "sp_attack", "sp_defense", "speed"]:
            self.stats[stat] = self.get_stat(self.base_stats[stat], self.iv[self.get_stat_index(stat)],
                                             self.ev[self.get_stat_index(stat)], self.nature_stats[stat])
        self.stats["accuracy"] = 1
        self.stats["evasion"] = 1
        self.current_hp = self.stats["hp"]
        self.move = [Move(10), Move(random.choice(self.id_moves)), Move(254), Move(1)]  # Variable temporal

    @staticmethod
    def get_stat_index(stat):
        return 0 if stat == "hp" \
            else 1 if stat == "attack" \
            else 2 if stat == "defense" \
            else 3 if stat == "sp_attack" \
            else 4 if stat == "sp_defense" \
            else 5

    # Obtener la experiencia base del pokemon
    def get_base_xp(self):
        """
        Obtiene la experiencia base del pokemon
        :return: int
        """
        self.cursor.execute(f"SELECT base_experience FROM pokemon WHERE id = {self.nro}")
        return self.cursor.fetchone()[0]

    # Obtener estadísticas bases del pokemon
    def get_base_stats(self):
        """
        Obtiene las stats bases del pokemon
        :return: int*8
        """
        query = f"SELECT base_stat, effort FROM pokemon_stats WHERE pokemon_id ={self.nro}"
        self.cursor.execute(query)
        stats = self.cursor.fetchall()
        base_stats = {
            "hp": stats[0][0],
            "attack": stats[1][0],
            "defense": stats[2][0],
            "sp_attack": stats[3][0],
            "sp_defense": stats[4][0],
            "speed": stats[5][0]
        }
        ev = [stat[1] for stat in stats]
        self.cursor.execute(f"SELECT growth_rate_id FROM pokemon_species WHERE id = {self.nro}")
        growth_rate_id = self.cursor.fetchone()[0]
        return base_stats, ev, growth_rate_id

    # Obtener naturaleza del pokemon (aleatoria)
    def get_nature(self):
        """
        Obtiene la naturaleza del pokemon (aleatoria)
        :return: dict --> {str: int}
        """
        nature = {}
        id_nature = random.randint(1, 25)
        query = f"SELECT identifier, decreased_stat_id, increased_stat_id FROM natures WHERE id = {id_nature}"
        self.cursor.execute(query)
        nature_info = self.cursor.fetchone()
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

    # Obtener la tasa de crecimiento del pokemon
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
        xp_dict = {
            1: (5 * (n ** 3)) / 4,
            2: n ** 3,
            3: (4 * (n ** 3)) / 5,
            4: (1.2 * (n ** 3)) - (15 * (n ** 2)) + 100 * n - 140,
            5: (n ** 3) * (2 - 0.02 * n) if 0 < n <= 50 else
            (n ** 3) * (1.5 - 0.01 * n) if 51 <= n <= 68 else
            (n ** 3) * (1.274 - 0.02 * (n / 3) - p(n % 3)) if 69 <= n <= 98 else
            (n ** 3) * (1.6 - 0.01 * n),
            6: (n ** 3) * (24 + (n + 1) / 3) / 50 if 0 < n <= 15 else
            (n ** 3) * (14 + n) / 50 if 16 <= n <= 35 else
            (n ** 3) * (32 + (n / 2)) / 50
        }
        return math.floor(xp_dict.get(self.growth_rate, 0))

    # Obtener valor real de las estadísticas del pokemon
    def get_stat(self, base, iv, ev, nature=None, hp=False):
        """
        Obtiene las estadisticas del pokemon segun su nivel, naturaleza, iv, y ev
        :param base: estadistica base
        :param iv: fortalezas individuales (individual values)
        :param ev: puntos de esfuerzo (effort values)
        :param nature: naturaleza
        :param hp: flag. El hp se calcula de manera distinta al resto de estadisticas
        :return: int
        """
        a = 2*base
        b = ev//4
        c = self.level
        d = iv
        if hp:
            return math.floor((((a+d+b)*c)//100)+c+10)
        else:
            return math.floor(((((a+d+b)*c)//100)+5)*nature)


class Battle:
    def __init__(self, ally, enemy):
        self.ally = ally
        self.enemy = enemy
        self.active = True
        self.ally_turn = self.ally.base_stats["speed"] >= self.enemy.base_stats["speed"]  # Determina de quien es el turno. En un inicio, ataca el pokemon mas rapido
        self.change = True  # Posibilidad de "ally" de cambiar de pokemon
        self.attempts_run = 0
        self.place = None  # Por el momento el campo de batalla en el mismo (Hierba Alta)
        self.effect_chart = [
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
            [1, 2, 1, .5, 1, 1, 1, 1, .5, .5, 1, 1, 1, 1, 1, 2, 2, 1]]
        self.first_move_made = False
        self.move_made = False

    # Obtener quien ataca primero
    def get_turn(self):
        """
        Calcula quien ataca primero en el primer movimiento
        :return:
        """
        return self.ally.base_stats["speed"] >= self.enemy.base_stats["speed"]

    # Verificar si el usuario puede escapar o no
    def can_run(self):
        """
        Calcula la posibilidad de un pokemon de huir de un combate. Calcula solo para "ally"
        :return:
        """
        a = self.ally.base_stats["speed"]
        b = max(1, self.enemy.base_stats["speed"])
        self.attempts_run += 1
        f = (a / b * 128) + 30 * self.attempts_run
        n = random.randint(0, 255)
        return n < int(f)

    # Obtener valores de bonus y efectividad necesarios para calcular en daño de un ataque
    def get_bonus_and_effectivity(self, move):
        """
        Calcula dos valores necesarios para get_damage()
        :param move:
        :return:
        """
        attacker = self.ally if self.ally_turn else self.enemy
        defender = self.ally if not self.ally_turn else self.enemy
        num_types = len(attacker.id_types)
        has_type = move.stats["id_type"] in attacker.id_types
        b = 1.5 if (num_types == 2 and has_type) or \
                   (num_types == 1 and has_type and move.type_id == attacker.id_type[0]) else 1
        e = self.effect_chart[move.stats["id_type"]-1][defender.id_types[0]-1]  # verifica solo con el primer tipo
        if e == 2:
            print("es super efectivo")
        elif e == 1:
            print("es normal")
        elif e == 0.5:
            print("es poco efectivo")
        return b, e

    # Calcular total de daño de un ataque
    def get_damage(self, move):
        """
        Calcula el daño de un movimiento
        :param move:
        :return:
        """
        if move.stats["category"] == 1:  # Por el momento no sirven los movimientos que provocan estados
            print("Movimiento de estado")
            return 0
        else:
            b, e = self.get_bonus_and_effectivity(move)
            v = random.randint(85, 100)
            n = self.ally.level if self.ally_turn else self.enemy.level
            if move.stats["category"] == 2:
                a = self.ally.base_stats["attack"] if self.ally_turn else self.enemy.base_stats["attack"]
                d = self.ally.base_stats["defense"] if not self.ally_turn else self.enemy.base_stats["defense"]
            elif move.stats["category"] == 3:
                a = self.ally.base_stats["sp_attack"] if self.ally_turn else self.enemy.base_stats["sp_attack"]
                d = self.ally.base_stats["sp_defense"] if not self.ally_turn else self.enemy.base_stats["sp_defense"]
            p = move.stats["power"]
            damage = 0.01 * b * e * v * ((((0.2 * n + 1) * a * p)/(25 * d)) + 2)

            # Critic
            critic = np.random.choice((True, False), p=(move.critic_chance_index, 1-move.critic_chance_index))
            if critic:
                attacker = self.ally if self.ally_turn else self.enemy
                multiplier = (2 * attacker.level + 5) / (attacker.level + 5)
                damage *= multiplier
            return math.floor(damage)

    # Realizar el ataque
    def make_move(self, opponent, move):
        if not self.move_made:
            damage = self.get_damage(move)
            opponent.current_hp -= damage
            opponent.current_hp = max(0, opponent.current_hp)
            print(f"{opponent.name.upper()} quedó con {opponent.current_hp}")
            self.move_made = True
            if opponent.current_hp == 0:
                self.end_combat()

    # Obtener el valor de la experiencia ganada begun el combate y oponente derrotado
    def get_experience(self):
        """
        Calcula la experiencia ganada por el pokemon ganador
        :return:
        """
        e = self.enemy.base_xp
        l = self.enemy.level
        c = 1 if self.enemy.wild else 1.5  # tipo de combate. salvaje = 1, entrenador = 1.5
        xp = (e * l * c) // 7
        return xp

    # Finalizar el combate. Modifica cantidad de experiencia y nivel del ganador(solo si este pertenece a un entrenador)
    def end_combat(self):
        """
        Funcion de finalizacion de combate
        :return:
        """
        winner = self.ally if self.enemy.current_hp == 0 else self.enemy if self.ally.current_hp == 0 else None
        if winner is not None:
            if not winner.wild:
                winner.current_xp += self.get_experience()
                if winner.current_xp >= winner.xp_next_level:
                    winner.level += 1
                    winner.current_xp = winner.current_xp - winner.xp_next_level
                self.active = False
            else:
                self.active = False
