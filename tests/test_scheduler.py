import pytest
import time
from pathlib import Path

from TowerScheduler.config import Configuration
from TowerScheduler.ensemble import Ensemble
from TowerScheduler.scheduler import  CheckTimePath, StateMachine, \
                WakeUp, CheckTime, Iterate, PerformEnsemble, Sleep


@pytest.fixture(name='state_machine')
def setup_test():
    Configuration.default_path = Path('testConfig.ini')
    ens_list = Ensemble.list_from_json("active_ensembles.json")
    return StateMachine(ens_list, time.sleep)

def test_wakeup_to_check_time_transition(state_machine):
    state_machine.curr_state = WakeUp.get_singleton()
    new_state = state_machine.curr_state.update(state_machine)
    assert isinstance(new_state, CheckTime)

def test_check_time_to_perform_ensemble_transition(state_machine):
    state_machine.curr_state = CheckTime.get_singleton()
    state_machine.curr_state.check_time_ctrl = CheckTimePath.RUN
    new_state = state_machine.curr_state.update(state_machine)
    assert isinstance(new_state, PerformEnsemble)

def test_check_time_to_sleep_transition(state_machine):
    state_machine.curr_state = CheckTime.get_singleton()
    state_machine.curr_state.check_time_ctrl = CheckTimePath.WAIT
    new_state = state_machine.curr_state.update(state_machine)
    assert isinstance(new_state, Sleep)

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

def test_iterate_to_check_time_transition(state_machine):
    state_machine.curr_state = Iterate.get_singleton()
    new_state = state_machine.curr_state.update(state_machine)
    assert isinstance(new_state, CheckTime)

def test_sleep_to_check_time_transition(state_machine):
    state_machine.curr_state = Sleep.get_singleton()
    new_state = state_machine.curr_state.update(state_machine)
    assert isinstance(new_state, CheckTime)

def test_perform_ensemble_to_check_time_transition(state_machine):
    state_machine.curr_state = PerformEnsemble.get_singleton()
    new_state = state_machine.curr_state.update(state_machine)
    assert isinstance(new_state, CheckTime)
