import math
import random
from collections import defaultdict

import constants
from .gambit_nash_equilibrium import find_all_equilibria

from config import logger


def remove_guaranteed_opponent_moves(score_lookup):
    """This method removes enemy moves from the score-lookup that do not give the bot a choice.
       For example - if the bot has 1 pokemon left, the opponent is faster, and can kill your active pokemon with move X
       then move X for the opponent will be removed from the score_lookup

       The bot behaves much better when it cannot see these types of decisions"""
    move_combinations = list(score_lookup.keys())
    if len(set(k[0] for k in move_combinations)) == 1:
        return score_lookup
    elif len(set(k[1] for k in move_combinations)) == 1:
        return score_lookup

    # find the opponent's moves where the bot has a choice
    opponent_move_scores = dict()
    opponent_decisions = set()
    for k, score in score_lookup.items():
        opponent_move = k[1]
        if opponent_move not in opponent_move_scores:
            opponent_move_scores[opponent_move] = score
        elif opponent_move in opponent_move_scores and score != opponent_move_scores[opponent_move] and not math.isnan(score):
            opponent_decisions.add(opponent_move)

    # re-create score_lookup with only the opponent's move acquired above
    new_opponent_decisions = dict()
    for k, v in score_lookup.items():
        if k[1] in opponent_decisions:
            new_opponent_decisions[k] = v

    return new_opponent_decisions


def pick_safest(score_lookup):
    modified_score_lookup = remove_guaranteed_opponent_moves(score_lookup)
    if not modified_score_lookup:
        modified_score_lookup = score_lookup
    worst_case = defaultdict(lambda: (tuple(), float('inf')))
    for move_pair, result in modified_score_lookup.items():
        if worst_case[move_pair[0]][1] > result:
            worst_case[move_pair[0]] = move_pair, result

    safest = max(worst_case, key=lambda x: worst_case[x][1])
    return worst_case[safest]


def decide_from_safest(score_lookup):
    safest = pick_safest(score_lookup)
    logger.debug("Safest: {}, {}".format(safest[0][0], safest[1]))
    return safest[0][0]


def _find_best_nash_equilibrium(equilibria, df):
    from nashpy import Game
    game = Game(df)

    score = float('-inf')
    best_eq = None
    for eq in equilibria:
        outcome = game[eq][0]
        if outcome > score:
            score = outcome
            best_eq = eq
    return best_eq, score


def find_nash_equilibrium(score_lookup):
    import pandas as pd
    modified_score_lookup = remove_guaranteed_opponent_moves(score_lookup)
    if not modified_score_lookup:
        modified_score_lookup = score_lookup

    df = pd.Series(modified_score_lookup).unstack()

    equilibria = find_all_equilibria(df)
    best_eq, score = _find_best_nash_equilibrium(equilibria, df)
    bot_percentages = best_eq[0]
    opponent_percentages = best_eq[1]

    bot_choices = df.index
    opponent_choices = df.columns

    return bot_choices, opponent_choices, bot_percentages, opponent_percentages, score


def _log_nash_equilibria(bot_choices, opponent_choices, bot_percentages, opponent_percentages, payoff):
    bot_options = []
    for i, percentage in enumerate(bot_percentages):
        if percentage:
            bot_options.append((bot_choices[i], percentage))

    opponent_options = []
    for i, percentage in enumerate(opponent_percentages):
        if percentage:
            opponent_options.append((opponent_choices[i], percentage))

    logger.debug("Bot options: {}".format(bot_options))
    logger.debug("Opponent options: {}".format(opponent_options))
    logger.debug("Payoff: {}".format(payoff))


def pick_from_nash_equilibria(score_lookup):
    bot_choices, opponent_choices, bot_percentages, opponent_percentages, payoff = find_nash_equilibrium(score_lookup)

    _log_nash_equilibria(bot_choices, opponent_choices, bot_percentages, opponent_percentages, payoff)

    s = sum(bot_percentages)
    percentages = [p / s for p in bot_percentages]

    return random.choices(bot_choices, weights=percentages)[0]


def pick_best_move(score_lookup, decision_type):
    if decision_type == constants.PICK_SAFEST:
        return pick_safest(score_lookup)
    elif decision_type == constants.PICK_NASH_EQUILIBRIUM:
        return pick_from_nash_equilibria(score_lookup)
    raise ValueError("Invalid decision type")
