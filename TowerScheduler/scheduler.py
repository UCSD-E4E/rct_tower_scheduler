'''
This module contains our scheduler's state machine and associated states.
Running the machine results in repeatedly executing the current state's process
function, then executing its update function to proceed to the next state. The
loop is ultimately broken when a call is made to a sleep timer's sleep function,
at which point the sleep timer shuts down the machine running the state machine.
'''

from __future__ import annotations

import abc
import argparse
import datetime as dt
import json
import sys
import time
from enum import Enum
from pathlib import Path

from TowerScheduler.config import Configuration, get_instance
from TowerScheduler.ensemble import Ensemble
from TowerScheduler.util import get_logger


class CheckTimePath(Enum):
    '''
    Path to take from CheckTime state

    skip: Time for current ensemble has been missed, so skip it (go to Iterate)
    run: It's time to execute current ensemble (go to PerformEnsemble)
    wait: Need to wait before current ensemble (go to Sleep)
    reset: All ensembles for the day done, must reset (go to CheckTime for first
            ensemble of next day)
    '''
    SKIP = 0
    RUN = 1
    WAIT = 2
    RESET = 3


class State(abc.ABC):
    '''
    Abstract state class. All states for our state machine will inherit from
    State.
    '''

    @abc.abstractmethod
    def __init__(self) -> None:
        '''
        Constructor for the State class. Initializes the State, including its
        Configuration and Logger objects, plus any other resources needed for
        that particular State.
        '''

    @abc.abstractmethod
    def get_singleton(cls) -> State:
        '''
        Return the singleton object for this state. If the singleton has not
        been created yet, create one, set it as the singleton, and return it.
        '''

    @abc.abstractmethod
    def process(self, state_machine: StateMachine):
        '''
        The process function for each state does what the state is meant to
        accomplish.

        @param state_machine: the machine to which this state belongs
        '''

    @abc.abstractmethod
    def update(self, state_machine: StateMachine) -> State:
        '''
        The update function for each state selects the state to transition to.

        @param state_machine: the machine to which this state belongs
        returns:
            State: The state to which we will next transition
        '''


class WakeUp(State):
    '''
    The WakeUp state is always the first state to run. It makes sure we actually
    have a file we can run and then passes control to CheckTime.
    '''

    singleton: Wakeup = None

    def __init__(self):
        self.config = get_instance(Configuration.default_path)
        self.__log = get_logger("Wake Up State", self.config.log_level)

    @classmethod
    def get_singleton(cls):
        if WakeUp.singleton is None:
            WakeUp.singleton = WakeUp()
        return WakeUp.singleton

    def process(self, state_machine):
        self.__log.info("Running WakeUp process func")

        try:
            with open("current_ensemble.json", "r", encoding="utf-8") as f_in:
                ens_json = json.load(f_in)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            ens_json = { "next_ensemble": 0 }

        state_machine.ens_index = ens_json["next_ensemble"]

        # on first run of day, check that all ensembles are valid
        if state_machine.ens_index == 0:
            for ens in state_machine.ens_list:
                if not ens.validate():
                    self.__log.exception("Invalid ensemble %s at %s. " + \
                        "Unable to continue.",
                        ens.title, ens.start_time.isoformat())
                    raise AttributeError

        now = dt.datetime.now()

        self.__log.info("Waking up at %s", now.isoformat())

    def update(self, state_machine):
        self.__log.info("Running WakeUp update func")
        return CheckTime.get_singleton()


class CheckTime(State):
    '''
    CheckTime determines if the machine should skip an ensemble,
    run an ensemble, or sleep until the next ensemble.
    '''

    singleton: CheckTime = None

    def __init__(self):
        self.check_time_ctrl = CheckTimePath.SKIP
        self.config = get_instance(Configuration.default_path)
        self.__log = get_logger("Check Time State", self.config.log_level)

        self.ctrl_to_state = {
            CheckTimePath.SKIP: Iterate.get_singleton(),
            CheckTimePath.RUN: PerformEnsemble.get_singleton(),
            CheckTimePath.WAIT: Sleep.get_singleton(),
            CheckTimePath.RESET: self
        }

    @classmethod
    def get_singleton(cls):
        if CheckTime.singleton is None:
            CheckTime.singleton = CheckTime()
        return CheckTime.singleton

    def process(self, state_machine):
        self.__log.info("Running CheckTime process func")
        self.__log.info("Current ens index = %i", state_machine.ens_index)

        curr_ens = state_machine.ens_list[state_machine.ens_index]

        # window where if the scheduler wakes up slightly early we allow the
        # scheduler to run the ensemble anyway if it wakes up slightly early
        time_buffer = dt.timedelta(seconds=self.config.execute_buffer)

        if state_machine.ens_index >= len(state_machine.ens_list):
            self.__log.info("Index beyond last ens, resetting")
            self.check_time_ctrl = CheckTimePath.RESET
            state_machine.ens_index = 0
            state_machine.daily_reset = True
            return

        # read time from ensemble and compare to current_time
        now = dt.datetime.now()
        nearest_ens_time = curr_ens.start_time

        if nearest_ens_time < now.time():
            self.__log.info("Time is past current ens, checking for skip")
            if state_machine.daily_reset:
                if now.day == state_machine.day_of_ens:
                    self.check_time_ctrl = CheckTimePath.WAIT
                else:
                    self.check_time_ctrl = CheckTimePath.SKIP
            else:
                self.check_time_ctrl = CheckTimePath.SKIP
        elif nearest_ens_time <= (now + time_buffer).time():
            self.__log.info("Correct time for ensemble %s", curr_ens.title)
            self.check_time_ctrl = CheckTimePath.RUN
        else:
            self.__log.info("Ensemble %s is still in future, go to sleep",
                    curr_ens.title)
            self.check_time_ctrl = CheckTimePath.WAIT

        state_machine.day_of_ens = now.day
        state_machine.daily_reset = False

    def update(self, state_machine):
        self.__log.info("Running CheckTime update func")

        # if current_time is passed current_ensemble time, report error
        if self.check_time_ctrl == CheckTimePath.SKIP:
            now = dt.datetime.now()
            curr_ensemble = state_machine.ens_list[state_machine.ens_index]

            self.__log.error("Skipping past missed ensemble: %s",
                                curr_ensemble.title)
            self.__log.info("Current time: %s", now.time().isoformat())
            self.__log.info("Ensemble target time: %s",
                                curr_ensemble.start_time.isoformat())

        return self.ctrl_to_state[self.check_time_ctrl]


class Iterate(State):
    '''
    Iterate just increases the index by one, then passes back to CheckTime
    '''

    singleton: Iterate = None

    def __init__(self):
        self.config = get_instance(Configuration.default_path)
        self.__log = get_logger("Iterate State", self.config.log_level)

    @classmethod
    def get_singleton(cls):
        if Iterate.singleton is None:
            Iterate.singleton = Iterate()
        return Iterate.singleton

    def process(self, state_machine):
        self.__log.info("Running Iterate process func")
        state_machine.ens_index += 1

    def update(self, state_machine):
        self.__log.info("Running Iterate update func")
        return CheckTime.get_singleton()


class PerformEnsemble(State):
    '''
    PerformEnsemble runs the function associated with the current ensemble
    and then passes to Iterate
    '''

    singleton: PerformEnsemble = None

    def __init__(self):
        self.config = get_instance(Configuration.default_path)
        self.__log = get_logger("Perform Ensemble State", self.config.log_level)

    @classmethod
    def get_singleton(cls):
        if PerformEnsemble.singleton is None:
            PerformEnsemble.singleton = PerformEnsemble()
        return PerformEnsemble.singleton

    def process(self, state_machine):
        self.__log.info("Running PERFORM process func")

        curr_ens = state_machine.ens_list[state_machine.ens_index]

        curr_ens.perform_ensemble_function()

        self.__log.info("Done performing %s", curr_ens.title)

        now = dt.datetime.now()
        self.__log.info("Time is now %s", now.time().isoformat())

    def update(self, state_machine):
        self.__log.info("Running PERFORM update func")
        return Iterate.get_singleton()


class Sleep(State):
    '''
    Sleep calculates how much time is available to sleep once
    the need for sleep is confirmed. A hardware sleep will
    make the machine reset and wake up in WakeUp. A software
    sleep leads to CheckTime.
    '''

    singleton: Sleep = None

    def __init__(self):
        self.nearest_ens_time: dt.time = None
        self.config = get_instance(Configuration.default_path)
        self.__log = get_logger("Sleep State", self.config.log_level)

    @classmethod
    def get_singleton(cls):
        if Sleep.singleton is None:
            Sleep.singleton = Sleep()
        return Sleep.singleton

    def process(self, state_machine):
        self.__log.info("Running Sleep process func")

        # write curr index to ens file before calcs
        with open("current_ensemble.json", "w", encoding="utf-8") as f_out:
            json_file = {
                "next_ensemble": state_machine.ens_index
            }
            json.dump(json_file, f_out, indent=4)

        now = dt.datetime.now()
        self.nearest_ens_time = dt.datetime.combine(dt.date.today(),
                state_machine.ens_list[state_machine.ens_index].start_time)

        self.__log.info("Next ensemble is at %s, and current time is %s",
                    self.nearest_ens_time.time().isoformat(),
                    now.time().isoformat())

    def update(self, state_machine):
        self.__log.info("Running Sleep update func")

        buffer = self.config.wakeup_time + self.config.shutdown_time

        # recalc current_time, and subtract buffer from calculated available
        # time to give ourselves a safely early wakeup
        available_sleep_time = self.seconds_until(self.nearest_ens_time) - \
                                self.config.execute_buffer

        # if enough time, call shutdown
        if available_sleep_time > buffer:
            to_sleep = available_sleep_time - buffer
            self.__log.info("calling sleep timer's sleep(%i)", to_sleep)
            state_machine.sleep_func(to_sleep)
            time.sleep(0.001) # yield

            # Python sleep, sleep timer is offline
            self.__log.error("Sleep timer failed to shut tower down. " + \
                "Calling Python's time.sleep instead...")
            available_sleep_time = self.seconds_until(self.nearest_ens_time) - \
                                    self.config.execute_buffer
            time.sleep(available_sleep_time)

        else:
            # if not enough time, call Python sleep for full time
            self.__log.info("Calling Python's time.sleep for %i seconds",
                    available_sleep_time)
            time.sleep(available_sleep_time)

        self.__log.info("Changing state to WakeUp")
        return WakeUp.get_singleton()

    def seconds_until(self, target: dt.time) -> int:
        '''
        Calculate seconds from the current time before the target time.

        @param target: time for which we want to calculate the seconds from now
        returns:
            int: number of seconds until the target time
        '''

        now = dt.datetime.now()

        if target.time() < now.time():
            self.__log.info("Last ensemble finished, index reset; " + \
                            "next ens is on next day")
            max_today = dt.datetime.combine(dt.date.today(), dt.time.max)
            to_target = dt.timedelta(hours=target.hour,
                                    minutes=target.minute,
                                    seconds=target.second)

            left_today = max_today - now
            sec_until = (left_today + to_target).total_seconds()
        else:
            self.__log.info("Current time less than next ens; " + \
                            "next ens is on same day")
            sec_until = (target - now).total_seconds()

        return sec_until


class StateMachine:
    '''
    The StateMachine class holds the data that needs to be accessed
    from multiple states and runs an infinte loop of process and update
    '''

    def __init__( self,
                ens_list: List[Ensemble],
                sleep_func: Callable[[int], None] ):

        self.config = get_instance(Configuration.default_path)
        self.__log = get_logger("State Machine", self.config.log_level)

        # State machine's data on ensemble schedule: list and next to execute
        self.ens_list: List[Ensemble] = ens_list
        self.ens_index: int = 0

        # Sleep timer's sleep func to call in order to shut tower down
        self.sleep_func: Callable[[int], None] = sleep_func

        # Data used when transitioning from end of one day to beginning of next
        self.day_of_ens: int = 0
        self.daily_reset: boolean = False

        # Start from wakeup state
        self.curr_state: State = WakeUp.get_singleton()

    def run_machine(self):
        while True:
            self.curr_state.process(self)
            self.curr_state = self.curr_state.update(self)

    @property
    def wakeup_time(self):
        return self.config.wakeup_time

    @wakeup_time.setter
    def wakeup_time(self, sec: int):
        if sec < self.config.wakeup_time:
            self.__log.info("New wakeup time %i is less than previous!", sec)
        self.config.wakeup_time = sec
        self.config.write()

    @property
    def shutdown_time(self):
        return self.config.shutdown_time

    @shutdown_time.setter
    def shutdown_time(self, sec: int):
        if sec < self.config.shutdown_time:
            self.__log.info("New shutdown time %i is less than previous!", sec)
        self.config.shutdown_time = sec
        self.config.write()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', type=Path, default='active_ensembles.json')
    parser.add_argument('--reset', type=bool, default=False)
    parser.add_argument('--config', type=Path, default='schedulerConfig.ini')
    args = parser.parse_args()

    Configuration.default_path = args.config

    try:
        ens_list = Ensemble.list_from_json(args.file)
    except FileNotFoundError:
        logging.exception("Active ensembles file not found. " + \
                        "Unable to continue.\n")
        raise FileNotFoundError
    except KeyError:
        logging.exception("Active ensembles file is improperly formatted. " + \
                        "Unable to continue.\n")
        raise KeyError

    if args.reset:
        with open("current_ensemble.json", "w", encoding="utf-8") as f_out:
            json_file = {
                "next_ensemble": 0
            }
            json.dump(json_file, f_out, indent=4)

    StateMachine(ens_list, time.sleep).run_machine()

if __name__ == "__main__":
    main()
