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

## Input File
Functions to perform should be stored in the following json format:
```
{
  "next_ensemble": "example1",
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
      "next_time": {
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
      "next_time": {
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
- next_ensemble: string matching some ensemble's title (defaults to first in sequence if missing or invalid)
- function: Callable
- inputs: void*, to be converted? Or a list of args & we trust user to match correct number and types of args to each function?
- starting time:
  - hour: hour at which to start [0, 23]
  - minute: minute at which to start [0, 59]
  - second: second at which to start [0, 59]
  0 is assumed for each of these if not specified
- next execution time:
  - hour: hour at which to next execute [0, 23] (default 23)
  - minute: minute at which to next execute [0, 59] (default 59)
  - second: second at which to next execute [0, 59] (default 59)
- iterations: int
- interval (seconds between iterations): double
An example file, dummy_ensembles.json, is provided for testing purposes.

## Outline
1.	Fetch current ensemble (what should be performed) from disk
2.	Read file until reaching current ensemble, read functions to perform
3.	Let tower perform functions in current ensemble
4.	Perform calculations to find sleep duration given current time, time at which to perform next ensemble, and wakeup and shutdown times
5.	Save next ensemble to disk to indicate what comes next
6.	Send sleep command to sleep timer

## Edge Cases
Edge cases to address after completing basic scheduler:
- Function takes more time than its own interval allows --> skip next iteration of that function
- Function takes more time than we have until a separate function must be called --> call second func as soon as first returns, don’t skip
- Not enough time to go into sleep + wake up --> just sit idle/spin for that time
- Sleep timer isn’t working --> tower needs to keep functioning on its own, not just turn off permanently
  - conserve power if possible (later goal)
- Can’t connect to network --> save something locally, upload offline later?
