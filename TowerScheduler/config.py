'''
Provides global configuration structures
'''
from __future__ import annotations

from configparser import ConfigParser
from pathlib import Path
from typing import Any, Dict

class Configuration:
    """
    Configuration file interface object
    """

    singleton = None

    def __init__(self, config_path: Path) -> None:
        self.__config_path = config_path

        self.__wakeup_time: int = 5
        self.__shutdown_time: int = 5
        self.__execute_buffer: int = 10

        self.__log_level: int = 20

    @classmethod
    def get_singleton(cls, config_path: Path) -> Configuration:
        if Configuration.singleton is None:
            Configuration.singleton = Configuration(config_path)
            Configuration.singleton.load()
        return Configuration.singleton

    def __create_dict(self):
        return {
            "Sleep": {
                'wakeup_time': self.__wakeup_time,
                'shutdown_time': self.__shutdown_time,
                'execute_buffer': self.__execute_buffer
            },
            "Logging": {
                'level': self.__log_level
            }
        }

    def load(self) -> None:
        """
        Loads the configuration from the specified file
        """
        parser = ConfigParser()
        parser.read_dict(self.__create_dict())
        parser.read(self.__config_path.as_posix())

        self.__wakeup_time = parser['Sleep'].getint('defaultWakeup')
        self.__shutdown_time = parser['Sleep'].getint('defaultShutdown')
        self.__execute_buffer = parser['Sleep'].getint('executeBuffer')

        self.__log_level = parser['Logging'].getint('level')

    def write(self) -> None:
        """
        Writes the configuration to the file
        """
        parser = ConfigParser()
        parser.read_dict(self.__create_dict())
        with open(self.__config_path, 'w', encoding='ascii') as handle:
            parser.write(handle)

    @property
    def wakeup_time(self) -> int:
        """
        Time it takes to wake tower up

        Returns:
            int: Seconds taken to wake up
        """
        return self.__wakeup_time

    @wakeup_time.setter
    def wakeup_time(self, value: Any) -> None:
        if not isinstance(value, int):
            raise TypeError
        if not 0 <= value:
            raise ValueError
        self.__wakeup_time = value

    @property
    def shutdown_time(self) -> int:
        """
        Time it takes to shut tower down

        Returns:
            int: Seconds taken to shut down
        """
        return self.__shutdown_time

    @shutdown_time.setter
    def shutdown_time(self, value: Any) -> None:
        if not isinstance(value, int):
            raise TypeError
        if not 0 <= value:
            raise ValueError
        self.__shutdown_time = value

    @property
    def execute_buffer(self) -> int:
        """
        Window in which we may execute a given ensemble, given as seconds before
        the scheduled time for that ensemble

        Returns:
            int: Maximum seconds we may execute an ensemble early
        """
        return self.__execute_buffer

    @execute_buffer.setter
    def execute_buffer(self, value: Any) -> None:
        if not isinstance(value, int):
            raise TypeError
        if not 0 <= value:
            raise ValueError
        self.__execute_buffer = value

    @property
    def log_level(self) -> str:
        """
        Level at which to set loggers, indicating the minimum level to be logged

        Returns:
            int: Message level to log
        """
        return self.__log_level

    @log_level.setter
    def log_level(self, value: Any) -> None:
        if not isinstance(value, int):
            raise TypeError
        if 0 > value:
            value = 0 # set to logging.NOTSET if value is negative

        self.__log_level = value

    def __enter__(self) -> Configuration:
        self.load()
        return self

    def __exit__(self, exc, exp, exv) -> None:
        self.write()


__config_instance: Dict[Path, Configuration] = {}
def get_instance(path: Path) -> Configuration:
    """
    Retrieves the corresponding configuration instance singleton

    Args:
        path (Path): Path to config path

    Returns:
        Configuration: Configuration singleton
    """
    if path not in __config_instance:
        __config_instance[path] = Configuration(path)
    return __config_instance[path]
