import re
import datetime as dt


COMMAND_RE = "You tell your raid, '\s*!{}\s*(.*?)\s*(\|\|.*)?'$"
AUCTION_START_RE = COMMAND_RE.format('bids open')
AUCTION_CLOSE_RE = COMMAND_RE.format('bids closed')
AUCTION_CANCEL_RE = COMMAND_RE.format('cancel')


def auction_start_match(line):
    return re.match(AUCTION_START_RE, line.contents, re.IGNORECASE)


def auction_start(line):
    """
    An auction is starting by sending the following message in RAID SAY:
    !Bids open ITEMLINK
    Case doesn't matter
    """
    search = re.search(AUCTION_START_RE,
                       line.contents,
                       re.IGNORECASE)
    if search:
        item_name = search.group(1)
        return {'action': 'AUCTION_START',
                'item_name': item_name.strip(),
                'timestamp': line.timestamp()}
    return None


BID_TELL_WINDOW_RE = '([A-Z][a-z]+) -> [A-Z][a-z]+:\s+(.+)\s+([0-9]+)\s*(\|\|.*)?$'
BID_TELL_RE = "([A-Z][a-z]+) tells you, '\s*(.+) ([0-9]+)"
def auction_bid_match(line):
    return re.match(BID_TELL_WINDOW_RE, line.contents) \
           or re.match(BID_TELL_RE, line.contents)


def auction_bid(line):
    search_tell_window = re.search(BID_TELL_WINDOW_RE, line.contents)
    search_tell = re.search(BID_TELL_RE, line.contents)
    if search_tell_window:
        player_name, item_name, value = search_tell_window.groups()[:3]
        return {'action': 'BID',
                'item_name': item_name.strip(),
                'player_name': player_name,
                'value': int(value),
                'timestamp': line.timestamp()}
    elif search_tell:
        player_name, item_name, value = search_tell.groups()
        return {'action': 'BID',
                'item_name': item_name.strip(),
                'player_name': player_name,
                'value': int(value),
                'timestamp': line.timestamp()}
    return None


def auction_close_match(line):
    return re.match(AUCTION_CLOSE_RE, line.contents, re.IGNORECASE)


def auction_close(line):
    search = re.search(AUCTION_CLOSE_RE, line.contents, re.IGNORECASE)
    if search:
        # TODO error handling if there is no such active auction
        item_name = search.group(1)
        print('group 1', search.group(1))
        print('group 2', search.group(2))
        return {'action': 'AUCTION_CLOSE',
                'item_name': item_name.strip(),
                'timestamp': line.timestamp()}
    return None


def auction_cancel_match(line):
    return re.match(AUCTION_CANCEL_RE,
                    line.contents,
                    re.IGNORECASE)


def auction_cancel(line):
    search = re.search(AUCTION_CANCEL_RE,
                       line.contents,
                       re.IGNORECASE)
    if search:
        item_name = search.group(1)
        return {'action': 'AUCTION_CANCEL',
                'item_name': item_name,
                'timestamp': line.timestamp()}
    return None



class LogLine:
    def __init__(self, text):
        self.time_str = text[:26]
        self.contents = text[27:].strip()

    def timestamp(self):
        return dt.datetime.strptime(self.time_str, '[%a %b %d %H:%M:%S %Y]')


def pre_filter(raw_line):
    """pre-filter lines. if it's not a tell or raid say, we know we don't care"""
    return re.match("^.{27}[A-Z][a-z]* ((tells the|tell your) raid|tells you|->)", raw_line)


def handle_line(raw_line):
    """ returns a description of the action to be taken based on the line, if we
    recognize it, or None"""
    if not pre_filter(raw_line):
        return None
    line = LogLine(raw_line)
    if auction_start_match(line):
        return auction_start(line)
    elif auction_bid_match(line):
        return auction_bid(line)
    elif auction_close_match(line):
        return auction_close(line)
    elif auction_cancel_match(line):
        return auction_cancel(line)
    else:
        return None

