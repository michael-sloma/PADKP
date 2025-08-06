"""
we have to serialize and deserialize dates as strings in all kinds of
strange and wacky ways

trying to keep them all in one place here

times are assumed to always be in the user's system's local time
"""
import datetime as dt

GUI_DISPLAY_S = '%b %d %Y, %I:%M %p'


def time_from_raid_dump(string):
    try:
        timestamp_string = string.split('-', 1)[1]
        time = dt.datetime.strptime(timestamp_string, '%Y%m%d-%H%M%S.txt')
        return time.astimezone()
    except:
        return dt.datetime.now().astimezone()


def time_to_gui_display(time):
    """ stringify a time to show to the user """
    return time.strftime(GUI_DISPLAY_S)


def time_from_gui_display(string):
    """ turn a displayed time back into a datetime
    it's kind of a code smell that we have to do this, should probably organize
    the data better instead?"""
    time = dt.datetime.strptime(string, GUI_DISPLAY_S)
    return time.astimezone()


def pick_nearest_time(time):
    """ Generate a time stamp for the nearest 30 minute increment """
    if time.minute >= 45:
        time = time.replace(minute=0, second=0, microsecond=0)
        time = time + dt.timedelta(hours=1)
    elif time.minute >= 15:
        time = time.replace(minute=30, second=0, microsecond=0)
    else:
        time = time.replace(minute=0, second=0, microsecond=0)
    return time


def build_time_choices(time):
    """Generate an array of 30 minute seperated times for a 3 hour window starting two hours before provided time"""
    if time.minute >= 30:
        time = time.replace(minute=30, second=0, microsecond=0)
    else:
        time = time.replace(minute=0, second=0, microsecond=0)

    time = time - dt.timedelta(hours=2)
    return [time_to_gui_display(time+dt.timedelta(minutes=30*i)) for i in range(10)]


def time_to_django_repr(time):
    """ stringify a datetime so that it's ready to be sent over the wire"""
    return time.strftime('%Y-%m-%dT%H:%M:%S%z')
