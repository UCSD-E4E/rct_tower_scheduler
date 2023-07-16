from TowerScheduler.scheduler import *

def test_wakeup_transition():
    state_machine = StateMachine()
    wake_up = WakeUp()
    wake_up.update(state_machine)

    assert state_machine.curr_state == state_machine.check_time_state
