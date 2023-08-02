from pathlib import Path

from TowerScheduler.config import Configuration


def test_config():
    # test that config data can be loaded from file correctly
    config_obj = Configuration(Path("tests/testConfig.ini")) # load occurs on initialization

    # sensitive to changes in testConfig.ini--future todo
    assert config_obj.wakeup_time == 5
    assert config_obj.shutdown_time == 5
    assert config_obj.execute_buffer == 10
    assert config_obj.log_level == 50
