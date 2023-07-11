import time

class mockedTimeSource:

    curr_time: float
    real_time: float

    def __init__(self):
        self.curr_time = time.time()
        self.real_time = self.curr_time

    def resetTime(self):
        self.curr_time = time.time()
        self.real_time = self.curr_time

    def setTime(self, new_time: float):
        self.curr_time = new_time
        self.real_time = time.time()

    def sleep(self, sleep_time: float):
        self.curr_time += sleep_time
    
    def getTime(self):
        timePassed = time.time() - self.real_time
        return self.curr_time + timePassed
