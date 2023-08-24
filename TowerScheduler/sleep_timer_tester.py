'''
Module to facilitate testing the sleep timer scheduler found in scheduler.py.
This includes a mock SleepTimer class and a main loop to fork a new process
running our scheduler state machine, which the parent process will kill when
the sleep function is called. Killing the child process and forking a new one
will simulate shutting down the tower (and, with it, the scheduler), then waking
it up for a new run at the appropriate time.

This module should not be considered a testbench in itself but rather a tool to
simulate an entire tower, controlled by a sleep timer to start execution of the
scheduler and kill the scheduler's process when sleep() is called.
'''

import math
import os
import signal
import struct
import sys
import time
from multiprocessing import shared_memory

from TowerScheduler.ensemble import Ensemble
from TowerScheduler.scheduler import StateMachine
from TowerScheduler.util import get_logger


class SleepTimerTester:
    '''
    SleepTimer object specifically for testing. This tester object's sleep
    function may be passed in to initialize a StateMachine in scheduler.py.
    '''
    def __init__(self):
        self.starttime_memory: shared_memory.SharedMemory = None
        self.sleeptime_memory: shared_memory.SharedMemory = None

    def sleep(self, sec: int):
        '''
        Set this sleep timer's memory to store a number of seconds for which to
        sleep. Both shared memories must have already been set before calling
        this function.
        @param sec: number of seconds to sleep
        '''
        assert self.sleeptime_memory is not None
        assert self.starttime_memory is not None

        self.sleeptime_memory.buf[:4] = struct.pack(">I", sec)
        self.starttime_memory.buf[:8] = struct.pack(">d", time.time())

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
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', type=Path, default='active_ensembles.json')
    args = parser.parse_args()

    get_logger("sleep_timer_tester", level=50)

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
    buffer_time = 2

    try:
        while True:
            logger.debug("running scheduler once")

            # start scheduler by forking new thread running scheduler.py
            new_pid = os.fork()
            if new_pid == 0:
                # run scheduler.py
                ens_list = Ensemble.list_from_json(args.file)
                scheduler = StateMachine(ens_list, sleep_timer.sleep)
                scheduler.wakeup_time = wakeup
                scheduler.shutdown_time = shutdown

                endtime = time.time()
                wakeup = max(math.ceil(endtime - starttime + buffer_time), wakeup)
                logger.info("WAKEUP TIME: %i seconds", wakeup)

                scheduler.run_machine()
            else:
                # wait for command sleep(x)
                while struct.unpack(">I", sleeptime_memory.buf[:4])[0] == 0:
                    time.sleep(1)

                # shut down scheduler by killing child process running it
                os.kill(new_pid, signal.SIGKILL)
                startttime = struct.unpack(">d", starttime_memory.buf[:8])[0]
                endtime = time.time()
                shutdown = max(math.ceil(endtime - starttime + buffer_time), shutdown)
                logger.info("SHUTDOWN TIME: %i seconds", shutdown)

                # sleep on daemon before rerunning scheduler in next iteration
                logger.info("sleeping for %i seconds",
                            struct.unpack(">I", sleeptime_memory.buf[:4])[0])
                time.sleep(struct.unpack(">I", sleeptime_memory.buf[:4])[0])
                starttime = time.time()
                sleeptime_memory.buf[:4] = struct.pack(">I", 0)

    except KeyboardInterrupt:
        os.kill(new_pid, signal.SIGKILL)
        sleeptime_memory.close()
        starttime_memory.close()
        if new_pid > 0: # only unlink SharedMemory once
            print("") # nicer formatting when just printing to terminal
            logger.info("received interrupt from user, exiting now...")
            sleeptime_memory.unlink()
            starttime_memory.unlink()

if __name__ == '__main__':
    main()
