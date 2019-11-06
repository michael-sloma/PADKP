import re
import datetime as dt


COMMAND_RE = r"You tell your raid, '\s*!{}\s*(?P<number1>![0-9])?\s*(?P<item>.*?)\s*(?P<number2>![0-9])?\s*(?P<comment>\|\|.*)?'$"
AUCTION_START_RE = COMMAND_RE.format(r'bids\s*open')
AUCTION_CLOSE_RE = COMMAND_RE.format(r'bids\s*closed')
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
        item_name = search.group('item')
        item_count = search.group('number1') or search.group('number2') or '!1'
        return {'action': 'AUCTION_START',
                'item_name': item_name.strip(),
                'item_count': int(item_count.replace('!', '')),
                'timestamp': line.timestamp()}
    return None


def auction_bid(line, active_items):
    for item in active_items:
        window_bid_format = (r'(?P<bidder>[A-Z][a-z]+) -> [A-Z][a-z]+:\s+'
                              rf'(?P<item>{item})\s*(?P<bid>[0-9]+)\s*'
                              r'(dkp)?\s*(?P<alt>alt|box)?\s*(?P<comment>\|\|.*)?$')
        direct_tell_format = (r"(?P<bidder>[A-Z][a-z]+) tells you, "
                              rf"'\s*(?P<item>{item})\s*(?P<bid>[0-9]+)\s*(dkp)?\s*"
                              r"(?P<alt>alt|box)?(?P<comment>\|\|.*)?")
        match = re.match(window_bid_format, line.contents, re.IGNORECASE) \
               or re.match(direct_tell_format, line.contents, re.IGNORECASE)
        if match is not None:
            player_name = match.group('bidder')
            item_name = match.group('item')
            value = match.group('bid')
            alt = match.group('alt')
            comment = match.group('comment')
            return {'action': 'BID',
                    'item_name': item_name.strip(),
                    'player_name': player_name,
                    'value': int(value),
                    'comment': comment[2:] if comment is not None else '',
                    'alt': alt is not None,
                    'timestamp': line.timestamp()}
    return None
    


def auction_close_match(line):
    return re.match(AUCTION_CLOSE_RE, line.contents, re.IGNORECASE)


def auction_close(line):
    search = re.search(AUCTION_CLOSE_RE, line.contents, re.IGNORECASE)
    if search:
        # TODO error handling if there is no such active auction
        item_name = search.group('item')
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
        item_name = search.group('item')
        return {'action': 'AUCTION_CANCEL',
                'item_name': item_name,
                'timestamp': line.timestamp()}
    return None

AUCTION_AWARD_RE = ("You tell your raid, "
                    r"'\s*!correction\s*!award\s*"
                    r"(?P<item>.*?)\s+"
                    r"(?P<name>[A-Z][a-z]+)\s+"
                    r"(?P<value>[0-9]+)\s+"
                    r"(?P<comment>\|\|.*)?'$")

AUCTION_AWARD_RE = r"You tell your raid, '\s*!correction\s*!award\s*(?P<item>.*)\s*!to\s*(?P<award>(?:[A-Z][a-z]+\s*[0-9]+\s*,?\s*)+)\s*(?P<comment>\|\|.*)?'$"


def auction_award_match(line):
    return re.match(AUCTION_AWARD_RE, line.contents, re.IGNORECASE)


def auction_award(line):
    search = re.search(AUCTION_AWARD_RE,
                       line.contents,
                       re.IGNORECASE)
    if search:
        item_name = search.group('item').strip()
        award = search.group('award').replace(',', ' ')
        winners = award.split()[::2]
        bids = award.split()[1::2]
        return {'action': 'AUCTION_AWARD',
                'item_name': item_name,
                'winners': winners,
                'bids': bids,
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


def handle_line(raw_line, active_items):
    """ returns a description of the action to be taken based on the line, if we
    recognize it, or None"""
    if not pre_filter(raw_line):
        return None
    line = LogLine(raw_line)
    if auction_start_match(line):
        return auction_start(line)
    match = auction_bid(line, active_items)
    if match:
        return match
    if auction_close_match(line):
        return auction_close(line)
    if auction_cancel_match(line):
        return auction_cancel(line)
    if auction_award_match(line):
        return auction_award(line)
    return None

