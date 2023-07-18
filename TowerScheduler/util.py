#!/usr/bin/python3
'''
Module containing utility functions and constants.
'''

SECONDS_IN_DAY = 86400

def hms_to_seconds(hour: int, minute: int, sec: int) -> int:
    """
    Converts hours, mins, seconds to just seconds

    @param hour: hour of timestamp to convert to seconds
    @param minute: minute of timestamp to convert to seconds
    @param sec: second of timestamp, to add to hour and minute conversions
    @return
    """
    return sec + minute * 60 + hour * 3600
