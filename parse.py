import re
import datetime as dt

def auction_start_match(line):
    return re.match("You tell your raid, '!bids open (.*)'$", line.contents, re.IGNORECASE)


def auction_start(line):
    """
    An auction is starting by sending the following message in RAID SAY:
    !Bids open ITEMLINK
    Case doesn't matter
    """
    search = re.search("You tell your raid, '!bids open (.*)'$",
                       line.contents,
                       re.IGNORECASE)
    if search:
        item_name = search.group(1)
        return {'action': 'AUCTION_START',
                'item_name': item_name,
                'timestamp': line.timestamp()}
    return None


def auction_bid_match(line):
    return re.match('([A-Z][a-z]+) -> [A-Z][a-z]+: (.+) ([0-9]+)$', line.contents)


def auction_bid(line):
    search_tell_window = re.search('([A-Z][a-z]+) -> [A-Z][a-z]+: (.+) ([0-9]+)$',
                                    line.contents)
    search_tell = re.search("([A-Z][a-z]+) tells you, '(.+) ([0-9]+)", line.contents)
    if search_tell_window:
        player_name, item_name, value = search_tell_window.groups()
        return {'action': 'BID',
                'item_name': item_name,
                'player_name': player_name,
                'value': int(value),
                'timestamp': line.timestamp()}
    elif search_tell:
        player_name, item_name, value = search_tell.groups()
        return {'action': 'BID',
                'item_name': item_name,
                'player_name': player_name,
                'value': int(value),
                'timestamp': line.timestamp()}
    return None


def auction_close_match(line):
    return re.match("!bids closed (.+)'$", line.contents, re.IGNORECASE)


def auction_close(line):
    search = re.search("!bids closed (.+)'$", line.contents, re.IGNORECASE)
    if search:
        # TODO error handling if there is no such active auction
        item_name = search.group(1)
        return {'action': 'AUCTION_CLOSE',
                'item_name': item_name,
                'timestamp': line.timestamp()}
    return None


class LogLine:
    def __init__(self, text):
        self.time_str = text[:26]
        self.contents = text[27:]

    def timestamp(self):
        return self.time_str
        #return dt.datetime.strptime(self.time_str, '[%a %b %d %H:%M:%S %Y]')


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
    elif auction_close(line):
        return auction_close(line)
    else:
        return None

