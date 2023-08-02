import datetime as dt
import pytest

from conftest import get_random_function
from TowerScheduler.convert_to_active import convert_one_ensemble
from TowerScheduler.ensemble import Ensemble


def test_to_dict():
    function_name = get_random_function()
    time = dt.datetime.now()
    ens = Ensemble('test ensemble', function_name, time)
    expected = {
        'title': 'test ensemble',
        'function': function_name,
        'start_time': str(time)
    }

    dict = ens.to_dict()

    assert dict == expected

@pytest.mark.parametrize('scheduled_ensemble', [1], indirect=True)
def test_from_dict(scheduled_ensemble):
    dict = convert_one_ensemble(scheduled_ensemble)[0]
    expected = Ensemble(dict["title"],
                        dict["function"],
                        dt.time.fromisoformat(dict["start_time"]))

    ens = Ensemble.from_dict(dict)

    assert ens.matches(expected)

def test_perform_ensemble_function():
    # ensemble with some function we know we can perform
    time = dt.datetime.now()
    ens = Ensemble("Get Five", "tester_functions:return_5", time)

    result = ens.perform_ensemble_function()

    assert result == 5

def test_validate():
    time = dt.datetime.now().time()
    good_func_ens = [
        Ensemble("Hello World", "tester_functions:hello_world", time),
        Ensemble("Add", "tester_functions:add_this", time),
        Ensemble("Subtract", "tester_functions:subtract_this", time)
    ]
    bad_func_ens = [
        Ensemble("Bad Function", "tester_functions:fake_func", time),
        Ensemble("Bad Module", "fake_module:hello_world", time),
        Ensemble("Function Takes Args", "tester_functions:takes_args", time)
    ]

    for ens in good_func_ens:
        assert ens.validate()

    for ens in bad_func_ens:
        assert not ens.validate()
