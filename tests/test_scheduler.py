import pytest
from TowerScheduler.scheduler import StateMachine, \
                    WakeUp, CheckTimePath, CheckTime, \
                    Iterate, Sleep, PerformEnsemble

def test_wakeup_transition():
    state_machine = StateMachine()
    wake_up = WakeUp()
    wake_up.update(state_machine)
    assert state_machine.curr_state == state_machine.check_time_state


def test_check_time_to_perform_ensemble_transition():
    state_machine = StateMachine()
    wake_up = WakeUp()
    wake_up.update(state_machine)
    check_time = CheckTime()
    check_time.check_time_ctrl = CheckTimePath.RUN
    check_time.update(state_machine)
    assert state_machine.curr_state == state_machine.perform_ensemble_state


def test_perform_ensemble():
    state_machine = StateMachine()
    wake_up = WakeUp()
    wake_up.update(state_machine)
    check_time = CheckTime()
    check_time.check_time_ctrl = CheckTimePath.RUN
    check_time.update(state_machine)
    perform = PerformEnsemble()
    perform.perform_ensemble_functions()
    assert state_machine.curr_state == state_machine.perform_ensemble_state

def test_check_time_to_sleep_transition():
    state_machine = StateMachine()
    wake_up = WakeUp()
    wake_up.update(state_machine)
    check_time = CheckTime()
    check_time.check_time_ctrl = CheckTimePath.WAIT
    check_time.update(state_machine)
    assert state_machine.curr_state == state_machine.sleep_state

def test_check_time_to_sleep_transition():
    state_machine = StateMachine()
    wake_up = WakeUp()
    wake_up.update(state_machine)
    check_time = CheckTime()
    check_time.check_time_ctrl = CheckTimePath.SKIP
    check_time.update(state_machine)
    assert state_machine.curr_state == state_machine.iterate_state

def test_check_time_reset_transition():
    state_machine = StateMachine()
    wake_up = WakeUp()
    wake_up.update(state_machine)
    check_time = CheckTime()
    check_time.check_time_ctrl = CheckTimePath.RESET
    check_time.update(state_machine)
    assert state_machine.curr_state == state_machine.check_time_state


def test_sleep_to_check_time_transition():
    state_machine = StateMachine()
    wake_up = WakeUp()
    wake_up.update(state_machine)
    check_time = CheckTime()
    check_time.check_time_ctrl = CheckTimePath.RESET
    check_time.update(state_machine)
    sleep = Sleep()
    sleep.update(state_machine)
    assert state_machine.curr_state == state_machine.check_time_state

# def test_fail():
#     assert False

def hello_world():
    print("Hello World")

def print_this():
    print("string")

def add_this():
    print("x + y")

def subtract_this():
    print("x - y")

def multiply_this():
    print("x * y")
