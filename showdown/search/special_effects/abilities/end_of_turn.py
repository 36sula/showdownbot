import constants


def poisonheal(state, attacking_side, attacking_pokemon, defending_side, defending_pokemon):
    if attacking_pokemon.status in [constants.POISON, constants.TOXIC]:
        return (
            constants.MUTATOR_HEAL,
            attacking_side,
            min(attacking_pokemon.maxhp - attacking_pokemon.hp, round(0.125 * attacking_pokemon.maxhp))
        )


ability_lookup = {
    "poisonheal": poisonheal,
}


def ability_end_of_turn(ability_name, state, attacking_side, attacking_pokemon, defending_side, defending_pokemon):
    ability_func = ability_lookup.get(ability_name)
    if ability_func is not None:
        return ability_func(state, attacking_side, attacking_pokemon, defending_side, defending_pokemon)
    else:
        return None
