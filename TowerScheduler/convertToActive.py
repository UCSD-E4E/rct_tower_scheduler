#
# This is a reimplementation of the cpp "setup" function as a standalone
# script so that whoever writes/generates the ensemble list can convert it
# into a format more easily used by the scheduler

# The default read-in file is "ensembles.json and can be overwritten by
# passing in a filename as an argument

# This script always writes to "active_ensembles.json" and WILL overwrite
# if a file of that name is in the same directory

import sys
import json


def hms_to_seconds(hour, minute, sec):
    """converts hours, mins, seconds to just seconds"""
    return sec + minute * 60 + hour * 3600


def sort_func(ens):
    """metric for sorting ensembles"""
    return ens["start_time"]


def main():
    """read the ensembles file, enumerate all ensembles and iterations,
       sort them, then write them into active_ensembles.json"""
    filein = "dummy_ensembles.json"
    if len(sys.argv) > 1 :
        filein = sys.argv[1]

    with open(filein, "r", encoding="utf-8") as f_in:
        ens = json.load(f_in)

    ens_list = []
    json_file = []
    # double loop adds all ensembles and their iterations to a list
    for i in ens["ensemble_list"]:
        i_hour = i["start_time"]["hour"]
        i_minute = i["start_time"]["minute"]
        i_second = i["start_time"]["second"]
        tot_time = hms_to_seconds(i_hour, i_minute, i_second)

        for j in range(i["iterations"]):
            iter_seconds = i["interval"]
            i_obj = { "title": i["title"],
                    "function": i["function"],
                    "inputs": i["inputs"],
                    "start_time": tot_time + iter_seconds * j }
            ens_list.append(i_obj)


    # create an extra object for teardown function
    teardown_obj = {
        "title": "teardown",
        "function": "teardown",
        "inputs": [],
        "start_time": 86399
    }

    ens_list.append(teardown_obj)

    # sort all the enumerated ensembles by time
    ens_list.sort(key=sort_func)

    # data that will become our json file format
    json_file = {
        "ensemble_list": [],
        "next_ensemble": 0
    }
    for i in ens_list:
        json_file["ensemble_list"].append(i)

    # open/create file in overwrite mode
    with open("active_ensembles.json", "w", encoding="utf-8") as f_out:
        f_out.write(json.dumps(json_file, indent=4))

    f_out.close()

if __name__ == "__main__":
    main()
