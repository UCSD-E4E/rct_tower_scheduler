from enum import Enum, auto

class ControlFlowStateMachine:

    currentState: int = -1

    class States(Enum):
        WAKE_UP = auto()
        READ_ACTIVE_ENSEMBLES = auto()
        CHECK_NEXT_ENSEMBLE_IS_SETUP = auto()
        SETUP = auto()
        CHECK_NEXT_ENSEMBLE_IS_TEARDOWN = auto()
        TEARDOWN = auto()
        ITERATE_NEXT_ENSEMBLE = auto()
        EXECUTE_NEXT_ENSEMBLE = auto()
        CHECK_NEXT_ENSEMBLE_PAST_CURR_TIME = auto()
        CHECK_NEXT_ENSEMBLE_TOO_CLOSE_TO_SLEEP = auto()
        SPINWAIT = auto()
        CALC_SLEEP_TIME = auto()
        SLEEP = auto()

    class Events(Enum):
        NO = auto()
        YES = auto()

    def update(self, event: Events):
        self.currentState = ControlFlowStateMachine.reducer(self.currentState, event)

    def reducer(self, currentState: States, event: Events):
        newState: self.States = currentState

        if (currentState == self.States.WAKE_UP):
            newState = self.States.READ_ACTIVE_ENSEMBLES

        elif (currentState == self.States.READ_ACTIVE_ENSEMBLES):
            newState = self.States.CHECK_NEXT_ENSEMBLE_IS_SETUP

        elif (currentState == self.States.CHECK_NEXT_ENSEMBLE_IS_SETUP):
            if (event == self.Events.YES):
                newState = self.States.SETUP
            elif (event == self.Events.NO): 
                newState = self.States.CHECK_NEXT_ENSEMBLE_IS_TEARDOWN

        elif (currentState == self.States.CHECK_NEXT_ENSEMBLE_IS_TEARDOWN):
            if (event == self.Events.YES):
                newState = self.States.TEARDOWN
            elif (event == self.Events.NO): 
                newState = self.States.EXECUTE_NEXT_ENSEMBLE

        elif (currentState == self.States.TEARDOWN):
            newState = self.States.SLEEP    

        elif (currentState == self.States.SETUP):
            newState = self.States.ITERATE_NEXT_ENSEMBLE

        elif (currentState == self.States.ITERATE_NEXT_ENSEMBLE):
            newState = self.States.CHECK_NEXT_ENSEMBLE_PAST_CURR_TIME

        elif (currentState == self.States.CHECK_NEXT_ENSEMBLE_PAST_CURR_TIME):
            if (event == self.Events.YES):
                newState = self.States.EXECUTE_NEXT_ENSEMBLE
            elif (event == self.Events.NO): 
                newState = self.States.CHECK_NEXT_ENSEMBLE_TOO_CLOSE_TO_SLEEP

        elif (currentState == self.States.EXECUTE_NEXT_ENSEMBLE):
            newState = self.States.ITERATE_NEXT_ENSEMBLE   

        elif (currentState == self.States.CHECK_NEXT_ENSEMBLE_TOO_CLOSE_TO_SLEEP):
            if (event == self.Events.YES):
                newState = self.States.SPINWAIT
            elif (event == self.Events.NO): 
                newState = self.States.CALC_SLEEP_TIME

        elif (currentState == self.States.SPINWAIT):
            newState = self.States.EXECUTE_NEXT_ENSEMBLE  

        elif (currentState == self.States.CALC_SLEEP_TIME):
            newState = self.States.SLEEP  

        elif (currentState == self.States.SLEEP):
            newState = self.States.WAKE_UP

        return newState


    def __init__(self):
        self.currentState = self.States.WAKE_UP

