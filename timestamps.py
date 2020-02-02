"""
we have to serialize and deserialize dates as strings in all kinds of
strange and wacky ways

trying to keep them all in one place here

times are assumed to always be in the user's system's local time
"""
import datetime as dt

GUI_DISPLAY_S = '%b %d %Y, %I:%M %p'


def time_from_raid_dump(string):
    time = dt.datetime.strptime(string, 'RaidRoster_mangler-%Y%m%d-%H%M%S.txt')
    return time.astimezone()


def time_to_gui_display(time):
    """ stringify a time to show to the user """
    return time.strftime(GUI_DISPLAY_S)


def time_from_gui_display(string):
    """ turn a displayed time back into a datetime
    it's kind of a code smell that we have to do this, should probably organize
    the data better instead?"""
    time = dt.datetime.strptime(string, GUI_DISPLAY_S)
    return time.astimezone()


def time_to_django_repr(time):
    """ stringify a datetime so that it's ready to be sent over the wire"""
    return time.strftime('%Y-%m-%dT%H:%M:%S%z')

