import unittest
import constants
from showdown.calculate_damage import DamageCalculator
from showdown.search.objects import Pokemon
from showdown.state.pokemon import Pokemon as StatePokemon


class TestCalculateDamage(unittest.TestCase):

    def setUp(self):

        self.damage_calculator = DamageCalculator()

        self.charizard = Pokemon.from_state_pokemon_dict(StatePokemon("charizard", 100).to_dict())
        self.venusaur = Pokemon.from_state_pokemon_dict(StatePokemon("venusaur", 100).to_dict())

    def test_fire_blast_from_charizard_to_venusaur_without_modifiers(self):
        move = 'fire Blast'

        dmg = self.damage_calculator.calculate_damage(self.charizard, self.venusaur, move, calc_type='max')
        self.assertEqual([300], dmg)

    def test_stab_without_weakness_calculates_properly(self):
        move = 'sludge bomb'

        dmg = self.damage_calculator.calculate_damage(self.venusaur, self.charizard, move, calc_type='max')
        self.assertEqual([130], dmg)

    def test_4x_weakness_calculates_properly(self):
        move = 'rock slide'

        dmg = self.damage_calculator.calculate_damage(self.venusaur, self.charizard, move, calc_type='max')
        self.assertEqual([268], dmg)

    def test_4x_resistance_calculates_properly(self):
        move = 'gigadrain'

        dmg = self.damage_calculator.calculate_damage(self.venusaur, self.charizard, move, calc_type='max')
        self.assertEqual([27], dmg)

    def test_immunity_calculates_properly(self):
        move = 'earthquake'

        dmg = self.damage_calculator.calculate_damage(self.venusaur, self.charizard, move, calc_type='max')
        self.assertEqual([0], dmg)

    def test_burn_modifier_properly_halves_physical_damage(self):
        move = 'rock slide'

        self.venusaur.status = constants.BURN

        dmg = self.damage_calculator.calculate_damage(self.venusaur, self.charizard, move, calc_type='max')
        self.assertEqual([134], dmg)

    def test_burn_does_not_modify_special_move(self):
        move = 'fire Blast'

        self.venusaur.status  = constants.BURN

        dmg = self.damage_calculator.calculate_damage(self.charizard, self.venusaur, move, calc_type='max')
        self.assertEqual([300], dmg)

    def test_sun_stab_and_2x_weakness(self):

        conditions = {
            'weather': constants.SUN
        }

        move = 'fireblast'

        dmg = self.damage_calculator.calculate_damage(self.charizard, self.venusaur, move, conditions, calc_type='max')
        self.assertEqual([450], dmg)

    def test_sand_increases_rock_spdef(self):

        self.venusaur.types = ['rock']

        conditions = {
            'weather': constants.SAND
        }

        move = 'fireblast'

        dmg = self.damage_calculator.calculate_damage(self.charizard, self.venusaur, move, conditions, calc_type='max')
        self.assertEqual([51], dmg)

    def test_sand_does_not_double_ground_spdef(self):

        self.venusaur.types = ['water']

        conditions = {
            'weather': constants.SAND
        }

        move = 'fireblast'

        dmg = self.damage_calculator.calculate_damage(self.charizard, self.venusaur, move, conditions, calc_type='max')
        self.assertEqual([75], dmg)

    def test_rain_properly_amplifies_water_damage(self):

        conditions = {
            'weather': constants.RAIN
        }

        move = 'surf'

        dmg = self.damage_calculator.calculate_damage(self.venusaur, self.charizard, move, conditions, calc_type='max')
        self.assertEqual([261], dmg)

    def test_reflect_properly_halves_damage(self):

        conditions = {
            'reflect': 1
        }

        move = 'rockslide'

        dmg = self.damage_calculator.calculate_damage(self.venusaur, self.charizard, move, conditions, calc_type='max')
        self.assertEqual([134], dmg)

    def test_light_screen_properly_halves_damage(self):

        conditions = {
            'lightscreen': 1
        }

        move = 'psychic'

        dmg = self.damage_calculator.calculate_damage(self.charizard, self.venusaur, move, conditions, calc_type='max')
        self.assertEqual([82], dmg)

    def test_aurora_veil_properly_halves_damage(self):

        conditions = {
            'auroraveil': 1
        }

        move = 'fireblast'

        dmg = self.damage_calculator.calculate_damage(self.charizard, self.venusaur, move, conditions, calc_type='max')
        self.assertEqual([150], dmg)

    def test_boosts_properly_affect_damage_calculation(self):
        self.charizard.special_attack_boost = 2

        move = 'fireblast'

        dmg = self.damage_calculator.calculate_damage(self.charizard, self.venusaur, move, calc_type='max')
        self.assertEqual([597], dmg)
