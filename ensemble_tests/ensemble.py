import json
import importlib.util
import sys


# Temporary file for ensemble functions until scheduler.py is fixed

def perform_ensemble_functions(filename: str = "dummy_ensembles.json"):
    '''
    use importlib
    Function to call all dummy_ensembles.json functions for the day
    @param filename: specifies file with ensemble specifications
    '''
    
    with open(filename) as user_file:
        file_contents = json.load(user_file)

    
    for i in file_contents['ensemble_list']:

        module_name = i["module_name"]
        module_directory = i["module_directory"]
        class_name = i["class"]
        function_name = i["function"]
        function_inputs = i["inputs"]

        # Load module
        # try:
        spec = importlib.util.spec_from_file_location(module_name,module_directory)
        module = importlib.util.module_from_spec(spec)
        # except ModuleNotFoundError:
        #     raise ModuleNotFoundError("JSON module_directory: {} is not found".format(module_directory))
        spec.loader.exec_module(module)

        # If there is no class
        if not class_name:
            # Get function from module
            class_function = getattr(module, function_name)
            
            # Run function
            class_function(*function_inputs)

        else: # We're accessing a function from a class

            # Get class from module
            module_class = getattr(module, class_name)

            # Get function from class
            class_function = getattr(module_class, function_name)
            
            # Run function
            class_function(*function_inputs)

perform_ensemble_functions()