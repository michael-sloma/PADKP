import re
import os
import datetime as dt


COMMAND_RE = r"You tell your raid, '\s*!{}\s*(?P<number1>![0-9])?\s*(?P<item>.*?)\s*(?P<number2>![0-9])?\s*(?P<comment>\|\|.*)?'$"
AUCTION_START_RE = COMMAND_RE.format(r'bids\s*open')
AUCTION_CLOSE_RE = COMMAND_RE.format(r'bids\s*closed')
AUCTION_CANCEL_RE = COMMAND_RE.format('cancel')

SUICIDE_START_RE = COMMAND_RE.format(r'suicide\s*open')
SUICIDE_CLOSE_RE = COMMAND_RE.format(r'suicide\s*closed')


def suicide_start(line):
    """
    Start a suicide auction
    An auction is starting by sending the following message in RAID SAY:
    !Bids open ITEMLINK
    Case doesn't matter
    """
    search = re.search(SUICIDE_START_RE,
                       line.contents,
                       re.IGNORECASE)
    if search:
        item_name = search.group('item')
        item_count = search.group('number1') or search.group('number2') or '!1'
        return {'action': 'SUICIDE_START',
                'item_name': item_name.strip(),
                'item_count': int(item_count.replace('!', '')),
                'timestamp': line.timestamp()}
    return None


def suicide_close(line):
    search = re.search(SUICIDE_CLOSE_RE, line.contents, re.IGNORECASE)
    if search:
        # TODO error handling if there is no such active auction
        item_name = search.group('item')
        return {'action': 'SUICIDE_CLOSE',
                'item_name': item_name.strip(),
                'timestamp': line.timestamp()}
    return None


def suicide_bid(line, active_items):
    for item in active_items:
        bid_format = (r"(?P<bidder>[A-Z][a-z]+) tells the raid, "
                      rf"'\s*!\s*want\s*(?P<item>{item})\s*")
        match = re.match(bid_format, line.contents, re.IGNORECASE)
        if match is not None:
            player_name = match.group('bidder')
            item_name = match.group('item')
            return {'action': 'SUICIDE_BID',
                    'item_name': item_name.strip(),
                    'player_name': player_name,
                    'timestamp': line.timestamp()}
    return None


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
        ## DEPRECATED
        window_bid_format = (r'(?P<bidder>[A-Z][a-z]+) -> [A-Z][a-z]+:\s+'
                              rf'(?P<item>{item})\s*(?P<bid>[0-9]+)\s*'
                              r'(dkp)?\s*(?P<status_flag>alt|box|inactive|recruit|fnf|ff|f&f|fandf)?\s*(?P<comment>\|\|.*)?$')
        # THIS IS THE WAY
        direct_tell_format = (r"(?P<bidder>[A-Z][a-z]+) tells you, "
                              rf"'\s*(?P<item>{item})\s*(?P<bid>[0-9]+)\s*(dkp)?\s*"
                              r"(?P<status_flag>alt|box|inactive|recruit|fnf|ff|f&f|fandf)?(?P<comment>\|\|.*)?")
        match = re.match(window_bid_format, line.contents, re.IGNORECASE) \
               or re.match(direct_tell_format, line.contents, re.IGNORECASE)
        if match is not None:
            player_name = match.group('bidder')
            item_name = match.group('item')
            value = match.group('bid')
            status_flag = match.group('status_flag')
            is_alt = status_flag is not None and status_flag.lower() in ['alt', 'box']
            comment = match.group('comment')
            return {'action': 'BID',
                    'item_name': item_name.strip(),
                    'player_name': player_name,
                    'value': int(value),
                    'comment': comment[2:] if comment is not None else '',
                    'status_flag': status_flag,
                    #'alt': status_flag is not None,
                    'is_second_class_citizen': status_flag is not None,
                    'is_alt': is_alt,
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
                    r"'\s*!(correction|tiebreak)\s*!award\s*"
                    r"(?P<item>.*?)\s+"
                    r"(?P<name>[A-Z][a-z]+)\s+"
                    r"(?P<value>[0-9]+)\s+"
                    r"(?P<comment>\|\|.*)?'$")

AUCTION_AWARD_RE = r"You tell your raid, '\s*!(correction|tiebreak)\s*!award\s*(?P<item>.*)\s*!to\s*(?P<award>(?:[A-Z][a-z]+\s*[0-9]+\s*,?\s*)+)\s*(?P<comment>\|\|.*)?'$"


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
                'data': line.contents,
                'timestamp': line.timestamp()}
    return None

PREREGISTER_RE = (r"You told (?P<recipient>[a-z]+), "
                  r"'\s*!preregister\s*(?P<item>.*?)\s*(?P<bid>[0-9]+)\s*(dkp)?\s*"
                  r"(?P<status_flag>alt|box)?(?P<comment>\|\|.*)?")


def preregister_match(line):
    return re.match(PREREGISTER_RE, line.contents, re.IGNORECASE)


def preregister(line):
    search = re.search(PREREGISTER_RE, line.contents, re.IGNORECASE)
    if search:
        recipient = search.group('recipient')
        item_name = search.group('item')
        value = search.group('bid')
        status_flag = search.group('status_flag')
        is_alt = status_flag is not None and status_flag.lower() in ['alt', 'box']
        comment = search.group('comment')
        return {'action': 'PREREGISTER',
                'item_name': item_name.strip(),
                'recipient': recipient,
                'value': int(value),
                'comment': comment[2:] if comment is not None else '',
                'status_flag': status_flag,
                'is_alt': status_flag is not None,
                'timestamp': line.timestamp()}
    return None


WAITLIST_RE = ("(You tell your|[A-Z][a-z]+ tells the) raid, "
               r"'\s*!waitlist\s*"
               r"(?P<command>[a-z]+)\s+"
               r"(?P<name>[A-Z][a-z]+)")

JOINED_RAID_RE = r"(?P<name>[A-Z][a-z]+) joined the raid."

def waitlist_match(line):
    return re.match(WAITLIST_RE, line.contents, re.IGNORECASE)


def waitlist(line):
    search = re.search(WAITLIST_RE, line.contents, re.IGNORECASE)
    if search:
        name = search.group('name').lower().capitalize()
        command = 'WAITLIST_' + search.group('command').upper()
        return {'action': command,
                'name': name,
                'timestamp': line.timestamp()}
    return None


def joined_raid(line):
    search = re.search(JOINED_RAID_RE, line.contents, re.IGNORECASE)
    if search:
        name = search.group('name').lower().capitalize()
        return {'action': 'JOINED RAID',
                'name': name,
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
    return re.match("^.{27}[A-Z][a-z]* (tells the|tell your|joined the) raid", raw_line) or tell_filter(raw_line)


def received_tell_filter(raw_line):
    return re.match("^.{27}[A-Z][a-z]* (tells you|->)", raw_line)


def sent_tell_filter(raw_line):
    return re.match("^.{27}You told", raw_line)


def tell_filter(raw_line):
    return received_tell_filter(raw_line) or sent_tell_filter(raw_line)


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
    if preregister_match(line):
        return preregister(line)
    if waitlist_match(line):
        return waitlist(line)
    if joined_raid(line):
        return joined_raid(line)
    if suicide_bid(line, active_items):
        return suicide_bid(line, active_items)
    if suicide_start(line):
        return suicide_start(line)
    if suicide_close(line):
        return suicide_close(line)
    if len(active_items) > 0 and received_tell_filter(raw_line):
        return {'action': 'FAILED_BID', 'data': line.contents, 'timestamp': line.timestamp()}
    return None


def get_name_from_log_file_path(filepath):
    short_filename = os.path.split(filepath)[-1]
    name_search = re.search(r'eqlog_(?P<my_name>.*)_.*.txt', short_filename)
    if name_search:
        return name_search.group('my_name')
    else:
        return 'MYSELF'

