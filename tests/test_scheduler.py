import pytest
import time
from TowerScheduler.ensemble import Ensemble
from TowerScheduler.scheduler import  CheckTimePath, StateMachine, \
                WakeUp, CheckTime, Iterate, PerformEnsemble, Sleep

@pytest.fixture(name='state_machine')
def setup_test():
    ens_list = Ensemble.list_from_json("active_ensembles.json")
    return StateMachine(ens_list, time.sleep)

def test_wakeup_transition(state_machine):
    state_machine.curr_state = WakeUp.get_singleton()
    new_state = state_machine.curr_state.update(state_machine)
    assert isinstance(new_state, CheckTime)

def test_check_time_to_perform_ensemble_transition(state_machine):
    state_machine.curr_state = CheckTime.get_singleton()
    state_machine.curr_state.check_time_ctrl = CheckTimePath.RUN
    new_state = state_machine.curr_state.update(state_machine)
    assert isinstance(new_state, PerformEnsemble)

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

def test_check_time_to_sleep_transition(state_machine):
    state_machine.curr_state = CheckTime.get_singleton()
    state_machine.curr_state.check_time_ctrl = CheckTimePath.WAIT
    new_state = state_machine.curr_state.update(state_machine)
    assert isinstance(new_state, Sleep)

# TODO: Fix AttributionError - Wesley
def test_check_time_to_iterate_transition(state_machine):
    state_machine.curr_state = CheckTime.get_singleton()
    state_machine.curr_state.check_time_ctrl = CheckTimePath.SKIP
    new_state = state_machine.curr_state.update(state_machine)
    assert isinstance(new_state, Iterate)


def test_check_time_reset_transition(state_machine):
    state_machine.curr_state = CheckTime.get_singleton()
    state_machine.curr_state.check_time_ctrl = CheckTimePath.RESET
    new_state = state_machine.curr_state.update(state_machine)
    assert isinstance(new_state, CheckTime)

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
