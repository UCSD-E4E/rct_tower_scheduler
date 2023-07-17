'''
Module containing ensemble class, specifying structure and functionality of an
ensemble to be performed by our towers.
'''

from __future__ import annotations

import importlib.util
import inspect
import json

from pathlib import Path

from util import SECONDS_IN_DAY

class Ensemble:
    '''
    Class specifying an ensemble to be executed by our tower. Includes data
    needed to specify the ensemble and functions to load an Ensemble list from
    a json file
    '''

    def __init__(self, title: str, function: str, start_time: int):
        self.title = title
        self.start_time = start_time

        module_raw = function.split(':')[0]
        self.module_dir = module_raw + ".py"
        self.module_name = module_raw.split("/")[-1]
        self.function_name = function.split(':')[-1]

    @classmethod
    def list_from_json(cls, file: Path) -> (list[Ensemble]):
        '''
        Convert a json file, such as that created by convert_to_active, into a
        list of Ensemble objects.

        @param file: Path to the file containing active ensemble json
        @return List[Ensemble]: list of Ensembles defined by json
        @return int: Index of next Ensemble to execute

        @throws FileNotFoundError if file argument is not a valid file
        @throws KeyError if file argument is improperly formatted
        '''

        with open(file, "r", encoding="utf-8") as f_in:
            ens_json = json.load(f_in)

        ens_list_json = ens_json["ensemble_list"]

        ens_list = []
        for ens in ens_list_json:
            ens_list.append( Ensemble(ens["title"],
                                    ens["function"],
                                    ens["start_time"]) )

        return ens_list

    @classmethod
    def list_to_json(cls, ens_list: list[Ensemble]) -> dict[str, list[dict[str, str]]]:
        json_list = []
        for ens in ens_list:
            function = ens.module_dir[0:-3] + ":" + ens.function_name
            ens_dict = {"title": ens.title,
                        "function": function,
                        "start_time": ens.start_time}
            json_list.append(ens_dict)

        return json_list

    def perform_ensemble_function(self):
        '''
        Function to call this Ensemble's non-member or static function.
        '''

        # TODO: test to confirm this works with external packages
        spec = importlib.util.spec_from_file_location(self.module_name,
                                                    self.module_dir)
        module = importlib.util.module_from_spec(spec)

        spec.loader.exec_module(module)
        class_function = getattr(module, self.function_name)

        class_function()

    def validate(self):
        '''
        Validate this Ensemble by confirming that its start time is a valid time
        and its specified function exists and takes no arguments.

        @return True if Ensemble is valid, else False
        '''

        valid_start = self.start_time >= 0 and self.start_time < SECONDS_IN_DAY

        try:
            spec_path = self.module_dir[0:-3].replace('/', '.')
            module = importlib.util.find_spec(spec_path)
        except ModuleNotFoundError:
            return False

        if module is not None:
            spec.loader.exec_module(module)
            try:
                func = getattr(module, self.function_name)
            except AttributeError:
                return False

            args = inspect.getfullargspec(func).args
            func_takes_args = args == []
        else:
            return False

        return valid_start and not func_takes_args
