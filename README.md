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
      "title": "example1",
      "function": somefunc,
      "inputs": [],
      "start_time": {
          "hour": 12,
          "minute": 0,
          "second": 0
      },
      "iterations": 5,
      "interval": 60
    },
    {
      "title": "example2",
      "function": somefunc,
      "inputs": [],
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
- inputs: list of arguments which the user must confirm matches the correct number and types of args to the given function
- starting time:
  - hour: hour at which to start [0, 23]
  - minute: minute at which to start [0, 59]
  - second: second at which to start [0, 59]
- iterations: int
- interval (seconds between iterations): int

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
2.	Read current ensemble from file: functions to perform and time to perform them
3.  Confirm it's time to execute this ensemble
4.	Let tower perform functions in current ensemble
5.	Perform calculations to find sleep duration given current time, time at which to perform next ensemble, and wakeup and shutdown times
6.	Save next ensemble to disk to indicate what comes next
7.	Send sleep command to sleep timer

## State Machine Diagram
![State machine diagram.](state_machine.png "This is our state machine.")

## To-Do Items
- [ ] Execution of ensemble functions
- [ ] Sleep timer tester (make a subclass of SleepTimer once interface is complete)
- [ ] Determine time needed for shutdown and wakeup
- [ ] Unit testing of component functions
- [ ] System testing using fabricated schedules
- [ ] Detect that sleep timer isn’t working (dependent on sleep timer interface)
- [ ] Can’t connect to network --> save something locally, upload offline later (dependent on sleep timer interface)
- [ ] Validate time synchronization between towers and GCS
