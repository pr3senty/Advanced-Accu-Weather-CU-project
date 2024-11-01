from enum import Enum


class TimeRange(Enum):
    HOURS12 = 1
    DAYS5 = 2

    def __str__(self):
        if self.value == TimeRange.HOURS12.value:
            return "12 часов"

        if self.value == TimeRange.DAYS5.value:
            return "5 дней"

    @staticmethod
    def get(value):
        if value == "12 часов":
            return TimeRange.HOURS12

        if value == "5 дней":
            return TimeRange.DAYS5

    @staticmethod
    def values():
        return [
            str(TimeRange.HOURS12),
            str(TimeRange.DAYS5),
        ]