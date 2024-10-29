from enum import Enum


class Result(Enum):
    SUCCESSFUL = 1
    INCORRECT_INPUT = 2
    EMPTY_FIELDS = 3
    ERRORS = 4


class TimeRange(Enum):
    HOURS12 = 1
    DAYS5 = 2