#!/usr/bin/python3
'''
This module contains our scheduler's state machine and associated states.
Running the machine results in repeatedly executing the current state's process
function, then executing its update function to proceed to the next state. The
loop is ultimately broken when a call is made to a sleep timer's sleep function,
at which point the sleep timer shuts down the machine running the state machine.
'''
from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import sys
import time
from enum import Enum
from pathlib import Path

from ensemble import Ensemble
from TowerScheduler.config import Configuration

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

def get_logger(name: str, level: int=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    formatter = logging.Formatter(
            '%(levelname)s: %(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

class State:
    '''
    Although each state is divided into process and update, they aren't
    always perfectly decoupled. Sometimes the update functioning has to
    do a bit of processing to make its determination. The example of that
    would be the Sleep state which calls into sleep then picks a new state.
    '''

    @classmethod
    def get_singleton(cls) -> State:
        '''
        Return the singleton object for this state. If the singleton has not
        been created yet, create one, set it as the singleton, and return it.
        '''

    def process(self, state_machine: StateMachine):
        '''
        The process function for each state does what the state is meant to
        accomplish. To be overwritten in each state.

        @param state_machine: the machine to which this state belongs
        '''

    def update(self, state_machine: StateMachine):
        '''
        The update function for each state selects the state to transition to.
        To be overwritten in each state.

        @param state_machine: the machine to which this state belongs
        '''

class WakeUp(State):
    '''
    The WakeUp state is always the first state to run. It makes sure we actually
    have a file we can run and then passes control to CheckTime.
    '''

    singleton = None

    def __init__(self):
        self.config_obj = Configuration.get_singleton(Path('schedulerConfig.ini'))
        self.logger = get_logger("Wake Up State", self.config_obj.log_level)

    @classmethod
    def get_singleton(cls):
        if WakeUp.singleton is None:
            WakeUp.singleton = WakeUp()
        return WakeUp.singleton

    def process(self, state_machine):
        self.logger.info("Running WakeUp process func")

        with open("active_ensembles.json", "r", encoding="utf-8") as f_in:
            ens_json = json.load(f_in)

        state_machine.ens_index = ens_json["next_ensemble"]

        # on first run of day, check that all ensembles are valid
        if state_machine.ens_index == 0:
            for ens in state_machine.ens_list:
                if not ens.validate():
                    self.logger.exception("Invalid ensemble %s to execute " + \
                        "at %i. Unable to continue.", ens.title, ens.start_time)
                    sys.exit()

        now = dt.datetime.now().time()

        self.logger.info("Waking up at %02i:%02i:%02i",
                        now.hour, now.minute, now.second)

    def update(self, state_machine):
        self.logger.info("Running WakeUp update func")
        state_machine.curr_state = CheckTime.get_singleton()

class CheckTime(State):
    '''
    CheckTime determines if the machine should skip an ensemble,
    run an ensemble, or sleep until the next ensemble.
    '''

    singleton = None

    def __init__(self):
        self.check_time_ctrl = CheckTimePath.SKIP
        self.config_obj = Configuration.get_singleton(Path('schedulerConfig.ini'))
        self.logger = get_logger("Check Time State", self.config_obj.log_level)

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
        self.logger.info("Running CheckTime process func")
        self.logger.info("Current ens index = %i", state_machine.ens_index)

        # this is a small window where if the scheduler wakes up
        # slightly early from sleep we allow it to run the ensemble anyway
        time_buffer = dt.timedelta(seconds=self.config_obj.execute_buffer)

        if state_machine.ens_index < len(state_machine.ens_list):
            # read time from ensemble and compare to current_time
            now = dt.datetime.now()
            nearest_ens_time = state_machine.ens_list[state_machine.ens_index].start_time

            if nearest_ens_time < now.time():
                self.logger.info("Time is past current ens, checking for skip")
                if state_machine.daily_reset:
                    if now.day == state_machine.day_of_ens:
                        self.check_time_ctrl = CheckTimePath.WAIT
                    else:
                        self.check_time_ctrl = CheckTimePath.SKIP
                else:
                    self.check_time_ctrl = CheckTimePath.SKIP
            elif nearest_ens_time <= (now + time_buffer).time():
                self.logger.info("Correct time for ensemble: %s",
                        state_machine.ens_list[state_machine.ens_index].title)
                self.check_time_ctrl = CheckTimePath.RUN
            else:
                self.logger.info("ensemble %s is still in future, go to sleep",
                        state_machine.ens_list[state_machine.ens_index].title)
                self.check_time_ctrl = CheckTimePath.WAIT

            state_machine.day_of_ens = now.day
            state_machine.daily_reset = False
        else:
            self.logger.info("Index beyond last ens, resetting")
            self.check_time_ctrl = CheckTimePath.RESET
            state_machine.ens_index = 0
            state_machine.daily_reset = True

    def update(self, state_machine):
        self.logger.info("Running CheckTime update func")

        # if current_time is passed current_ensemble time, report error
        if self.check_time_ctrl == CheckTimePath.SKIP:
            now = dt.datetime.now()
            curr_ensemble = state_machine.ens_list[state_machine.ens_index]

            self.logger.error("Skipping past missed ensemble: %s",
                                curr_ensemble.title)
            self.logger.info("Current time: %02i:%02i:%02i",
                                now.hour, now.minute, now.second)
            self.logger.info("Ensemble target time: %02i:%02i:%02i",
                                curr_ensemble.start_time.hour,
                                curr_ensemble.start_time.minute,
                                curr_ensemble.start_time.second)

        state_machine.curr_state = self.ctrl_to_state[self.check_time_ctrl]

class Iterate(State):
    '''
    Iterate just increases the index by one, then passes back to CheckTime
    '''

    singleton = None

    def __init__(self):
        self.config_obj = Configuration.get_singleton(Path('schedulerConfig.ini'))
        self.logger = get_logger("Iterate State", self.config_obj.log_level)

    @classmethod
    def get_singleton(cls):
        if Iterate.singleton is None:
            Iterate.singleton = Iterate()
        return Iterate.singleton

    def process(self, state_machine):
        self.logger.info("Running Iterate process func")

        # increment the current_ensemble variable
        state_machine.ens_index += 1

    def update(self, state_machine):
        self.logger.info("Running Iterate update func")

        # transition to CheckTime state
        state_machine.curr_state = CheckTime.get_singleton()

class PerformEnsemble(State):
    '''
    PerformEnsemble runs the function associated with the current ensemble
    and then passes to Iterate
    '''

    singleton = None

    def __init__(self):
        self.config_obj = Configuration.get_singleton(Path('schedulerConfig.ini'))
        self.logger = get_logger("Perform Ensemble State",
                                self.config_obj.log_level)

    @classmethod
    def get_singleton(cls):
        if PerformEnsemble.singleton is None:
            PerformEnsemble.singleton = PerformEnsemble()
        return PerformEnsemble.singleton

    def process(self, state_machine):
        self.logger.info("Running PERFORM process func")

        # run the function of the current ensemble
        state_machine.ens_list[ens_index].perform_ensemble_function()

        self.logger.info("Done performing %s",
                state_machine.ens_list[state_machine.ens_index].title)

        now = dt.datetime.now()
        self.logger.info("Time is now %02i:%02i:%02i",
                now.hour, now.minute, now.second)

    def update(self, state_machine):
        self.logger.info("Running PERFORM update func")
        state_machine.curr_state = Iterate.get_singleton()

class Sleep(State):
    '''
    Sleep calculates how much time is available to sleep once
    the need for sleep is confirmed. A hardware sleep will
    make the machine reset and wake up in WakeUp. A software
    sleep leads to CheckTime.
    '''

    singleton = None

    def __init__(self):
        self.nearest_ens_time: dt.time = None
        self.config_obj = Configuration.get_singleton(Path('schedulerConfig.ini'))
        self.logger = get_logger("Sleep State", self.config_obj.log_level)

    @classmethod
    def get_singleton(cls):
        if Sleep.singleton is None:
            Sleep.singleton = Sleep()
        return Sleep.singleton

    def process(self, state_machine):
        self.logger.info("Running Sleep process func")

        # write curr index to ens file before calcs
        with open("active_ensembles.json", "w", encoding="utf-8") as f_out:
            json_file = {
                "ensemble_list": Ensemble.list_to_json(state_machine.ens_list),
                "next_ensemble": state_machine.ens_index
            }
            json.dump(json_file, f_out, indent=4)

        now = dt.datetime.now()
        self.nearest_ens_time = dt.datetime.combine(dt.date.today(),
                state_machine.ens_list[state_machine.ens_index].start_time)

        self.logger.info("Next ensemble is at %02i:%02i:%02i, "+ \
                "and current time is %02i:%02i:%02i",
                    self.nearest_ens_time.hour,
                    self.nearest_ens_time.minute,
                    self.nearest_ens_time.second,
                    now.hour, now.minute, now.second)

    def update(self, state_machine):
        self.logger.info("Running Sleep update func")

        # write configuration to save any updates before sleep
        self.config_obj.write()

        # recalc current_time vs (current_ensemble time + wakeup + shutdown)
        now = dt.datetime.now()

        if self.nearest_ens_time.time() < now.time():
            self.logger.info("Last ensemble finished, index reset; " + \
                            "next ens is on next day")
            max_today = dt.datetime.combine(dt.date.today(), dt.time.max)
            to_nearest = dt.timedelta(hours=self.nearest_ens_time.hour,
                                    minutes=self.nearest_ens_time.minute,
                                    seconds=self.nearest_ens_time.second)

            time_left_today = max_today - now
            available_sleep_time = (time_left_today + to_nearest).total_seconds()
        else:
            self.logger.info("Current time less than next ens; " + \
                            "next ens is on same day")
            available_sleep_time = (self.nearest_ens_time - now).total_seconds()

        # if enough time, call shutdown
        if available_sleep_time > \
                (self.config_obj.wakeup_time + self.config_obj.shutdown_time):
            to_sleep = available_sleep_time - \
                (self.config_obj.wakeup_time + self.config_obj.shutdown_time)
            self.logger.info("calling sleep timer's sleep(%i)", to_sleep)
            state_machine.sleep_func(to_sleep)
            time.sleep(1) # yield

            # Python sleep, sleep timer is offline
            self.logger.error("Sleep timer failed to shut tower down. Calling" \
                + " Python's time.sleep for %i seconds", to_sleep)
            time.sleep(to_sleep)

        else:
            # if not enough time, call Python sleep
            self.logger.info("Calling Python's time.sleep for %i seconds",
                    available_sleep_time)
            time.sleep(available_sleep_time)
            self.logger.info("Changing state to CheckTime")
            state_machine.curr_state = CheckTime.get_singleton()

class StateMachine:
    '''
    The StateMachine class holds the data that needs to be accessed
    from multiple states and runs an infinte loop of process and update
    '''

    def __init__( self,
                ens_list: List[Ensemble],
                sleep_func: Callable[[int], None] ):

        self.config_obj = Configuration.get_singleton(Path('schedulerConfig.ini'))
        self.logger = get_logger("State Machine", self.config_obj.log_level)

        # State machine's data on ensemble schedule: list and next to execute
        self.ens_list = ens_list
        self.ens_index = 0

        # Sleep timer's sleep func to call in order to shut tower down
        self.sleep_func = sleep_func

        # Data used when transitioning from end of one day to beginning of next
        self.day_of_ens = 0
        self.daily_reset = False

        # Start from wakeup state
        self.curr_state = WakeUp.get_singleton()

    def run_machine(self):
        while True:
            self.curr_state.process(self)
            self.curr_state.update(self)

    @property
    def wakeup_time(self):
        return self.config_obj.wakeup_time

    @wakeup_time.setter
    def wakeup_time(self, sec: int):
        if sec < self.config_obj.wakeup_time:
            self.logger.info("New wakeup time %i is less than previous!", sec)
        self.config_obj.wakeup_time = sec

    @property
    def shutdown_time(self):
        return self.config_obj.shutdown_time

    @shutdown_time.setter
    def shutdown_time(self, sec: int):
        if sec < self.config_obj.shutdown_time:
            self.logger.info("New shutdown time %i is less than previous!", sec)
        self.config_obj.shutdown_time = sec


def main(ens_list: list[Ensemble]):
    control_flow = StateMachine(ens_list, time.sleep)
    control_flow.run_machine()

if __name__ == "__main__":
    # check for input file argument
    parser = argparse.ArgumentParser()
    parser.add_argument('file', type=Path)
    args = parser.parse_args()

    try:
        ens_list = Ensemble.list_from_json(args.file)
    except FileNotFoundError:
        logging.exception("Active ensembles json file not found." + \
                        "Unable to continue.\n")
        sys.exit()
    except KeyError:
        logging.exception("Active ensembles json file is improperly " + \
                        "formatted. Unable to continue.\n")
        sys.exit()

    main(ens_list)
