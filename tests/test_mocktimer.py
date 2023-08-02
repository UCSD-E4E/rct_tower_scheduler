import random
import time
from multiprocessing import shared_memory

from TowerScheduler.sleep_timer_tester import SleepTimerTester, main


def test_sleep():
    sleep_timer = SleepTimerTester()

    sleeptime_memory = shared_memory.SharedMemory(create=True, size=4)
    sleep_timer.set_sleeptime_memory(sleeptime_memory)

    starttime_memory = shared_memory.SharedMemory(create=True, size=8)
    sleep_timer.set_starttime_memory(starttime_memory)

    starttime = time.time()
    time.sleep(2) # make sure time progresses at least slightly

    to_sleep = int(random.uniform(1, 2048))

    # confirm that sleeping correctly sets our SharedMemory
    sleep_timer.sleep(to_sleep)

    assert int.from_bytes(sleeptime_memory.buf[:], "big") == to_sleep
    assert int.from_bytes(starttime_memory.buf[:], "big") > starttime
