#!/usr/bin/python3

from multiprocessing import shared_memory
import os
import signal
import time

from state_machine_design import StateMachine

'''
Ideally, we make a SleepTimerTester object which inherits from SleepTimer.
Then, we run the scheduler itself with any SleepTimer object, which can include a tester.
'''
class SleepTimerTester:
    '''
    SleepTimer object specifically for testing. This should inherit from SleepTimer once
    that package is completed. Scheduler can be run with any SleepTimer object, which,
    in this case, is our tester.
    '''
    def __init__(self):
        self.memory = None
        #self.time_to_sleep = 0

    def sleep(self, sec: int):
        self.memory.buf[:] = sec.to_bytes(4, "big")
        #self.time_to_sleep = sec
    
    def set_memory(self, memory: shared_memory.SharedMemory):
        self.memory = memory

def main():
    memory = shared_memory.SharedMemory(create=True, size=4)
    sleep_timer = SleepTimerTester()
    sleep_timer.set_memory(memory)

    while True:
        print("running scheduler once")
        
        # start scheduler by forking new thread running scheduler.py
        new_pid = os.fork()
        if new_pid == 0:
            # run scheduler.py
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

            # sleep on daemon before rerunning scheduler in next iteration
            print("sleeping for " + str(int.from_bytes(memory.buf[:], "big")))
            time.sleep(int.from_bytes(memory.buf[:], "big"))
            memory.buf[:] = int(0).to_bytes(4, "big")

    memory.close()

if __name__ == '__main__':
    main()
