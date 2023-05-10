import datetime
import json
import time
import importlib.util


TIME_SHUTDOWN = 5 # find real shutdon and wakeup times later
TIME_WAKEUP = 5

def teardown():
    '''
    Find how long until the first ensemble of the next day
    Uses slightly different logic than the normal next time
    calculation since we're going to the next day
    '''

    seconds_in_day = 86400

    filename = "active_ensembles.json"
    with open(filename, "r", encoding="utf-8") as f_in:
        ens = json.load(f_in)

    f_in.close()
    first_ensemble_start = ens["ensemble_list"][0]["start_time"]


    ens["next_ensemble"] = 0 # back to first ensemble
    with open(filename, "w", encoding="utf-8") as f_out:
        json.dump(ens, f_out, indent=4)

    f_out.close()


    now = time.localtime()
    curr_time_seconds = hmsToSeconds(now.tm_hour, now.tm_min, now.tm_sec)

    print("time now: " + str(curr_time_seconds))
    print("target time: " + str(first_ensemble_start))

    time_left_today = seconds_in_day - curr_time_seconds
    time_to_sleep = time_left_today + first_ensemble_start
    print("calling sleep timer for " + str(time_to_sleep) + " seconds")
    # call sleep timer here


def hmsToSeconds(hour: int, min: int, sec: int):
    '''
    Convert hours, minutes, and seconds to just seconds

    @param hour: number of hours to convert to sec
    @param min: number of minutes to convert to sec
    @param sec: number of seconds

    return: sum of seconds in hour, min, and sec
    '''

    return sec + min * 60 + hour * 3600


def setup(filename: str = "dummy_ensembles.json"):
    '''
    Function to set up active_ensembles.json for the day by ordering all
    iterations of all ensembles into execuntion order by time.

    @param filename: specifies file with ensemble specifications
    '''

    f = open(filename)
    ensembles = json.load(f)
    ens = ensembles["ensemble_list"] # shortcut for orig file
    f.close()

    # Get every ensemble and create a new dict for each iteration
    all_ensembles = []
    for i in range(len(ens)):
        i_hour   = ens[i]["start_time"]["hour"]
        i_minute = ens[i]["start_time"]["minute"]
        i_second = ens[i]["start_time"]["second"]
        tot_time = hmsToSeconds(i_hour, i_minute, i_second)
        for j in range(ens[i]["iterations"] + 1):
            iter_seconds = ens[i]["interval"]
            func_event = {}
            func_event["title"] = ens[i]["title"] + "-" + str(j)
            func_event["function"] = ens[i]["function"]
            func_event["time"] = tot_time + iter_seconds * j
            all_ensembles.append(func_event)

    # TODO: figure out when and how much we want to tear down
	# teardown sets setup as next func then sleeps for 1-2 mins
    teardown = {}
    teardown["title"] = "teardown"
    teardown["function"] = "teardown"
    teardown["time"] = 86399 # one min before midnight
    all_ensembles.append(teardown)

	# sort all of the enumerated ensembles by time
    for i in range(len(all_ensembles)):
        for j in range(i + 1, len(all_ensembles)):
            if (all_ensembles[j]["time"] < all_ensembles[i]["time"]):
                tmp = all_ensembles[i]
                all_ensembles[i] = all_ensembles[j]
                all_ensembles[j] = tmp

    full_json = {"next_ensemble": 0, "ensemble_list": all_ensembles}
    ensemble_ofile = open("active_ensembles.json", 'w')
    json.dump(full_json, ensemble_ofile)
    ensemble_ofile.close()


def someFunc():
    ''''
    simple printing function for use in testing
    '''
    print("someFunc called!")

def perform_ensemble_functions(filename: str = "dummy_ensembles.json"):
    '''
    Function to call all dummy_ensembles.json functions for the day
    @param filename: specifies file with ensemble specifications
    '''
    with open(filename, encoding="utf-8") as user_file:
        file_contents = json.load(user_file)
    for i in file_contents['ensemble_list']:
        module_name = i["module_name"]
        module_directory = i["module_directory"]
        class_name = i["class"]
        function_name = i["function"]
        function_inputs = i["inputs"]
        # Load module
        # try:
        spec = importlib.util.spec_from_file_location(module_name,module_directory)
        module = importlib.util.module_from_spec(spec)
        # except ModuleNotFoundError:
        # raise ModuleNotFoundError("JSON module_directory: \
        # {} is not found".format(module_directory))
        spec.loader.exec_module(module)
        # If there is no class
        if not class_name:
            # Get function from module
            class_function = getattr(module, function_name)
            # Run function
            class_function(*function_inputs)
        else: # We're accessing a function from a class
            # Get class from module
            module_class = getattr(module, class_name)
            # Get function from class
            class_function = getattr(module_class, function_name)
            # Run function
            class_function(*function_inputs)

def check_ensemble_should_sleep(nearest_ens_time: int):
    '''
    Given the time of execution of an ensemble, determine whether we have enough
    time for the tower to go into sleep before it will need to wake up again.

    @param nearest_ens_time: time (in seconds) of next ensemble's execution
    @return should_sleep: True if tower has enough time to go into sleep and
                wake up again before next ensemble, else false
            available_sleep_time: seconds for which tower may sleep
    '''
    # Get current time
    now = time.localtime()
    curr_time_seconds = hmsToSeconds(now.tm_hour, now.tm_min, now.tm_sec)
    print("now in seconds: " + str(curr_time_seconds))
    print("next ensemble time in seconds: " + str(nearest_ens_time))

    # Next ensemble time past current time
    if (nearest_ens_time >= curr_time_seconds):
        # Do not need to sleep
        return (False, 0)
    else:
        available_sleep_time = nearest_ens_time - curr_time_seconds - \
            TIME_WAKEUP - TIME_SHUTDOWN

        '''
        TODO: check if sleep timer is responsive
        if not, do time.sleep instead of calling sleep timer
        '''

        # not enough time to go into sleep and wake up again before next ensemble
        if available_sleep_time <= 0:
            sleep_time = nearest_ens_time - curr_time_seconds
            # time.sleep(sleep_time) # Wait using Python sleep function
            print(f"Temporary print replace sleep: time.sleep({str(sleep_time)})")
            # Do not need to sleep any longer
            return (False, 0)
        else:
            # Need to send sleep command to sleep timer
            return (True, available_sleep_time)


def main():
    filename = "active_ensembles.json"

    try:
        f = open(filename)
        ensembles = json.load(f)
        f.close()
        next_ensemble = ensembles["next_ensemble"]
        ens = ensembles["ensemble_list"]
    except:
        next_ensemble = 0
        setup()

    f = open(filename)
    ensembles = json.load(f)
    f.close()

    ens = ensembles["ensemble_list"] # shortcut for active

    '''
    Checks if next_ensemble is already past current time
     If so, runs the ensemble, iterates next_ensemble and checks again
     If not,
    If there's time to sleep, print very last statement about sleepTimer.sleepIf not enough time to sleep, time.sleep(sec)
    '''
    while (True):
        next_ensemble = ensembles["next_ensemble"]
        if (next_ensemble >= len(ens)):
            break

        nearest_ens_time = ens[next_ensemble]["time"]
        should_sleep, sleep_time = check_ensemble_should_sleep(nearest_ens_time)

        if (should_sleep):
            # someRefToSleepTimer.sleep(sleep_time)
            print(f"Temporary print replacing sleep: sleepTimer.sleep({str(sleep_time)})")
        else:
            print("performing ensemble functions: ")
            perform_ensemble_functions()
            next_ensemble += 1

            ensembles["next_ensemble"] += 1

            #ensemble_ofile = open(filename, "w")
            #json.dump(full_json, ensemble_ofile)
            #ensemble_ofile.close()


if __name__ == '__main__':
    main()
