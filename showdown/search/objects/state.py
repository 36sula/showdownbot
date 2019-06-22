import constants
from .side import Side


class State(object):
    __slots__ = ('self', 'opponent', 'weather', 'force_switch', 'field', 'trick_room', 'wait')

    def __init__(self, user, opponent, weather, field, trick_room, force_switch, wait):
        self.self = user
        self.opponent = opponent
        self.weather = weather
        self.field = field
        self.trick_room = trick_room
        self.force_switch = force_switch
        self.wait = wait

    @classmethod
    def from_dict(cls, state_dict):
        return State(
            Side.from_dict(state_dict[constants.SELF]),
            Side.from_dict(state_dict[constants.OPPONENT]),
            state_dict[constants.WEATHER],
            state_dict[constants.FIELD],
            state_dict[constants.TRICK_ROOM],
            state_dict[constants.FORCE_SWITCH],
            state_dict[constants.WAIT],
        )

    def __repr__(self):
        return str(
            {
                constants.SELF: self.self,
                constants.OPPONENT: self.opponent,
                constants.WEATHER: self.weather,
                constants.FIELD: self.field,
                constants.TRICK_ROOM: self.trick_room,
                constants.FORCE_SWITCH: self.force_switch,
                constants.WAIT: self.wait
            }
        )
