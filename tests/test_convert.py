import datetime
import random
import pytest
import string
from schema import Regex, Schema, SchemaError

from TowerScheduler.convert_to_active import ensemble_schema, \
                function_regex, time_regex


NUM_TRIALS = 128
MAX_RANDOM_WORD_LENGTH = 16
MAX_RANDOM_DIR_LENGTH = 8

@pytest.fixture
def function_list(request):
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

            func_list.append(dir + func)

    else: # several types of invalid function strings
        func_list = ["tests.:hello_world",
                    ".test:hello_world",
                    "test:",
                    "test.hello_world",
                    "hello_world",
                    ":hello_world"]

    return func_list, request.param

'''
@pytest.fixture
def schedule(request):
    # make some schedule such as found in ensembles.json
    request.param
    return True
'''


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
    now = datetime.datetime.now().replace(microsecond=0)
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

#def test_one_ens_conversion():
    # test random input ens is converted to correct format
    # (separate functionality into helper func, outside of convert_to_active's main)
