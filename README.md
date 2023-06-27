# rct_tower_scheduler
Sleep period scheduler for Radio Telemetry's tower deployments

## Problem
Given:
-	File ensembles.json containing functions to perform at scheduled times, specifications below, read:
  -	Set S of functions to perform now
  -	Time tn+1 at which we need to perform next set of communications from ensembles.json

Constants:
-	Time tshutdown needed to go into sleep
-	Time twake needed to wake from sleep
These will need to be determined later, can use nonsense constants while building

Need to find (and communicate to sleep timer):
-	Time tsleep between going to sleep and being woken up

Perform S, then get current time tn.
Find tsleep as tn+1 - tn – tshutdown – twake, and communicate this to sleep timer.
Assume some sleep(float time) function which tells the sleep timer to put given tower to sleep for time s.
Remember to save variable indicating next set of communications to disk, since local memory will be wiped once tower goes to sleep.

## Input

### Initial File Format
Functions to perform should be stored in the following json format:
```
{
  "ensemble_list": [
    {
            "title": "zeta2",
            "function": "ensemble_tests.tester_functions:print_this",
            "inputs": [
                "Hello World!"
            ],
            "start_time": {
                "hour": 8,
                "minute": 0,
                "second": 30
            },
            "iterations": 5,
            "interval": 60
        },
        {
            "title": "dummy1",
            "function": "ensemble_tests.tester_functions:add_this",
            "inputs": [
                1,
                2
            ],
            "start_time": {
                "hour": 12,
                "minute": 0,
                "second": 0
            },
            "iterations": 5,
            "interval": 60
        },
        {
            "title": "alpha1",
            "function": "ensemble_tests.tester_functions:subtract_this",
            "inputs": [
                1,
                2
            ],
            "start_time": {
                "hour": 12,
                "minute": 0,
                "second": 0
            },
            "iterations": 5,
            "interval": 60
        }
    ...etc...
  ]
}
```
With each item being of the correct type:
- function: Callable
- inputs: void*, to be converted? Or a list of args & we trust user to match correct number and types of args to each function?
- starting time:
  - hour: hour at which to start [0, 23]
  - minute: minute at which to start [0, 59]
  - second: second at which to start [0, 59]
- iterations: int
- interval (seconds between iterations): double

### Useable File Format
The initial file of ensembles is meant to be easy to write but is annoying
to program around. We provide the `convertToActive.py` to convert the
initial format into the `active_ensembles.json` file that the scheduler
can use.

Use it like this:
```
python convertToActive.py input_file.json
```

The script uses input file `ensembles.json` by default and always outputs
to `active_ensembles.json`. Be careful since it will overwrite a previous
active ensembles file.

## Usage
Once you have a proper `active_ensembles.json` file in the same directory
as the scheduler, start it with:
```
python scheduler.py
```

## Testing
- `dummy_ensembles.json` is provided as an example initial file
- the `active_ensembles.json` provided is the scheduler-usable form of `dummy_ensembles.json`
- start the scheduler as above to run it


## Outline
1.	Fetch current ensemble (what should be performed) from disk
2.	Read file until reaching current ensemble, read functions to perform
3.	Let tower perform functions in current ensemble
4.	Perform calculations to find sleep duration given current time, time at which to perform next ensemble, and wakeup and shutdown times
5.	Save next ensemble to disk to indicate what comes next
6.	Send sleep command to sleep timer

![State machine diagram.](state_machine.png "This is our state machine.")

## Edge Cases
Edge cases to address after completing basic scheduler:
- [x] Sleep timer isn’t working --> tower will report error and resort to software sleep
- [x] Not enough time for full hardware sleep --> scheduler will use a short software sleep
- [x] Scheduler wakes up past an ensemble's time --> Skip that ensemble
- [ ] Can’t connect to network --> save something locally, upload offline later?
