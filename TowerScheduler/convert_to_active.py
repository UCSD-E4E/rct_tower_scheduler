import argparse
import json
import os
from pathlib import Path
from schema import Regex, Schema

LAST_SEC_OF_DAY = 86399

ensemble_schema = Schema(
    {
        "ensemble_list": [
            {
                "title": str,
                "function": Regex(r'^((\w)+\/)*\w+:\w+$'),
                "inputs": list,
                "start_time": {
                    "hour": int,
                    "minute": int,
                    "second": int
                },
                "iterations": int,
                "interval": int
            }
        ]
    }
)

def hms_to_seconds(hour: int, minute: int, sec: int) -> int:
    """
    Converts hours, mins, seconds to just seconds

    @param hour: hour of timestamp to convert to seconds
    @param minute: minute of timestamp to convert to seconds
    @param sec: second of timestamp, to add to hour and minute conversions
    @return
    """
    return sec + minute * 60 + hour * 3600

def main(filein: Path):
    """
    Read the ensembles file, enumerate all ensembles and iterations,
    sort them, then write them into active_ensembles.json

    @param filein: Path to the schedule to be converted to active_ensembles
    """

    with open(filein, "r", encoding="utf-8") as f_in:
        ens = json.load(f_in)
    ensemble_schema.validate(ens)

    ens_list = []
    json_file = []
    # double loop adds all ensembles and their iterations to a list
    for func in ens["ensemble_list"]:
        curr_hour = func["start_time"]["hour"]
        curr_min = func["start_time"]["minute"]
        curr_sec = func["start_time"]["second"]
        timestamp = hms_to_seconds(curr_hour, curr_min, curr_sec)

        for j in range(func["iterations"]):
            interval_sec = func["interval"]
            curr_obj = { "title": func["title"],
                    "function": func["function"],
                    "inputs": func["inputs"],
                    "start_time": timestamp + interval_sec * j }
            ens_list.append(curr_obj)

    # create an extra object for teardown function
    teardown_obj = {
        "title": "teardown",
        "function": "teardown",
        "inputs": [],
        "start_time": LAST_SEC_OF_DAY
    }

    ens_list.append(teardown_obj)

    # sort all the enumerated ensembles by time
    ens_list.sort(key=lambda ens:ens['start_time'])

    # data that will become our json file format
    json_file = {
        "ensemble_list": ens_list,
        "next_ensemble": 0
    }

    # open/create file in overwrite mode
    with open("active_ensembles.json", "w", encoding="utf-8") as f_out:
        f_out.write(json.dumps(json_file, indent=4))

if __name__ == "__main__":
    # check for input file argument
    parser = argparse.ArgumentParser()
    parser.add_argument('file', type=Path)
    args = parser.parse_args()

    main(args.file)
