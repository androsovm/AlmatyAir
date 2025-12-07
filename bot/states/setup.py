from aiogram.fsm.state import State, StatesGroup


class SetupStates(StatesGroup):
    """FSM states for user setup wizard"""

    # Screen 1: Choose notification types
    choose_notifications = State()

    # Screen 2: Set daily notification time
    set_time = State()

    # Screen 3: Set AQI threshold
    set_threshold = State()
