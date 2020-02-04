import datetime as dt
import timestamps


def test_time_from_gui_display():
    test_s = "Jan 01 2020, 10:00 AM"
    time = timestamps.time_from_gui_display(test_s)
    assert time.month == 1
    assert time.day == 1
    assert time.hour == 10


def test_time_from_gui_display_pm():
    test_s = "Jan 01 2020, 10:00 PM"
    time = timestamps.time_from_gui_display(test_s)
    assert time.month == 1
    assert time.day == 1
    assert time.hour == 22


def test_time_to_gui_display():
    test_time = dt.datetime(month=1, day=1, year=2020, hour=10, minute=0)
    time_s = timestamps.time_to_gui_display(test_time)
    assert time_s == "Jan 01 2020, 10:00 AM"


def test_time_to_gui_display_pm():
    test_time = dt.datetime(month=1, day=1, year=2020, hour=20, minute=0)
    time_s = timestamps.time_to_gui_display(test_time)
    assert time_s == "Jan 01 2020, 10:00 PM"


def test_time_to_gui_display_pm():
    test_s = "Jan 01 2020, 10:00 PM"
    time = timestamps.time_from_gui_display(test_s)
    assert time.month == 1
    assert time.day == 1
    assert time.hour == 22


def test_timestamp_reversible():
    """ we can convert a string to datetime and back and it will be unchanged """
    test_s = "Jan 01 2020, 10:00 AM"
    assert timestamps.time_to_gui_display((timestamps.time_from_gui_display(test_s))) == test_s
