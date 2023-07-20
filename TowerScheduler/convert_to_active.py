'''
Module to convert a json file of the specified schema (title, function, and
timing) into a new json containing a current index and an ordered list of
ensembles to execute. Each listed ensemble in the new active_ensembles.json will
contain the title, module and function, inputs, and start time (in seconds,
relative to 0=midnight), and they will be ordered according to increasing start
time.
'''

import argparse
import datetime as dt
import json
from pathlib import Path

from schema import Regex, Schema

LAST_SEC_OF_DAY = 86399

ensemble_schema = Schema(
    {
        "ensemble_list": [
            {
                "title": str,
                "function": Regex(r'^((\w)+\/)*\w+:\w+$'),
                "start_time": Regex(r'^[0-9][0-9]:[0-9][0-9]:[0-9][0-9]$'),
                "iterations": int,
                "interval": int
            }
        ]
    }
)

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
        start_time = dt.time.fromisoformat(func["start_time"])

        for j in range(func["iterations"]):
            interval_sec = dt.timedelta(seconds=func["interval"])

            this_iteration_time = (dt.datetime.combine(dt.date.today(), start_time) + \
                interval_sec * j).time()

            curr_obj = { "title": func["title"],
                    "function": func["function"],
                    "start_time":  str(this_iteration_time) }
            ens_list.append(curr_obj)

    '''
    # create an extra object for teardown function
    teardown_obj = {
        "title": "teardown",
        "function": "teardown",
        "start_time": LAST_SEC_OF_DAY
    }

    ens_list.append(teardown_obj)
    '''

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
