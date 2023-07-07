'''
state machine design attempt by Dylan

this uses classes to define the states and each one has two functions
process() just does whatever calculation or action is required
update() uses the current state and whatever was done during process()
to figure out the next state
at the bottom we just create a state machine object and run process()
then update() in a permanent loop.
'''

import json
import logging
import sys
import time

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


TIME_SHUTDOWN = 5 # find real shutdown and wakeup times later
TIME_WAKEUP = 5

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
        The process function for each state does what the state is meant to accomplish.
        To be overwritten in each state.
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
        logging.info("Running WAKE_UP process func")

        # read active ensembles file
        try:
            with open(sm.ens_filename, "r", encoding="utf-8") as f_in:
                sm.ens = json.load(f_in)

            f_in.close()
            # f = open(sm.ens_filename)
            # sm.ens = json.load(f)
            # f.close()
            sm.ens_index = sm.ens["next_ensemble"]
            sm.ens_list = sm.ens["ensemble_list"]
        except:
            sm.err_code = NO_ENS_FILE

        now = time.localtime()
        curr_time_seconds = hms_to_seconds(now.tm_hour, now.tm_min, now.tm_sec)

        logging.info(f"Waking up at: curr_time_seconds = {str(curr_time_seconds)}")

    def update(self, sm):
        logging.info("Running WAKE_UP update func")
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
        logging.info("Running CHECK_TIME process func")
        logging.info(f"Current ens index = {str(sm.ens_index)}")

        # this is a small window where if the scheduler wakes up
        # slightly early from sleep we allow it to run the ensemble anyway
        TIME_BUFFER = 5

        if sm.ens_index < len(sm.ens_list):
            # read time from ensemble and compare to current_time
            now = time.localtime()
            curr_time_seconds = hms_to_seconds(now.tm_hour, now.tm_min, now.tm_sec)

            nearest_ens_time = sm.ens_list[sm.ens_index]["start_time"]

                
            if nearest_ens_time < curr_time_seconds:
                logging.info("Time is past current ens, checking if should skip")
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
                logging.info(f"Correct time for ensemble: {sm.ens_list[sm.ens_index]['title']}")
                self.check_time_ctrl = RUN
            else:
                logging.info(f"ensemble {sm.ens_list[sm.ens_index]['title']} is still in future, go to sleep")
                self.check_time_ctrl = WAIT

            sm.day_of_ens = now.tm_wday
            sm.rst = False
        else:
            logging.info("Index beyond last ens, resetting")
            self.check_time_ctrl = RESET
            sm.ens_index = 0
            sm.rst = True


    def update(self, sm):
        logging.info("Running CHECK_TIME update func")

        # if current_time is passed current_ensemble time,
        # transition to ITERATE
        if self.check_time_ctrl == SKIP:
            # sm.state = ITERATE() # switch with below line to disable error log on skip
            sm.state = ERROR() # do we want to log this as error then recover?
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
        logging.info("Running ITERATE process func")

        # increment the current_ensemble variable
        sm.ens_index += 1

    def update(self, sm):
        logging.info("Running ITERATE update func")

        # transition to CHECK_TIME state
        sm.state = CHECK_TIME()


class PERFORM_ENSEMBLE(State):
    '''
    PERFORM_ENSEMBLE runs the function associated with the current ensemble
    and then passes to ITERATE
    '''

    def process(self, sm):
        logging.info("Running PERFORM process func")
        # run the function of the current ensemble

        logging.info(f"Finished perform_ens of {sm.ens_list[sm.ens_index]['title']}")

        now = time.localtime()
        curr_time_seconds = hms_to_seconds(now.tm_hour, now.tm_min, now.tm_sec)
        logging.info(f"Time is now curr_time_seconds = {str(curr_time_seconds)}")

    def update(self, sm):
        logging.info("Running PERFORM update func")
        # always transition to ITERATE state
        sm.state = ITERATE()


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
        logging.info("Running SLEEP process func")

        seconds_in_day = 86400

        # check if sleep timer is online or not
        # sleep_timer_responsive = sleepTimer.checkResponsive()


        # recalculate current_time vs current_ensemble time + wakeup + shutdown time
        # write to active_ensembles (next_ensemble variable)
        now = time.localtime()
        curr_time_seconds = hms_to_seconds(now.tm_hour, now.tm_min, now.tm_sec)

        nearest_ens_time = sm.ens_list[sm.ens_index]["start_time"]

        logging.info("Inside SLEEP process, " + 
                    f"with next ensemble: {str(nearest_ens_time)} " +
                    f"and current time: {str(curr_time_seconds)}")

        if nearest_ens_time < curr_time_seconds:
            logging.info("Last ensemble finished, index reset; next ens is on next day")
            time_left_today = seconds_in_day - curr_time_seconds
            self.available_sleep_time = time_left_today + nearest_ens_time
        else:
            logging.info("Current time less than next ens; next ens is on same day")
            self.available_sleep_time = nearest_ens_time - curr_time_seconds


    def update(self, sm):
        logging.info("Running SLEEP update func")

        # if enough time call shutdown, or
        # transfer to SHUTDOWN state if we want one just to call shutdown func
        if self.available_sleep_time >= TIME_WAKEUP + TIME_SHUTDOWN:
            if self.sleep_timer_responsive == True:
                # write curr index to ens file then sleep
                sm.ens["next_ensemble"] = sm.ens_index

                with open(sm.ens_filename, "w", encoding="utf-8") as f_out:
                    json.dump(sm.ens, f_out, indent=4)

                f_out.close()

                # someRefToSleepTimer.sleep(sleep_time)

            else:
                # Python sleep with full time, sleep timer is offline
                # we sleep here then change to ERROR to report sleep timer problem
                logging.info(f"Calling sleep timer for {str(self.available_sleep_time)} seconds")
                time.sleep(self.available_sleep_time) # Wait using Python sleep
                sm.err_code = TIMER_OFFLINE
                sm.state = ERROR()

        else:
            # if not enough time, call python sleep timer then
            # transition to CHECK_TIME state
            logging.info(f"Calling sleep timer for {str(self.available_sleep_time)} seconds")
            time.sleep(self.available_sleep_time) # Wait using Python sleep
            logging.info(f"Changing state to CHECK_TIME")
            sm.state = CHECK_TIME()


class ERROR(State):
    '''
    ERROR reports errors and then sends the control back where
    it belongs, usually to ITERATE
    '''

    def __init__(self):
        self.err_msgs = ["No error recorded\n",                                          # 0
                         "No active_ensembles.json file found. Unable to continue.\n",   # 1
                         "Skipping past missed ensemble.\n",                             # 2
                         "Hardware timer unresponsive. Defaulting to software sleep.\n"] # 3


    def process(self, sm):
        # Logs errors, could output to file also?
        # can also call ERROR if we skip ensembles if we can to log them
        logging.info(f"Running ERROR process func")

        now = time.localtime()
        curr_time_seconds = hms_to_seconds(now.tm_hour, now.tm_min, now.tm_sec)

        if sm.err_code == NO_ENS_FILE:
            logging.error(self.err_msgs[NO_ENS_FILE])
        elif sm.err_code == MISSED_ENS:
            logging.info(f"Missed ensemble: {sm.ens_list[sm.ens_index]['title']}")
            logging.info(f"Current time: {str(curr_time_seconds)}")
            logging.info(f"Ensemble target time: {str(sm.ens_list[sm.ens_index]['start_time'])}")
            logging.error(self.err_msgs[MISSED_ENS])
        elif sm.err_code == TIMER_OFFLINE:
            logging.error(self.err_msgs[TIMER_OFFLINE])

    def update(self, sm):
        logging.info(f"Running ERROR update func")

        if sm.err_code == NO_ENS_FILE:
            sys.exit()
        elif sm.err_code == MISSED_ENS:
            sm.state = ITERATE()
        elif sm.err_code == TIMER_OFFLINE:
            # the SLEEP state handles the software sleep so ERROR
            # just logs the error then passes back to ITERATE
            sm.state = CHECK_TIME()


class StateMachine:
    '''
    The StateMachine class holds the data that needs to be accessed
    from multiple states and runs an infinte loop of process and update
    '''

    def __init__(self):
        self.day_of_ens = 0
        self.err_code = NO_ERR
        self.ens_filename = "active_ensembles.json"
        self.ens = ""
        self.ens_index = 0
        self.ens_list = ""
        self.rst = False
        self.state = WAKE_UP()

    def run_machine(self):
        while True:
            self.state.process(self)
            self.state.update(self)


if __name__ == "__main__":
    control_flow = StateMachine()


    control_flow.run_machine()
