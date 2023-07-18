import pytest
import time
from TowerScheduler.scheduler import StateMachine, \
                    WakeUp, CheckTimePath, CheckTime, \
                    Sleep, PerformEnsemble, Iterate


def setup_test():
    state_machine = StateMachine("../TowerScheduler/active_ensembles.json",\
                                  time.sleep)
    return state_machine


def test_wakeup_transition():
    state_machine = setup_test()
    state_machine.curr_state = WakeUp.get_singleton()
    state_machine.curr_state.update(state_machine)
    assert isinstance(state_machine.curr_state, CheckTime)

def test_check_time_to_perform_ensemble_transition():
    state_machine = setup_test()
    state_machine.curr_state = CheckTime.get_singleton()
    state_machine.curr_state.check_time_ctrl = CheckTimePath.RUN
    state_machine.curr_state.update(state_machine)
    assert isinstance(state_machine.curr_state, PerformEnsemble)

# def test_perform_ensemble(): TODO: Perform ensemble function - Wesley
#     state_machine = StateMachine()
#     wake_up = WakeUp()
#     wake_up.update(state_machine)
#     check_time = CheckTime()
#     check_time.check_time_ctrl = CheckTimePath.RUN
#     check_time.update(state_machine)
#     perform = PerformEnsemble()
#     perform.perform_ensemble_functions()
#     assert state_machine.curr_state == state_machine.perform_ensemble_state

def test_check_time_to_sleep_transition():
    state_machine = setup_test()
    state_machine.curr_state = CheckTime.get_singleton()
    state_machine.curr_state.check_time_ctrl = CheckTimePath.WAIT
    state_machine.curr_state.update(state_machine)
    assert isinstance(state_machine.curr_state, Sleep)

# TODO: Fix AttributionError - Wesley
def test_check_time_to_iterate_transition(): 
    state_machine = setup_test()
    state_machine.curr_state = CheckTime.get_singleton()
    state_machine.curr_state.check_time_ctrl = CheckTimePath.SKIP
    state_machine.curr_state.update(state_machine)
    assert isinstance(state_machine.curr_state, Iterate)


def test_check_time_reset_transition():
    state_machine = setup_test()
    state_machine.curr_state = CheckTime.get_singleton()
    state_machine.curr_state.check_time_ctrl = CheckTimePath.RESET
    state_machine.curr_state.update(state_machine)
    assert isinstance(state_machine.curr_state, CheckTime)

# TODO: Fix Infinite Loop - Matthew
# def test_sleep_to_check_time_transition():
#     state_machine = setup_test()
#     state_machine.curr_state = Sleep.get_singleton()
#     state_machine.curr_state.update(state_machine)
#     assert isinstance(state_machine.curr_state, CheckTime)

# # def test_fail():
# #     assert False

# def hello_world():
#     print("Hello World")

# def print_this():
#     print("string")

# def add_this():
#     print("x + y")

# def subtract_this():
#     print("x - y")

# def multiply_this():
#     print("x * y")
