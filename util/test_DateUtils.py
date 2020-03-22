
import pytest

from util.DateUtils import remaining_days_of_month, dt


def testRemainingDaysInMonth():
    assert remaining_days_of_month(dt(2020,3,21)) == 11