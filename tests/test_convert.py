import datetime as dt
import random
import pytest
import string
from schema import Regex, Schema, SchemaError
from typing import Dict, List

from TowerScheduler.convert_to_active import convert_one_ensemble, \
                ensemble_schema, function_regex, time_regex


NUM_TRIALS = 128
MAX_RANDOM_WORD_LENGTH = 16
MAX_RANDOM_DIR_LENGTH = 8
MAX_RANDOM_ENS_INTERVAL = 3600
DEFAULT_ENS_ITERATIONS = 3

def get_random_function() -> str:
    '''
    Construct one random function string. Period-delimited directories may be up
    to MAX_RANDOM_DIR_LENGTH deep, and both directory and function names may be
    up to MAX_RANDOM_WORD_LENGTH characters long. Path and function name are
    separated by a colon.

    returns:
        str: Randomly-created full function string
    '''

    dir = ''
    # up to MAX_RANDOM_DIR_LENGTH period-delimited directory names
    for i in range(int(random.uniform(1, MAX_RANDOM_DIR_LENGTH))):
        # up to MAX_RANDOM_WORD_LENGTH characters in directory name
        for j in range(int(random.uniform(1, MAX_RANDOM_WORD_LENGTH))):
            dir += random.choice(string.ascii_letters + '_')
        dir += '.'
    dir = dir[:-1] # remove trailing '.' from final module name

    func = ':'
    # up to MAX_RANDOM_WORD_LENGTH characters in function name
    for i in range(int(random.uniform(1, MAX_RANDOM_WORD_LENGTH))):
        func += random.choice(string.ascii_letters + '_')

    return dir + func

@pytest.fixture
def function_list(request) -> (List[str], str):
    """
    Creates a list of functions of the form path_to_module.module:function

    Inputs may be valid (including randomly-generated good input) or invalid.

    @param request (pytest.FixtureRequest): Fixture Request
    returns:
        func_list: List of function names which are either all valid (if request
            parameter is 'good') or all invalid (if request parameter is not
            'good')
        request.param: Fixture Request, 'good' if all function strings in
            func_list are valid, 'bad' if all function strings are invalid
    """

    if request.param == 'good': # valid function strings
        func_list = ["tests.tester_functions:hello_world",
                    "autostart.rctrun:main"]
        for _ in range(NUM_TRIALS): # add randomized but valid strings
            func_list.append(get_random_function())

    else: # several types of invalid function strings
        func_list = ["tests.:hello_world",
                    ".test:hello_world",
                    "test:",
                    "test.hello_world",
                    "hello_world",
                    ":hello_world"]

    return func_list, request.param

@pytest.fixture
def scheduled_ensemble() -> Dict[str, str]:
    '''
    Create a dictionary containing data for a fake scheduled ensemble. Includes
    a randomized title, valid function string, and interval. Start time defaults
    to the current time and iterations to DEFAULT_ENS_ITERATIONS.

    returns:
        Dict[str, str]: dictionary of constructed ensemble data
    '''

    title = ''
    for i in range(int(random.uniform(1, MAX_RANDOM_WORD_LENGTH))):
        title += random.choice(string.ascii_letters + '_')

    function = get_random_function()

    start_time = dt.datetime.now().time().replace(microsecond=0)

    interval = int(random.uniform(1, MAX_RANDOM_ENS_INTERVAL))

    sched = {
        "title": title,
        "function": function,
        "start_time": start_time.isoformat(),
        "iterations": DEFAULT_ENS_ITERATIONS,
        "interval": interval
    }

    return sched


@pytest.mark.parametrize('function_list', ['good', 'bad'], indirect=True)
def test_function_regex(function_list):
    good = (function_list[1] == 'good')
    for func in function_list[0]:
        try:
            function_regex.validate(func)
            assert good # input should be good if validation was successful
        except SchemaError:
            assert not good # input should be bad if there's a SchemaError

def test_time_regex():
    # first test that whatever current time is can be validated
    now = dt.datetime.now().replace(microsecond=0)
    time_str = now.time().isoformat()
    time_regex.validate(time_str)

    # edit current time in valid way--hh:mm:ss to h:mm:ss format
    time_regex.validate(time_str[1:])

    # edit current time in invalid ways
    invalid_list = [
        '1' + time_str, # too many hour digits
        time_str.replace(':', '.'), # incorrect delimiter
        time_str[:-3], # missing seconds
        time_str[:3] + time_str[4:] # too few minute digits
    ]
    for bad_time in invalid_list:
        try:
            time_regex.validate(bad_time)
            assert False # we should never reach this
        except SchemaError:
            assert True # we should reach this

def test_ens_conversion(scheduled_ensemble):
    for _ in range(NUM_TRIALS):
        start_time = dt.time.fromisoformat(scheduled_ensemble["start_time"])
        start_time = dt.datetime.combine(dt.date.today(), start_time)
        interval = dt.timedelta(seconds=scheduled_ensemble["interval"])

        result = convert_one_ensemble(scheduled_ensemble)

        for i in range(DEFAULT_ENS_ITERATIONS):
            expected_time = (start_time + i*interval).time().isoformat()
            assert result[i]["title"] == scheduled_ensemble["title"]
            assert result[i]["function"] == scheduled_ensemble["function"]
            assert result[i]["start_time"] == expected_time
