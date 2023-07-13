#!/usr/bin/python3

import datetime
import importlib.util
import json
import logging
import sys
import time

# TODO: consider using enums for path and error constants

# variables for selecting path in CHECK_TIME state
SKIP = 0
RUN = 1
WAIT = 2
RESET = 3

# variables for handling and recovering in ERROR state
NO_ERR = 0
NO_ENS_FILE = 1
MISSED_ENS = 2
TIMER_OFFLINE = 3

def hms_to_seconds(hour: int, min: int, sec: int):
    '''
    Convert hours, minutes, and seconds to just seconds

    @param hour: number of hours to convert to sec
    @param min: number of minutes to convert to sec
    @param sec: number of seconds

    return: sum of seconds in hour, min, and sec
    '''

    return sec + min * 60 + hour * 3600

class State:
    '''
    Although each state is divided into process and update, they aren't
    always perfectly decoupled. Sometimes the update functioning has to
    do a bit of processing to make its determination. The example of that
    would be the SLEEP state which calls into sleep then picks a new state.
    '''

    def process(self, sm):
        '''
        The process function for each state does what the state is meant to
        accomplish. To be overwritten in each state.
        '''

    def update(self, sm):
        '''
        The update function for each state selects the state to transition to.
        To be overwritten in each state.
        '''


class WAKE_UP(State):
    '''
    The WAKE_UP state is always the first state to run.
    It makes sure we actually have a file we can run and
    then passes control to CHECK_TIME.
    '''

    def process(self, sm):
        sm.logger.info("Running WAKE_UP process func")

        # read active ensembles file
        try:
            with open(sm.ens_filename, "r", encoding="utf-8") as f_in:
                sm.ens = json.load(f_in)

            sm.ens_index = sm.ens["next_ensemble"]
            sm.ens_list = sm.ens["ensemble_list"]
        except:
            sm.err_code = NO_ENS_FILE

        now = time.localtime()
        curr_time_seconds = hms_to_seconds(now.tm_hour, now.tm_min, now.tm_sec)

        sm.logger.info(f"Waking up at seconds = {str(curr_time_seconds)}")

    def update(self, sm):
        sm.logger.info("Running WAKE_UP update func")
        # if active ensembles file not found or other reading with error,
        # transition to ERROR state
        if sm.err_code != NO_ERR:
            sm.state = ERROR()
        else:
            # otherwise always
            # transition to CHECK_TIME state
            sm.state = CHECK_TIME()

class CHECK_TIME(State):
    '''
    CHECK_TIME determines if the machine should skip an ensemble,
    run an ensemble, or sleep until the next ensemble.
    '''

    def __init__(self):
        self.check_time_ctrl = SKIP

    def process(self, sm):
        sm.logger.info("Running CHECK_TIME process func")
        sm.logger.info(f"Current ens index = {str(sm.ens_index)}")

        # this is a small window where if the scheduler wakes up
        # slightly early from sleep we allow it to run the ensemble anyway
        TIME_BUFFER = 5

        if sm.ens_index < len(sm.ens_list):
            # read time from ensemble and compare to current_time
            now = time.localtime()
            curr_time_seconds = hms_to_seconds(now.tm_hour, now.tm_min,
                                                now.tm_sec)

            nearest_ens_time = sm.ens_list[sm.ens_index]["start_time"]

            if nearest_ens_time < curr_time_seconds:
                sm.logger.info("Time is past current ens, checking for skip")
                if sm.rst == True:
                    if now.tm_wday == sm.day_of_ens:
                        self.check_time_ctrl = WAIT
                    else:
                        self.check_time_ctrl = SKIP
                        sm.err_code = MISSED_ENS
                else:
                    self.check_time_ctrl = SKIP
                    sm.err_code = MISSED_ENS
            elif nearest_ens_time <= curr_time_seconds + TIME_BUFFER:
                sm.logger.info("Correct time for ensemble: " + \
                                f"{sm.ens_list[sm.ens_index]['title']}")
                self.check_time_ctrl = RUN
            else:
                sm.logger.info(f"ensemble {sm.ens_list[sm.ens_index]['title']} " \
                                + "is still in future, go to sleep")
                self.check_time_ctrl = WAIT

            sm.day_of_ens = now.tm_wday
            sm.rst = False
        else:
            sm.logger.info("Index beyond last ens, resetting")
            self.check_time_ctrl = RESET
            sm.ens_index = 0
            sm.rst = True

    def update(self, sm):
        sm.logger.info("Running CHECK_TIME update func")

        # if current_time is passed current_ensemble time,
        # transition to ITERATE
        if self.check_time_ctrl == SKIP:
            sm.state = ERROR()

        # if current_time == current_ensemble time,
        # transition to PERFORM_ENSEMBLE state
        elif self.check_time_ctrl == RUN:
            sm.state = PERFORM_ENSEMBLE()

        # if current_time is less than current_ensemble time,
        # transition to SLEEP state
        elif self.check_time_ctrl == WAIT:
            sm.state = SLEEP()

        # if all ensembles are done, need to sleep til first one of next day
        elif self.check_time_ctrl == RESET:
            sm.state = CHECK_TIME()

class ITERATE(State):
    '''
    ITERATE just increases the index by one then passes
    back to CHECK_TIME
    '''

    def process(self, sm):
        sm.logger.info("Running ITERATE process func")

        # increment the current_ensemble variable
        sm.ens_index += 1

    def update(self, sm):
        sm.logger.info("Running ITERATE update func")

        # transition to CHECK_TIME state
        sm.state = CHECK_TIME()

class PERFORM_ENSEMBLE(State):
    '''
    PERFORM_ENSEMBLE runs the function associated with the current ensemble
    and then passes to ITERATE
    '''

    def process(self, sm):
        sm.logger.info("Running PERFORM process func")

        # run the function of the current ensemble
        self.perform_ensemble_functions(sm.ens_index)

        sm.logger.info(f"Done performing {sm.ens_list[sm.ens_index]['title']}")

        now = time.localtime()
        curr_time_seconds = hms_to_seconds(now.tm_hour, now.tm_min, now.tm_sec)
        sm.logger.info(f"Time is now seconds = {str(curr_time_seconds)}")

    def update(self, sm):
        sm.logger.info("Running PERFORM update func")
        # always transition to ITERATE state
        sm.state = ITERATE()

    def perform_ensemble_functions(self, ensemble_index: int,
                                    filename: str = "active_ensembles.json"):
        '''
        Function to call one non-member or static function.
        It is required that the json has the following parameters provided:
        title: "str"
        function: "dir/module:function_str"
        inputs: [Any]
        @param ensemble_index: index of the ensemble function being run
        @param filename: specifies file with ensemble specifications
        '''
        with open(filename, encoding="utf-8") as user_file: # TODO: don't reload
            file_contents = json.load(user_file)

        curr_ens = file_contents['ensemble_list'][ensemble_index]
        function = curr_ens["function"].split(":")
        function_inputs = curr_ens["inputs"]

        module_dir = function[0] + ".py"
        module_name = function[0].split("/")[-1]

        function_name = function[-1]

        # Load module
        spec = importlib.util.spec_from_file_location(module_name, module_dir)
        module = importlib.util.module_from_spec(spec)

        spec.loader.exec_module(module)
        class_function = getattr(module, function_name)

        class_function(*function_inputs)

class SLEEP(State):
    '''
    SLEEP calculates how much time is available to sleep once
    the need for sleep is confirmed. A hardware sleep will
    make the machine reset and wake up in WAKE_UP. A software
    sleep leads to CHECK_TIME.
    '''

    def __init__(self):
        self.sleep_timer_responsive = False
        self.available_sleep_time = 0

    def process(self, sm):
        sm.logger.info("Running SLEEP process func")

        seconds_in_day = 86400

        # TODO: check if sleep timer is online or not
        # sleep_timer_responsive = sleepTimer.checkResponsive()

        # recalc current_time vs (current_ensemble time + wakeup + shutdown)
        now = time.localtime()
        curr_time_seconds = hms_to_seconds(now.tm_hour, now.tm_min, now.tm_sec)

        nearest_ens_time = sm.ens_list[sm.ens_index]["start_time"]

        sm.logger.info("Inside SLEEP process, "  + \
                    f"with next ensemble: {str(nearest_ens_time)} " + \
                    f"and current time: {str(curr_time_seconds)}")

        if nearest_ens_time < curr_time_seconds:
            sm.logger.info("Last ensemble finished, index reset; " + \
                            "next ens is on next day")
            time_left_today = seconds_in_day - curr_time_seconds
            self.available_sleep_time = time_left_today + nearest_ens_time
        else:
            sm.logger.info("Current time less than next ens; " + \
                            "next ens is on same day")
            self.available_sleep_time = nearest_ens_time - curr_time_seconds

    def update(self, sm):
        sm.logger.info("Running SLEEP update func")

        # if enough time call shutdown, or
        # transfer to SHUTDOWN state if we want one just to call shutdown func
        if self.available_sleep_time > sm.wakeup_time + sm.shutdown_time:
            if self.sleep_timer_responsive == True:
                # write curr index to ens file then sleep
                sm.ens["next_ensemble"] = sm.ens_index

                with open(sm.ens_filename, "w", encoding="utf-8") as f_out:
                    json.dump(sm.ens, f_out, indent=4)

                to_sleep = self.available_sleep_time - \
                        (sm.wakeup_time + sm.shutdown_time)
                sm.logger.info(f"calling sleep timer's sleep({to_sleep})")
                sm.sleep_timer.sleep(to_sleep)
                time.sleep(1)

            else:
                # Python sleep with full time, sleep timer is offline
                # proceed to ERROR to report sleep timer problem
                sm.logger.info("Calling Python's time.sleep for " + \
                                f"{str(self.available_sleep_time)} seconds")
                time.sleep(self.available_sleep_time)
                sm.err_code = TIMER_OFFLINE
                sm.state = ERROR()

        else:
            # if not enough time, call Python sleep
            sm.logger.info("Calling Python's time.sleep for " + \
                            f"{str(self.available_sleep_time)} seconds")
            time.sleep(self.available_sleep_time)
            sm.logger.info(f"Changing state to CHECK_TIME")
            sm.state = CHECK_TIME()

class ERROR(State):
    '''
    ERROR reports errors and then sends the control back where
    it belongs, usually to ITERATE
    '''

    def __init__(self):
        self.err_msgs = ["No error recorded\n",                             # 0
            "No active_ensembles.json file found. Unable to continue.\n",   # 1
            "Skipping past missed ensemble.\n",                             # 2
            "Hardware timer unresponsive. Defaulting to software sleep.\n"] # 3

    def process(self, sm):
        sm.logger.info(f"Running ERROR process func")

        now = time.localtime()
        curr_time_seconds = hms_to_seconds(now.tm_hour, now.tm_min, now.tm_sec)

        if sm.err_code == NO_ENS_FILE:
            sm.logger.error(self.err_msgs[NO_ENS_FILE])
        elif sm.err_code == MISSED_ENS:
            sm.logger.info("Missed ensemble: " + \
                            f"{sm.ens_list[sm.ens_index]['title']}")
            sm.logger.info(f"Current time: {str(curr_time_seconds)}")
            sm.logger.info("Ensemble target time: " + \
                            f"{str(sm.ens_list[sm.ens_index]['start_time'])}")
            sm.logger.error(self.err_msgs[MISSED_ENS])
        elif sm.err_code == TIMER_OFFLINE:
            sm.logger.error(self.err_msgs[TIMER_OFFLINE])

    def update(self, sm):
        sm.logger.info(f"Running ERROR update func")

        if sm.err_code == NO_ENS_FILE:
            sys.exit()
        elif sm.err_code == MISSED_ENS:
            sm.state = ITERATE()
        elif sm.err_code == TIMER_OFFLINE:
            # SLEEP state handles software sleep, so ERROR just logs then
            # passes back to CHECK_TIME
            sm.state = CHECK_TIME()

class StateMachine:
    '''
    The StateMachine class holds the data that needs to be accessed
    from multiple states and runs an infinte loop of process and update
    '''

    def __init__(self, filename: str = "active_ensembles.json"):
        self.day_of_ens = 0
        self.err_code = NO_ERR
        self.ens_filename = filename
        self.ens = ""
        self.ens_index = 0
        self.ens_list = ""
        self.rst = False
        self.state = WAKE_UP()

        self.logger = self.get_logger()
        self.__sleep_timer = None
        self.__wakeup_time = 5
        self.__shutdown_time = 5

    def run_machine(self):
        while True:
            self.state.process(self)
            self.state.update(self)

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
        if (sec < self.__wakeup_time):
            sm.logger.info("new wakeup time is less than previous!")
        self.__wakeup_time = sec

    @property
    def shutdown_time(self):
        return self.__shutdown_time

    @shutdown_time.setter
    def shutdown_time(self, sec: int):
        if (sec < self.__shutdown_time):
            sm.logger.info("new shutdown time is less than previous!")
        self.__shutdown_time = sec

    def get_logger(self):
        # TODO: allow easier configuration of logger via config file
        logger = logging.getLogger("sleep_scheduler")
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(levelname)s: %(name)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

def main():
    control_flow = StateMachine()
    control_flow.run_machine()

if __name__ == "__main__":
    main()
