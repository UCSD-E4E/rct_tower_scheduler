from enum import Enum, auto

class ControlFlowStateMachine:

    currentState: int = -1

    class States(Enum):
        WAKE_UP = auto()
        SETUP = auto()
        ITERATE_ENSEMBLES = auto()
        SLEEP = auto()
        SHUTDOWN = auto()

    class Events(Enum):
        ENSEMBLE_SET_UP_TRUE = auto()
        ENSEMBLE_SET_UP_FALSE = auto()

        CAN_SLEEP = auto()
        EXECUTE_NEXT = auto()

        CAN_SHUTDOWN_TRUE = auto()
        CAN_SHUTDOWN_FALSE = auto()

    def update(self, event: Events):
        self.currentState = ControlFlowStateMachine.reducer(self.currentState, event)

    def reducer(self, currentState: States, event: Events):
        newState: self.States = currentState

        if (currentState == self.States.WAKE_UP):
            if (event == self.Events.ENSEMBLE_SET_UP_FALSE):
                newState = self.States.SETUP
            elif (event == self.Events.ENSEMBLE_SET_UP_TRUE):
                newState = self.States.ITERATE_ENSEMBLES
        
        elif (currentState == self.States.SETUP):
            newState = self.States.ITERATE_ENSEMBLES

        elif (currentState == self.States.ITERATE_ENSEMBLES):
            if (event == self.Events.CAN_SLEEP):
                newState = self.States.SLEEP
            # NOTE: This event encapsulates two scenarios
            #       1. Missed execution time and skipped ensemble
            #       2. Executed ensemble
            elif (event == self.Events.EXECUTE_NEXT):
                newState = self.States.ITERATE_ENSEMBLES

        elif (currentState == self.States.SLEEP):
            if (event == self.Events.CAN_SHUTDOWN_FALSE):
                newState = self.States.ITERATE_ENSEMBLES
            elif (event == self.Events.CAN_SHUTDOWN_TRUE):
                newState = self.States.SHUTDOWN

        return newState


    def __init__(self):
        self.currentState = self.States.WAKE_UP

