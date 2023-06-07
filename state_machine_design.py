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
import time
import sys

# variables for selecting path in CHECK_TIME state
SKIP = 0
NOW = 1
WAIT = 2
RESET = 3

# variables for handling and recovering in ERROR state
NO_ERR = 0
NO_ENS_FILE = 1
MISSED_ENS = 2
TIMER_OFFLINE = 3


TIME_SHUTDOWN = 5 # find real shutdon and wakeup times later
TIME_WAKEUP = 5

def hmsToSeconds(hour: int, min: int, sec: int):
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
        print("WAKE_UP process func")

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
            sm.err_msg = "active_ensembles.json not found"

        now = time.localtime()
        curr_time_seconds = hmsToSeconds(now.tm_hour, now.tm_min, now.tm_sec)

        print("waking up at: " + str(curr_time_seconds))

    def update(self, sm):
        print("WAKE_UP update func")
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
        print("CHECK_TIME process func")
        print("ens index: " + str(sm.ens_index))

        if sm.ens_index < len(sm.ens_list):
            # read time from ensemble and compare to current_time
            now = time.localtime()
            curr_time_seconds = hmsToSeconds(now.tm_hour, now.tm_min, now.tm_sec)

            nearest_ens_time = sm.ens_list[sm.ens_index]["start_time"]

            if nearest_ens_time < curr_time_seconds:
                print("time past current ens, skipping")
                self.check_time_ctrl = SKIP
                sm.err_code = MISSED_ENS
                # sm.err_msg = "Current ensemble past time, skipping ensemble "
                # + sm.ens_list[sm.ens_index]["title"] + " at " + curr_time_seconds
            elif nearest_ens_time == curr_time_seconds:
                print("correct time for ensemble: " + sm.ens_list[sm.ens_index]["title"])
                self.check_time_ctrl = NOW
            else:
                print("ensemble " + sm.ens_list[sm.ens_index]["title"] +
                      " is still in future, go to sleep")
                self.check_time_ctrl = WAIT
        else:
            print("index beyond last ens, resetting")
            self.check_time_ctrl = RESET
            sm.ens_index = 0


    def update(self, sm):
        print("CHECK_TIME update func")

        # if current_time is passed current_ensemble time,
        # transition to ITERATE
        if self.check_time_ctrl == SKIP:
            # sm.state = ITERATE() # switch with below line to disable error log on skip
            sm.state = ERROR() # do we want to log this as error then recover?
        # if current_time == current_ensemble time,
        # transition to PERFORM_ENSEMBLE state
        elif self.check_time_ctrl == NOW:
            sm.state = PERFORM_ENSEMBLE()
        # if current_time is less than current_ensemble time,
        # transition to SLEEP state
        elif self.check_time_ctrl == WAIT:
            sm.state = SLEEP()
        # if all ensembles are done, need to sleep til first one of next day
        elif self.check_time_ctrl == RESET:
            sm.state = SLEEP()


class ITERATE(State):
    '''
    ITERATE just increases the index by one then passes
    back to CHECK_TIME
    '''

    def process(self, sm):
        print("ITERATE process func")

        # increment the current_ensemble variable
        sm.ens_index += 1

    def update(self, sm):
        print("ITERATE update func")

        # transition to CHECK_TIME state
        sm.state = CHECK_TIME()


class PERFORM_ENSEMBLE(State):
    '''
    PERFORM_ENSEMBLE runs the function associated with the current ensemble
    and then passes to ITERATE
    '''

    def process(self, sm):
        print("PERFORM process func")
        # run the function of the current ensemble

        print("inside perform_ens for: " + sm.ens_list[sm.ens_index]["title"])

        now = time.localtime()
        curr_time_seconds = hmsToSeconds(now.tm_hour, now.tm_min, now.tm_sec)
        print("time is: " + str(curr_time_seconds))
        print("now leaving")

    def update(self, sm):
        print("PERFORM update func")
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
        print("SLEEP process func")

        seconds_in_day = 86400

        # check if sleep timer is online or not
        # sleep_timer_responsive = sleepTimer.checkResponsive()


        # recalculate current_time vs current_ensemble time + wakeup + shutdown time
        # write to active_ensembles (next_ensemble variable)
        now = time.localtime()
        curr_time_seconds = hmsToSeconds(now.tm_hour, now.tm_min, now.tm_sec)

        nearest_ens_time = sm.ens_list[sm.ens_index]["start_time"]

        print("inside sleep")
        print("next ensemble: " + str(nearest_ens_time))
        print("current time: " + str(curr_time_seconds))

        if nearest_ens_time < curr_time_seconds:
            print("should be here after last ensemble finishes and " +
                  "index resets; next ens is on next day")
            time_left_today = seconds_in_day - curr_time_seconds
            self.available_sleep_time = time_left_today + nearest_ens_time
        else:
            print("should be here if current time is less than next ens; next ens is on same day")
            self.available_sleep_time = nearest_ens_time - curr_time_seconds


    def update(self, sm):
        print("SLEEP update func")

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
                print("calling sleep timer for " + str(self.available_sleep_time) + " seconds")
                time.sleep(self.available_sleep_time) # Wait using Python sleep
                sm.err_code = TIMER_OFFLINE
                sm.state = ERROR()

        else:
            # if not enough time, call python sleep timer then
            # transition to CHECK_TIME state
            print("calling sleep timer for " + str(self.available_sleep_time) + " seconds")
            time.sleep(self.available_sleep_time) # Wait using Python sleep
            print("changing state to CHECK_TIME")
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
        # print error message (and/or log it in a file?)
        # can also call ERROR if we skip ensembles if we can to log them
        print("ERROR process func")

        now = time.localtime()
        curr_time_seconds = hmsToSeconds(now.tm_hour, now.tm_min, now.tm_sec)

        if sm.err_code == NO_ENS_FILE:
            print(self.err_msgs[NO_ENS_FILE])
        elif sm.err_code == MISSED_ENS:
            print("Missed ensemble " + sm.ens_list[sm.ens_index]["title"])
            print("Current time: " + str(curr_time_seconds))
            print("Ensemble target time: " + str(sm.ens_list[sm.ens_index]["start_time"]))
            print(self.err_msgs[MISSED_ENS])
        elif sm.err_code == TIMER_OFFLINE:
            print(self.err_msgs[TIMER_OFFLINE])

    def update(self, sm):
        print("ERROR update func")

        if sm.err_code == NO_ENS_FILE:
            sys.exit()
        elif sm.err_code == MISSED_ENS:
            sm.state = ITERATE()
        elif sm.err_code == TIMER_OFFLINE:
            # the SLEEP state handles the software sleep so ERROR
            # just logs the error then passes back to ITERATE
            sm.state = ITERATE()


class StateMachine:
    '''
    The StateMachine class holds the data that needs to be accessed
    from multiple states and runs an infinte loop of process and update
    '''

    def __init__(self):
        self.err_code = NO_ERR
        self.ens_filename = "active_ensembles.json"
        self.ens = ""
        self.ens_index = 0
        self.ens_list = ""
        self.state = WAKE_UP()

    def run_machine(self):
        while True:
            self.state.process(self)
            self.state.update(self)


if __name__ == "__main__":
    control_flow = StateMachine()


    control_flow.run_machine()
