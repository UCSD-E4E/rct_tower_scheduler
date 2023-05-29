# state machine design attempt by Dylan

# this uses classes to define the states and each one has two functions
# process() just does whatever calculation or action is required
# update() uses the current state and whatever was done during process()
# to figure out the next state
# at the bottom we just create a state machine object and run process()
# then update() in a permanent loop. The state machine itself can have
# variables that do the equivalent of the "event" from the other method

# this organization seemed to make more sense to me however I also
# trimmed the number of states and that can easily be applied to the
# previous state machine design if we would rather use that one


class State:
    def process(self, sm):
        pass

    def update(self, sm):
        pass


class WAKE_UP(State):
    def process(self, sm):
        # read active ensembles file
        print("WAKE_UP process func")

    def update(self, sm):
        # if active ensembles file not found or other reading with error,
        # transition to ERROR state

        # otherwise always
        # transition to CHECK_TIME state
        print("WAKE_UP update func")
        sm.state = CHECK_TIME()


class CHECK_TIME(State):
    def process(self, sm):
        # read time from ensemble and compare to current_time
        print("CHECK_TIME process func")

    def update(self, sm):
        # if current_time is passed current_ensemble time,
        # transition to ITERATE

        # if current_time == current_ensemble time,
        # transition to PERFORM_ENSEMBLE state

        # if current_time is less than current_ensemble time,
        # transition to SLEEP state
        print("CHECK_TIME update func")
        sm.state = ITERATE()


class ITERATE(State):
    def process(self, sm):
        # increment the current_ensemble variable
        print("ITERATE process func")

    def update(self, sm):
        # transition to CHECK_TIME state
        print("ITERATE update func")
        sm.state = PERFORM_ENSEMBLE()


class PERFORM_ENSEMBLE(State):
    def process(self, sm):
        # run the function of the current ensemble
        print("PERFORM process func")

    def update(self, sm):
        # always transition to ITERATE state
        print("PERFORM update func")
        sm.state = SLEEP()


class SLEEP(State):
    def process(self, sm):
        # recalculate current_time vs current_ensemble time + wakeup + shutdown time
        # write to active_ensembles (next_ensemble variable)
        print("SLEEP process func")

    def update(self, sm):
        # if not enough time, call python sleep timer then
        # transition to CHECK_TIME state

        # if enough time call shutdown, or
        # transfer to SHUTDOWN state if we want one just to call shutdown func
        print("SLEEP update func")
        sm.state = ERROR()


class ERROR(State):
    def process(self, sm):
        # print error message (and/or log it in a file?)
        # can also call ERROR if we skip ensembles if we can to log them
        print("ERROR process func")
        print("Current error message: " + sm.err_msg)

    def update(self, sm):
        # if calling because we can't read ensembles we can either try again
        # or shut down

        # if we call in because we want to log, then we can
        # transition to ITERATE state after this
        print("ERROR update func")

        # this line is only here to kill flow for demo purposes
        # BREAK is not a real state
        sm.state = BREAK()

        # this makes it loop if you want to watch it do that
        # sm.state = WAKE_UP()


class StateMachine:
    def __init__(self):
        self.err_msg = "No error"

        self.state = WAKE_UP()

    def run_machine(self):
        while True:
            self.state.process(self)
            self.state.update(self)


if __name__ == "__main__":
    control_flow = StateMachine()


    control_flow.run_machine()
