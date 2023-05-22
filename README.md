# rct_tower_scheduler
Sleep period scheduler for Radio Telemetry's tower deployments

## Setup
### Linux:
Install jsoncpp using:
`sudo apt-get install libjsoncpp-dev`

Compile using:
`g++ -ljsoncpp -o testscheduler exscheduler.cpp`
### Windows:
Install jsoncpp amalgamate using:
```
git clone git@github.com:open-source-parsers/jsoncpp.git
cd jsoncpp
python amalgamate.py
```
Move jsoncpp.cpp and the json directory from `dist` subdirectory into `rct_tower_scheduler` directory
Compile jsoncpp library (only needs to be done once) using:
```
g++ -c jsoncpp.cpp -o jsoncpp.o
ar cr lib_jsoncpp.a jsoncpp.o
```
Compile scheduler using:
```
g++ -c exscheduler.cpp -o testscheduler.o
g++ testscheduler.o lib_jsoncpp.a -o testscheduler -static-libstdc++
```
### Mac:

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
  "ensemble_list": [
    {
      "title": "zeta1",
      "function": "ensemble_tests.tester_functions.hello_world",
      "inputs": [],
      "start_time": {
          "hour": 8,
          "minute": 0,
          "second": 15
      },
      "iterations": 5,
      "interval": 60
    },
    {
      "title": "zeta2",
      "function": "ensemble_tests.tester_functions.print_this",
      "inputs": ["Hello World!"],
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
      "function": "ensemble_tests.tester_functions.add_this",
      "inputs": [1, 2],
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
      "function": "ensemble_tests.tester_functions.subtract_this",
      "inputs": [1, 2],
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
  0 is assumed for each of these if not specified
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
