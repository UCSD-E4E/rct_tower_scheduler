#!/usr/bin/python3
'''
This module contains our scheduler's state machine and associated states.
Running the machine results in repeatedly executing the current state's process
function, then executing its update function to proceed to the next state. The
loop is ultimately broken when a call is made to a sleep timer's sleep function,
at which point the sleep timer shuts down the machine running the state machine.
'''

from enum import Enum
import importlib.util
import json
import logging
import sys
import time

SECONDS_IN_DAY = 86400

class CheckTimePath(Enum):
    '''
    Path to take from CheckTime state

    skip: Time for current ensemble has been missed, so skip it (go to Iterate)
    run: It's time to execute current ensemble (go to PerformEnsemble)
    wait: Need to wait before current ensemble (go to Sleep)
    reset: All ensembles for the day done, must reset (go to CheckTime for first
            ensemble of next day)
    '''
    skip = 0
    run = 1
    wait = 2
    reset = 3

class ErrorCode(Enum): # TODO: error state unnecessary at this point, just fold missed_ens into Check Time state
    '''
    Types of errors, for use in handling and recovering in Error state

    no_err: No error to report
    missed_ens: Time for an ensemble was missed, report that this ensemble
            wasn't performed
    '''
    no_err = 0
    missed_ens = 1

def hms_to_seconds(hour: int, minute: int, sec: int): # TODO: just use from convert_to_active (put in another module for helper funcs or smth)
    '''
    Convert hours, minutes, and seconds to just seconds

    @param hour: number of hours to convert to sec
    @param minute: number of minutes to convert to sec
    @param sec: number of seconds

    return: sum of seconds in hour, minute, and sec
    '''

    return sec + minute * 60 + hour * 3600

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

    def process(self, state_machine):
        '''
        The process function for each state does what the state is meant to
        accomplish. To be overwritten in each state.

        @param state_machine: the machine to which this state belongs
        '''

    def update(self, state_machine):
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

    def __init__(self):
        self.err_code = ErrorCode.no_err
        self.logger = get_logger("Wake Up State")

    def process(self, state_machine):
        self.logger.info("Running WakeUp process func")

        # read active ensembles file
        try:
            with open(state_machine.ens_filename, "r", encoding="utf-8") as f_in:
                state_machine.ens = json.load(f_in)

            state_machine.ens_index = state_machine.ens["next_ensemble"]
            state_machine.ens_list = state_machine.ens["ensemble_list"]
        except FileNotFoundError:
            self.logger.exception("No active_ensembles.json file found." + \
                            "Unable to continue.\n")
            sys.exit()

        now = time.localtime()
        curr_time_seconds = hms_to_seconds(now.tm_hour, now.tm_min, now.tm_sec)

        self.logger.info("Waking up at seconds = %i" % curr_time_seconds)

    def update(self, state_machine):
        self.logger.info("Running WakeUp update func")
        state_machine.curr_state = state_machine.check_time_state

class CheckTime(State):
    '''
    CheckTime determines if the machine should skip an ensemble,
    run an ensemble, or sleep until the next ensemble.
    '''

    def __init__(self):
        self.check_time_ctrl = CheckTimePath.skip
        self.err_code = ErrorCode.no_err
        self.logger = get_logger("Check Time State")

    def process(self, state_machine):
        self.logger.info("Running CheckTime process func")
        self.logger.info("Current ens index = %i" % state_machine.ens_index)

        # this is a small window where if the scheduler wakes up
        # slightly early from sleep we allow it to run the ensemble anyway
        TIME_BUFFER = 5 # TODO: allow configuration

        if state_machine.ens_index < len(state_machine.ens_list):
            # read time from ensemble and compare to current_time
            now = time.localtime()
            curr_time_seconds = hms_to_seconds(now.tm_hour,
                                                now.tm_min,
                                                now.tm_sec)

            nearest_ens_time = state_machine.ens_list[state_machine.ens_index]["start_time"]

            if nearest_ens_time < curr_time_seconds:
                self.logger.info("Time is past current ens, checking for skip")
                if state_machine.daily_reset == True:
                    if now.tm_wday == state_machine.day_of_ens:
                        self.check_time_ctrl = CheckTimePath.wait
                    else:
                        self.check_time_ctrl = CheckTimePath.skip
                        self.err_code = ErrorCode.missed_ens
                else:
                    self.check_time_ctrl = CheckTimePath.skip
                    self.err_code = ErrorCode.missed_ens
            elif nearest_ens_time <= curr_time_seconds + TIME_BUFFER:
                self.logger.info("Correct time for ensemble: %s" % \
                        state_machine.ens_list[state_machine.ens_index]['title'])
                self.check_time_ctrl = CheckTimePath.run
            else:
                self.logger.info("ensemble %s is still in future, go to sleep" \
                        % state_machine.ens_list[state_machine.ens_index]['title'])
                self.check_time_ctrl = CheckTimePath.wait

            state_machine.day_of_ens = now.tm_wday
            state_machine.daily_reset = False
        else:
            self.logger.info("Index beyond last ens, resetting")
            self.check_time_ctrl = CheckTimePath.reset
            state_machine.ens_index = 0
            state_machine.daily_reset = True

    def update(self, state_machine):
        # TODO: states shouldn't know about each other, let sm transition itself
        # TODO: use dict mapping to next state, not this if-else mess
        self.logger.info("Running CheckTime update func")

        # if current_time is passed current_ensemble time,
        # transition to Iterate
        if self.check_time_ctrl == CheckTimePath.skip:
            state_machine.error_state.error_code = self.error_code # terrible horrible but temporary while states still update each other
            state_machine.curr_state = state_machine.error_state

        # if current_time == current_ensemble time,
        # transition to PerformEnsemble state
        elif self.check_time_ctrl == CheckTimePath.run:
            state_machine.curr_state = state_machine.perform_ensemble_state

        # if current_time is less than current_ensemble time,
        # transition to SLEEP state
        elif self.check_time_ctrl == CheckTimePath.wait:
            state_machine.curr_state = state_machine.sleep_state

        # if all ensembles are done, need to sleep til first one of next day
        elif self.check_time_ctrl == CheckTimePath.reset:
            state_machine.curr_state = state_machine.check_time_state

class Iterate(State):
    '''
    Iterate just increases the index by one then passes
    back to CheckTime
    '''

    def __init__(self):
        self.err_code = ErrorCode.no_err
        self.logger = get_logger("Iterate State")

    def process(self, state_machine):
        self.logger.info("Running Iterate process func")

        # increment the current_ensemble variable
        state_machine.ens_index += 1

    def update(self, state_machine):
        self.logger.info("Running Iterate update func")

        # transition to CheckTime state
        state_machine.curr_state = state_machine.check_time_state

class PerformEnsemble(State):
    '''
    PerformEnsemble runs the function associated with the current ensemble
    and then passes to Iterate
    '''
    def __init__(self):
        self.err_code = ErrorCode.no_err
        self.logger = get_logger("Perform Ensemble State")

    def process(self, state_machine):
        self.logger.info("Running PERFORM process func")

        # run the function of the current ensemble
        self.perform_ensemble_functions(state_machine.ens_index)

        self.logger.info("Done performing %s" % \
                state_machine.ens_list[state_machine.ens_index]['title'])

        now = time.localtime()
        curr_time_seconds = hms_to_seconds(now.tm_hour, now.tm_min, now.tm_sec)
        self.logger.info("Time is now seconds = %i" % curr_time_seconds)

    def update(self, state_machine):
        self.logger.info("Running PERFORM update func")
        # always transition to Iterate state
        state_machine.curr_state = state_machine.iterate_state

    def perform_ensemble_functions(self, ensemble_index: int,
                                    filename: str = "active_ensembles.json"):
        '''
        Function to call one non-member or static function.
        It is required that the json has the following parameters provided:
        title: "str"
        function: "dir/module:function_str"
        @param ensemble_index: index of the ensemble function being run
        @param filename: specifies file with ensemble specifications
        '''
        with open(filename, encoding="utf-8") as user_file: # TODO: don't reload
            file_contents = json.load(user_file)

        curr_ens = file_contents['ensemble_list'][ensemble_index]
        function = curr_ens["function"].split(":")

        module_dir = function[0] + ".py"
        module_name = function[0].split("/")[-1]

        function_name = function[-1]

        # Load module
        # TODO: test to confirm this works with external packages
        spec = importlib.util.spec_from_file_location(module_name, module_dir)
        module = importlib.util.module_from_spec(spec)

        spec.loader.exec_module(module)
        class_function = getattr(module, function_name)

        class_function()

class Sleep(State):
    '''
    Sleep calculates how much time is available to sleep once
    the need for sleep is confirmed. A hardware sleep will
    make the machine reset and wake up in WakeUp. A software
    sleep leads to CheckTime.
    '''

    def __init__(self):
        self.nearest_ens_time = 0
        self.err_code = ErrorCode.no_err
        self.logger = get_logger("Sleep State")

    def process(self, state_machine):
        self.logger.info("Running Sleep process func")

        # write curr index to ens file before calcs
        state_machine.ens["next_ensemble"] = state_machine.ens_index
        with open(state_machine.ens_filename, "w", encoding="utf-8") as f_out:
            json.dump(state_machine.ens, f_out, indent=4)

        now = time.localtime()
        curr_time_seconds = hms_to_seconds(now.tm_hour, now.tm_min, now.tm_sec)
        self.nearest_ens_time = state_machine.ens_list[state_machine.ens_index]["start_time"]

        self.logger.info("Next ensemble at %i and current time %i" % \
                (self.nearest_ens_time, curr_time_seconds))

    def update(self, state_machine):
        self.logger.info("Running Sleep update func")

        # recalc current_time vs (current_ensemble time + wakeup + shutdown)
        now = time.localtime()
        curr_time_seconds = hms_to_seconds(now.tm_hour, now.tm_min, now.tm_sec)
        if self.nearest_ens_time < curr_time_seconds:
            self.logger.info("Last ensemble finished, index reset; " + \
                            "next ens is on next day")
            time_left_today = SECONDS_IN_DAY - curr_time_seconds
            available_sleep_time = time_left_today + self.nearest_ens_time
        else:
            self.logger.info("Current time less than next ens; " + \
                            "next ens is on same day")
            available_sleep_time = self.nearest_ens_time - curr_time_seconds

        # if enough time, call shutdown
        if available_sleep_time > state_machine.wakeup_time + state_machine.shutdown_time:
            to_sleep = available_sleep_time - \
                    (state_machine.wakeup_time + state_machine.shutdown_time)
            self.logger.info("calling sleep timer's sleep(%i)" % to_sleep)
            state_machine.sleep_timer.sleep(to_sleep) # TODO: this will just be calling sleep, not sleep_timer.sleep
            time.sleep(1) # yield

            # Python sleep, sleep timer is offline
            self.logger.error("Sleep timer failed to shut tower down. Calling" \
                    + "Python's time.sleep for %i seconds" % available_sleep_time)
            time.sleep(to_sleep)

        else:
            # if not enough time, call Python sleep
            self.logger.info("Calling Python's time.sleep for %i seconds" % \
                    available_sleep_time)
            time.sleep(available_sleep_time)
            self.logger.info("Changing state to CheckTime")
            state_machine.curr_state = state_machine.check_time_state

class Error(State):
    '''
    Error reports errors and then sends the control back where
    it belongs, usually to Iterate
    '''

    def __init__(self):
        self.err_msgs = ["No error recorded\n",                             # 0
            "Skipping past missed ensemble.\n"]                             # 1

        self.err_code = ErrorCode.no_err
        self.logger = get_logger("Error State")

    def process(self, state_machine):
        self.logger.info("Running Error process func")

        now = time.localtime()
        curr_time_seconds = hms_to_seconds(now.tm_hour, now.tm_min, now.tm_sec)

        if self.err_code == ErrorCode.missed_ens:
            self.logger.info("Missed ensemble: %s" % \
                    state_machine.ens_list[state_machine.ens_index]['title'])
            self.logger.info("Current time: %i" % curr_time_seconds)
            self.logger.info("Ensemble target time: %i" % \
                    state_machine.ens_list[state_machine.ens_index]['start_time'])
            self.logger.error(self.err_msgs[ErrorCode.missed_ens.value])

    def update(self, state_machine):
        self.logger.info("Running Error update func")

        if state_machine.err_code == ErrorCode.missed_ens:
            state_machine.curr_state = Iterate()

class StateMachine:
    '''
    The StateMachine class holds the data that needs to be accessed
    from multiple states and runs an infinte loop of process and update
    '''

    def __init__(self, filename: str = "active_ensembles.json"): # TODO: make args ens list and sleep func
        self.day_of_ens = 0
        self.ens_filename = filename
        self.ens = ""
        self.ens_index = 0
        self.ens_list = ""
        self.daily_reset = False

        self.wake_up_state = WakeUp()
        self.check_time_state = CheckTime()
        self.iterate_state = Iterate()
        self.perform_ensemble_state = PerformEnsemble()
        self.sleep_state = Sleep()
        self.error_state = Error()
        self.curr_state = self.wake_up_state

        self.logger = get_logger("State Machine")
        self.__sleep_timer = None
        self.__wakeup_time = 5 # TODO: make defaults configurable or otherwise precalculate
        self.__shutdown_time = 5

    def run_machine(self):
        while True:
            self.curr_state.process(self)
            self.curr_state.update(self)

    @property
    def sleep_timer(self):
        return self.__sleep_timer

    @sleep_timer.setter
    def sleep_timer(self, sleep_timer):
        '''
        Set this state machine's sleep timer reference
        '''
        self.__sleep_timer = sleep_timer

    @property
    def wakeup_time(self):
        return self.__wakeup_time

    @wakeup_time.setter
    def wakeup_time(self, sec: int):
        if sec < self.__wakeup_time:
            self.logger.info("New wakeup time is less than previous!")
        self.__wakeup_time = sec

    @property
    def shutdown_time(self):
        return self.__shutdown_time

    @shutdown_time.setter
    def shutdown_time(self, sec: int):
        if sec < self.__shutdown_time:
            self.logger.info("New shutdown time is less than previous!")
        self.__shutdown_time = sec

def main():
    control_flow = StateMachine()
    control_flow.run_machine()

if __name__ == "__main__":
    main()
