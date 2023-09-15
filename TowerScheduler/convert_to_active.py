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
from typing import Dict, List


LAST_SEC_OF_DAY = 86399

# one or more period-delimited words describing the path to a
# module, followed by a colon and another word for the function
function_regex = Regex(r'^(\w+.)*\w+:\w+$')

# pairs of digits separated by colons
time_regex = Regex(r'^\d{1,2}:\d{2}:\d{2}$')

ensemble_schema = Schema(
    {
        "ensemble_list": [
            {
                "title": str,
                "function": function_regex,
                "start_time": time_regex,
                "iterations": int,
                "interval": int
            }
        ]
    }
)

def convert_one_ensemble(ens: Dict[str, str]) -> List[Dict[str, str]]:
    '''
    Convert one ensemble from scheduled format to a List of all its iterations
    in the format needed by the scheduler.

    @param ens: Dict[str, str]: dictionary containing ensemble title, function,
        start time, and number of intervals
    returns:
        List[Dict[str, str]]: list of all iterations of the provided ensemble,
            containing each iteration's title, function, and start time
    '''
    this_ens_list = []
    start_time = dt.time.fromisoformat(ens["start_time"])
    start_time = dt.datetime.combine(dt.date.today(), start_time)
    interval_sec = dt.timedelta(seconds=ens["interval"])

    for j in range(ens["iterations"]):
        this_iteration_time = (start_time + interval_sec * j).time()

        curr_obj = { "title": ens["title"],
                "function": ens["function"],
                "start_time":  str(this_iteration_time) }
        this_ens_list.append(curr_obj)

    return this_ens_list


def main():
    """
    Read the ensembles file, enumerate all ensembles and iterations,
    sort them, then write them into active_ensembles.json.
    """

    # check for input file argument
    parser = argparse.ArgumentParser()
    parser.add_argument('filein', type=Path)
    parser.add_argument('--fileout', type=Path, required=False,
                        default='active_ensembles.json')
    args = parser.parse_args()

    with open(args.filein, "r", encoding="utf-8") as f_in:
        ens = json.load(f_in)
    ensemble_schema.validate(ens)

    ens_list = []
    json_file = []
    for func in ens["ensemble_list"]:
        ens_list += convert_one_ensemble(func)

    ens_list.sort(key=lambda ens:ens['start_time'])

    # data that will become our json file format
    json_file = {
        "ensemble_list": ens_list
    }

    with open(args.fileout, "w", encoding="utf-8") as f_out:
        f_out.write(json.dumps(json_file, indent=4))

if __name__ == "__main__":
    main()
