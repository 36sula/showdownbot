import json
import asyncio
import concurrent.futures

from copy import deepcopy

import constants
import config
from config import logger
from config import reset_logger
from showdown.decide.decide import decide_from_safest
from showdown.search.select_best_move import get_move_combination_scores
from showdown.state.battle import Battle
from showdown.state.pokemon import Pokemon
from showdown.state.battle_modifiers import update_battle
from showdown.search.state_mutator import StateMutator

from websocket_communication import PSWebsocketClient


async def _handle_team_preview(battle: Battle, ps_websocket_client: PSWebsocketClient):
    battle_copy = deepcopy(battle)
    battle_copy.user.active = Pokemon.get_dummy()
    battle_copy.opponent.active = Pokemon.get_dummy()

    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        formatted_message = await loop.run_in_executor(
            pool, _find_best_move, battle_copy
        )
    size_of_team = len(battle.user.reserve) + 1
    team_list_indexes = list(range(1, size_of_team))
    choice_digit = int(formatted_message[0].split()[-1])

    team_list_indexes.remove(choice_digit)
    message = ["/team {}{}|{}".format(choice_digit, "".join(str(x) for x in team_list_indexes), battle.rqid)]
    battle.user.active = battle.user.reserve.pop(choice_digit - 1)

    await ps_websocket_client.send_message(battle.battle_tag, message)


async def get_battle_tag_and_opponent(ps_websocket_client: PSWebsocketClient):
    while True:
        msg = await ps_websocket_client.receive_message()
        split_msg = msg.split('|')
        first_msg = split_msg[0]
        if 'battle' in first_msg:
            battle_tag = first_msg.replace('>', '').strip()
            user_name = split_msg[-1].replace('☆', '').strip()
            opponent_name = split_msg[4].replace(user_name, '').replace('vs.', '').strip()
            return battle_tag, opponent_name


async def _initialize_battle_with_tag(ps_websocket_client: PSWebsocketClient):
    battle_tag, opponent_name = await get_battle_tag_and_opponent(ps_websocket_client)
    while True:
        msg = await ps_websocket_client.receive_message()
        split_msg = msg.split('|')
        if split_msg[1].strip() == 'request' and split_msg[2].strip():
            user_json = json.loads(split_msg[2].strip('\''))
            user_id = user_json[constants.SIDE][constants.ID]
            opponent_id = constants.ID_LOOKUP[user_id]
            battle = Battle(battle_tag)
            battle.opponent.name = opponent_id
            battle.opponent.account_name = opponent_name
            return battle, opponent_id, user_json


async def _start_random_battle(ps_websocket_client: PSWebsocketClient):
    battle, opponent_id, user_json = await _initialize_battle_with_tag(ps_websocket_client)
    reset_logger(logger, "{}-{}.log".format(battle.opponent.account_name, battle.battle_tag))
    while True:
        msg = await ps_websocket_client.receive_message()

        if constants.START_STRING in msg:
            msg = msg.split(constants.START_STRING)[-1]
            for line in msg.split('\n'):
                if opponent_id in line and constants.SWITCH_STRING in line:
                    battle.start_random_battle(user_json, line)
                    continue

                if battle.started:
                    await update_battle(battle, line)

            return battle


async def _start_standard_battle(ps_websocket_client: PSWebsocketClient, pokemon_battle_type):
    battle, opponent_id, user_json = await _initialize_battle_with_tag(ps_websocket_client)
    reset_logger(logger, "{}-{}.log".format(battle.opponent.account_name, battle.battle_tag))

    msg = ''
    while constants.START_TEAM_PREVIEW not in msg:
        msg = await ps_websocket_client.receive_message()

    preview_string_lines = msg.split(constants.START_TEAM_PREVIEW)[-1].split('\n')

    opponent_pokemon = []
    for line in preview_string_lines:
        if not line:
            continue

        split_line = line.split('|')
        if split_line[1] == constants.TEAM_PREVIEW_POKE and split_line[2].strip() == opponent_id:
            opponent_pokemon.append(split_line[3])

    battle.initialize_team_preview(user_json, opponent_pokemon, pokemon_battle_type)
    await _handle_team_preview(battle, ps_websocket_client)

    return battle


def _find_best_move(battle: Battle):
    state = battle.to_object()
    logger.debug("Attempting to find best move from: {}".format(state))
    mutator = StateMutator(state)
    move_scores = get_move_combination_scores(mutator)
    logger.debug("Score lookups produced: {}".format(move_scores))

    decision = decide_from_safest(move_scores)
    logger.debug("Decision: {}".format(decision))

    if decision.startswith(constants.SWITCH_STRING) and decision != "switcheroo":
        switch_pokemon = decision.split("switch ")[-1]
        for pkmn in battle.user.reserve:
            if pkmn.name == switch_pokemon:
                message = "/switch {}".format(pkmn.index)
                break
        else:
            raise ValueError("Tried to switch to: {}".format(switch_pokemon))
    else:
        message = "/choose move {}".format(decision)
        if battle.user.active.can_mega_evo:
            message = "{} {}".format(message, constants.MEGA)
        elif battle.user.active.can_ultra_burst:
            message = "{} {}".format(message, constants.ULTRA_BURST)

        if battle.user.active.get_move(decision).can_z:
            message = "{} {}".format(message, constants.ZMOVE)

    return [message, str(battle.rqid)]


async def pokemon_battle(ps_websocket_client: PSWebsocketClient, pokemon_battle_type):
    if "random" in pokemon_battle_type:
        battle = await _start_random_battle(ps_websocket_client)
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            formatted_message = await loop.run_in_executor(
                pool, _find_best_move, battle
            )
        await ps_websocket_client.send_message(battle.battle_tag, formatted_message)
    else:
        battle = await _start_standard_battle(ps_websocket_client, pokemon_battle_type)

    await ps_websocket_client.send_message(battle.battle_tag, ['/timer on'])
    while True:
        msg = await ps_websocket_client.receive_message()
        if constants.WIN_STRING in msg:
            winner = msg.split(constants.WIN_STRING)[-1].split('\n')[0].strip()
            logger.debug("Winner: {}".format(winner))
            await ps_websocket_client.leave_battle(battle.battle_tag, save_replay=config.save_replay)
            return winner
        action_required = await update_battle(battle, msg)
        if action_required and not battle.wait:
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                formatted_message = await loop.run_in_executor(
                    pool, _find_best_move, battle
                )
            if formatted_message is not None:
                await ps_websocket_client.send_message(battle.battle_tag, formatted_message)
