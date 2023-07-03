#!/usr/bin/python3

from multiprocessing import shared_memory
import os
import signal
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

    def sleep(self, sec: int):
        '''
        Set this sleep timer's memory to store a number of seconds for which to
        sleep. Memory must have already been set before calling this function.
        @param sec: number of seconds to sleep
        '''
        self.memory.buf[:] = sec.to_bytes(4, "big")

    def set_memory(self, memory: shared_memory.SharedMemory):
        '''
        Assign shared memory to this sleep timer, so it has a section of memory
        which our parent process can access
        @param memory: SharedMemory with a size of 4 bytes (to store one int)
        '''
        self.memory = memory

def main():
    memory = shared_memory.SharedMemory(create=True, size=4)
    sleep_timer = SleepTimerTester()
    sleep_timer.set_memory(memory)
    new_pid = -1

    try:
        while True:
            print("running scheduler once")

            # start scheduler by forking new process running scheduler
            new_pid = os.fork()
            if new_pid == 0:
                # run state machine
                scheduler = StateMachine()
                scheduler.set_sleep_timer(sleep_timer)
                scheduler.run_machine()
                #os.execl("./state_machine_design.py", "./state_machine_design.py")
            else:
                # wait for command sleep(x)
                while int.from_bytes(memory.buf[:], "big") == 0:
                    time.sleep(1)

                # shut down scheduler by killing child process running it
                os.kill(new_pid, signal.SIGKILL)

                # sleep on parent proc before rerunning scheduler in next iteration
                print("sleeping for " + str(int.from_bytes(memory.buf[:], "big")))
                time.sleep(int.from_bytes(memory.buf[:], "big"))
                memory.buf[:] = int(0).to_bytes(4, "big")

    except KeyboardInterrupt:
        print("received interrupt from user, exiting now...")
        if new_pid > 0:
            os.kill(new_pid, signal.SIGKILL)
        memory.close()
        memory.unlink()

if __name__ == '__main__':
    main()
