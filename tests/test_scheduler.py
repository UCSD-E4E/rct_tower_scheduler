import datetime as dt
import json
import os
import pytest
import time
from pathlib import Path

from conftest import create_time_source
from TowerScheduler.config import Configuration, get_instance
from TowerScheduler.ensemble import Ensemble
from TowerScheduler.scheduler import  CheckTimePath, StateMachine, \
                WakeUp, CheckTime, Iterate, PerformEnsemble, Sleep


# test each State's update() function by confirming correct transitions
@pytest.fixture(name='state_machine')
def setup_test():
    # remove current ensemble file so we know we're starting from index 0
    if os.path.exists("current_ensemble.json"):
        os.remove("current_ensemble.json")

    Configuration.default_path = Path('testConfig.ini')
    ens_list = Ensemble.list_from_json("tests/test_active_ensembles.json")
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

def test_sleep_to_wakeup_transition(state_machine):
    state_machine.curr_state = Sleep.get_singleton()
    config = get_instance(Configuration.default_path)
    # Calling Python's time.sleep for 0 seconds
    state_machine.curr_state.nearest_ens_time = dt.datetime.now()\
         + dt.timedelta(seconds=config.execute_buffer + 1)
    new_state = state_machine.curr_state.update(state_machine)

    # TODO: test state_machine.sleep_func vs time.sleep

    assert isinstance(new_state, WakeUp)

def test_perform_ensemble_to_iterate_transition(state_machine):
    state_machine.curr_state = PerformEnsemble.get_singleton()
    new_state = state_machine.curr_state.update(state_machine)
    assert isinstance(new_state, Iterate)


# test each State's process() function
def test_wakeup_process(state_machine):
    state_machine.curr_state = WakeUp.get_singleton()

    # test curr_ensemble = 0 --> all ensembles are validated
    try:
        state_machine.curr_state.process(state_machine)
        assert False # we should not reach this due to bad function input
    except AttributeError:
        assert True # we should reach this
        with open("current_ensemble.json", "w", encoding="utf-8") as f_out:
            json_file = {
                "next_ensemble": 1
            }
            json.dump(json_file, f_out, indent=4)

    # should no longer throw exception now that validate is not called
    state_machine.curr_state.process(state_machine)

def test_check_time_process_wait(state_machine):
    state_machine.curr_state = CheckTime.get_singleton()
    ens_time = dt.datetime.combine(dt.date.today(),
                                state_machine.ens_list[0].start_time)

    config = get_instance(Configuration.default_path)
    max_buffer = dt.timedelta(seconds=config.execute_buffer)

    # confirm maximum time until ens will run
    state_machine.time_func = create_time_source(ens_time - max_buffer)
    state_machine.curr_state.process(state_machine)
    assert state_machine.curr_state.check_time_ctrl == CheckTimePath.RUN

    # confirm exact time of ens will run
    state_machine.time_func = create_time_source(ens_time)
    state_machine.curr_state.process(state_machine)
    assert state_machine.curr_state.check_time_ctrl == CheckTimePath.RUN

# test checktime SKIP

# test checktime WAIT

# test checktime RESET
