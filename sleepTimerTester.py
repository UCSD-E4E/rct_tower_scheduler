#!/usr/bin/python3

import logging
import math
from multiprocessing import shared_memory
import os
import signal
import sys
import time

from state_machine_design import StateMachine

class SleepTimerTester:
    '''
    SleepTimer object specifically for testing. This should inherit from
    SleepTimer once that package is completed. Scheduler can be run with any
    SleepTimer object, which, in this case, is our tester.
    '''
    def __init__(self):
        self.memory = None
        self.starttime = 0

    def sleep(self, sec: int):
        '''
        Set this sleep timer's memory to store a number of seconds for which to
        sleep. Memory must have already been set before calling this function.
        @param sec: number of seconds to sleep
        '''
        self.sleeptime_memory.buf[:] = sec.to_bytes(4, "big")
        self.starttime_memory.buf[:] = int(time.time()).to_bytes(8, "big")

    def set_sleeptime_memory(self, memory: shared_memory.SharedMemory):
        '''
        Assign shared memory to this sleep timer, so it has a section of memory
        which our parent process can use to access sleep length.
        @param memory: SharedMemory with a size of 4 bytes (to store one int)
        '''
        self.sleeptime_memory = memory

    def set_starttime_memory(self, memory: shared_memory.SharedMemory):
        '''
        Assign shared memory to this sleep timer, so it has a section of memory
        which our parent process can use to access beginning of shutdown time.
        @param memory: SharedMemory with a size of 8 bytes (to store one long)
        '''
        self.starttime_memory = memory

def main():
    logger = logging.getLogger("sleep_timer_tester")
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s: %(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    sleep_timer = SleepTimerTester()
    
    sleeptime_memory = shared_memory.SharedMemory(create=True, size=4)
    sleep_timer.set_sleeptime_memory(sleeptime_memory)

    starttime_memory = shared_memory.SharedMemory(create=True, size=8)
    sleep_timer.set_starttime_memory(starttime_memory)

    starttime = time.time()
    wakeup = 5 # starting value for wakeup time, can inc
    shutdown = 5 # starting value for shutdown time, can inc
    new_pid = -1

    # constant to add to calculated wakeup and shutdown times, to be safe
    BUFFER_TIME = 2

    try:
        while True:
            logger.debug("running scheduler once")

            # start scheduler by forking new thread running scheduler.py
            new_pid = os.fork()
            if new_pid == 0:
                # run scheduler.py
                scheduler = StateMachine()
                scheduler.set_sleep_timer(sleep_timer)
                scheduler.set_wakeup(wakeup)
                scheduler.set_shutdown(shutdown)

                endtime = time.time()
                wakeup = max(math.ceil(endtime - starttime + BUFFER_TIME), wakeup)
                logger.info("WAKEUP TIME: " + str(wakeup) + " seconds")

                scheduler.run_machine()
                #os.execl("./state_machine_design.py", "./state_machine_design.py")
            else:
                # wait for command sleep(x)
                while int.from_bytes(sleeptime_memory.buf[:], "big") == 0:
                    time.sleep(1)

                # shut down scheduler by killing child process running it
                os.kill(new_pid, signal.SIGKILL)
                starttime = int.from_bytes(starttime_memory.buf[:], "big")
                endtime = time.time()
                shutdown = max(math.ceil(endtime - starttime + BUFFER_TIME), shutdown)
                logger.info("SHUTDOWN TIME: " + str(shutdown) + " seconds")

                # sleep on daemon before rerunning scheduler in next iteration
                logger.info("sleeping for " + str(int.from_bytes(sleeptime_memory.buf[:], "big")))
                time.sleep(int.from_bytes(sleeptime_memory.buf[:], "big"))
                starttime = time.time()
                sleeptime_memory.buf[:] = int(0).to_bytes(4, "big")

    except KeyboardInterrupt:
        if new_pid > 0:
            print("")
            logger.info("received interrupt from user, exiting now...")
            os.kill(new_pid, signal.SIGKILL)
            sleeptime_memory.close()
            starttime_memory.close()
            sleeptime_memory.unlink()
            starttime_memory.unlink()

if __name__ == '__main__':
    main()
