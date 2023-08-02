import datetime as dt
import pytest
from schema import Regex, Schema, SchemaError

from conftest import DEFAULT_ENS_ITERATIONS, NUM_TRIALS
from TowerScheduler.convert_to_active import convert_one_ensemble, \
                ensemble_schema, function_regex, time_regex


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

@pytest.mark.parametrize('scheduled_ensemble', [DEFAULT_ENS_ITERATIONS], indirect=True)
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
