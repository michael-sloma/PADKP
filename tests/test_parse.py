import pytest
import parse
import re


def test_log_line_timestamp():
    test_line = "[Wed Jun 12 22:49:34 2019] Foobar tells the raid,  'Ha ha ha!'"
    timestamp = parse.LogLine(test_line).timestamp()
    assert timestamp.day == 12
    assert timestamp.month == 6
    assert timestamp.year == 2019
    assert timestamp.hour == 22
    assert timestamp.minute == 49
    assert timestamp.second == 34


auction_tell_windows = \
    """[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open Singing Steel Breastplate'
[Wed Jun 12 23:07:49 2019] Playerone -> Quaff: Singing Steel Breastplate 10
[Wed Jun 12 23:07:49 2019] Playertwo -> Quaff: Singing Steel Breastplate 55
[Wed Jun 12 23:07:49 2019] Playerthree -> Quaff: Singing Steel Breastplate 20
[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids closed Singing Steel Breastplate'
[Wed Jun 12 22:49:34 2019] Clikclik tells the raid,  'Grats Intermezzo Singing Steel Breastplate 55 DKP!'"""

AUCTION_OPEN = "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open Singing Steel Breastplate'"
AUCTION_OPEN_BAD_CHARACTERS = "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open Singing Steel Breastplate\\'"
AUCTION_OPEN_WITH_COMMENT = "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open Singing Steel Breastplate|| TELLS TO ME'"
AUCTION_OPEN_WITH_COMMENT_2 = "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open Singing Steel Breastplate || TELLS TO ME'"
AUCTION_OPEN_WITH_WHITESPACE_1 = "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open Singing Steel Breastplate || TELLS TO ME'"
AUCTION_OPEN_WITH_WHITESPACE_2 = "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open   Singing Steel Breastplate || TELLS TO ME'"
AUCTION_OPEN_WITH_WHITESPACE_3 = "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open Singing Steel Breastplate  || TELLS TO ME'"
AUCTION_OPEN_WITH_WHITESPACE_4 = "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids         open Singing Steel Breastplate  || TELLS TO ME'"
AUCTION_OPEN_DOUBLE = "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open Singing Steel Breastplate !2 || THERE ARE TWO'"
AUCTION_OPEN_DOUBLE_2 = "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open !2 Singing Steel Breastplate  || THERE ARE TWO'"

BID_TELL = "[Wed Jun 12 23:07:49 2019] Playertwo tells you, 'Singing Steel Breastplate 55'"
BID_TELL_2 = "[Wed Jun 12 23:07:49 2019] Playertwo tells you, 'Singing Steel Breastplate 55 '"
BID_TELL_3 = "[Wed Jun 12 23:07:49 2019] Playertwo tells you, 'Singing Steel Breastplate  55'"
BID_TELL_4 = "[Wed Jun 12 23:07:49 2019] Playertwo tells you, ' Singing Steel Breastplate 55'"
BID_TELL_NO_SPACE = "[Wed Jun 12 23:07:49 2019] Playertwo tells you, 'Singing Steel Breastplate55'"
BID_TELL_COMMENT = "[Wed Jun 12 23:07:49 2019] Playertwo tells you, 'Singing Steel Breastplate 55 || I can\'t even use it lol'"
BID_TELL_DKP = "[Wed Jun 12 23:07:49 2019] Playertwo tells you, 'Singing Steel Breastplate 55dkp '"
BID_TELL_ALT_1 = "[Wed Jun 12 23:07:49 2019] Playertwo tells you, 'Singing Steel Breastplate 55  alt'"
BID_TELL_ALT_2 = "[Wed Jun 12 23:07:49 2019] Playertwo tells you, 'Singing Steel Breastplate 55 ALT'"
BID_TELL_ALT_3 = "[Wed Jun 12 23:07:49 2019] Playertwo tells you, 'Singing Steel Breastplate 55 box'"

BIDS_CLOSED = "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids closed Singing Steel Breastplate'"
BIDS_CLOSED_WITH_ONE_WHITESPACE_AFTER = "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids closed Singing Steel Breastplate '"
BIDS_CLOSED_WITH_TWO_WHITESPACE_AFTER = "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids closed Singing Steel Breastplate  '"
BIDS_CLOSED_WITH_WHITESPACE_BEFORE = "[Wed Jun 12 23:24:33 2019] You tell your raid, ' !Bids closed Singing Steel Breastplate'"
BIDS_CLOSED_WITH_COMMENT = "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids closed Singing Steel Breastplate || tells to Quaff'"


FAILED_BID = "[Wed Jun 12 23:07:49 2019] Playertwo tells you, 'I like apples'"
FAILED_BID_TYPO = "[Wed Jun 12 23:07:49 2019] Playertwo tells you, 'Singing Steel Breastplate 55 a;t'"

DEFAULT_ITEMS = set(['Singing Steel Breastplate'])


@pytest.mark.parametrize('comment, bids_open_message',
                         [('regular message', AUCTION_OPEN),
                          ('comment message', AUCTION_OPEN_WITH_COMMENT),
                             ('comment message', AUCTION_OPEN_WITH_COMMENT_2),
                             ('whitespace', AUCTION_OPEN_WITH_WHITESPACE_1),
                             ('whitespace', AUCTION_OPEN_WITH_WHITESPACE_2),
                             ('whitespace', AUCTION_OPEN_WITH_WHITESPACE_3),
                             ('whitespace', AUCTION_OPEN_WITH_WHITESPACE_4),
                          ]
                         )
def test_auction_open(comment, bids_open_message):
    input_line = parse.LogLine(bids_open_message)
    result = parse.auction_start(input_line)
    assert result['item_name'] == 'Singing Steel Breastplate'


@pytest.mark.parametrize('comment, bid_message',
                         [('regular message', BID_TELL),
                          ('whitespace', BID_TELL_2),
                             ('whitespace', BID_TELL_3),
                             ('whitespace', BID_TELL_4),
                             ('comment', BID_TELL_COMMENT),
                             ('has "dkp" in it', BID_TELL_DKP),
                             ('alt', BID_TELL_ALT_1),
                             ('alt', BID_TELL_ALT_2),
                             ('box', BID_TELL_ALT_3),
                             ('no space before bid', BID_TELL_NO_SPACE),
                          ]
                         )
def test_auction_bid_tell(comment, bid_message):
    input_line = parse.LogLine(bid_message)
    result = parse.auction_bid(input_line, DEFAULT_ITEMS)[1]
    assert result is not None
    assert result['item_name'] == 'Singing Steel Breastplate'
    assert result['player_name'] == 'Playertwo'
    assert result['value'] == 55
    assert result['action'] == 'BID'


def test_bad_open_bid():
    result = parse.handle_line(AUCTION_OPEN_BAD_CHARACTERS, DEFAULT_ITEMS)
    assert result is None


def test_failed_bid():
    result = parse.handle_line(FAILED_BID, DEFAULT_ITEMS)
    assert result is not None
    assert result['action'] == 'FAILED_BID'


def test_failed_close_bid():
    result = parse.handle_line(FAILED_BID_TYPO, DEFAULT_ITEMS)
    assert result is not None
    assert result['action'] == 'FAILED_BID'


def test_failed_bid_outside_auctions():
    result = parse.handle_line(FAILED_BID, set())
    assert result is None


@ pytest.mark.parametrize('comment, bid_message, expect_alt',
                          [('regular message', BID_TELL, False),
                           ('whitespace', BID_TELL_2, False),
                           ('alt', BID_TELL_ALT_1, True),
                           ('alt', BID_TELL_ALT_2, True),
                           ('box', BID_TELL_ALT_3, True),
                           ])
def test_auction_bid_alt(comment, bid_message, expect_alt):
    """ check that we correctly interpret an alt message"""
    input_line = parse.LogLine(bid_message)
    result = parse.auction_bid(input_line, DEFAULT_ITEMS)[1]
    assert result is not None
    assert result['is_alt'] == expect_alt


@ pytest.mark.parametrize('comment, bids_closed_message',
                          [('regular message', BIDS_CLOSED),
                           ('comment message', BIDS_CLOSED_WITH_COMMENT),
                           ('whitespace after',
                              BIDS_CLOSED_WITH_ONE_WHITESPACE_AFTER),
                           ('whitespace after',
                              BIDS_CLOSED_WITH_TWO_WHITESPACE_AFTER),
                           ('whitespace before', BIDS_CLOSED_WITH_WHITESPACE_BEFORE)
                           ]
                          )
def test_auction_award(comment, bids_closed_message):
    input_line = parse.LogLine(bids_closed_message)
    result = parse.auction_close(input_line)
    assert result['item_name'] == 'Singing Steel Breastplate'
    assert result['action'] == 'AUCTION_CLOSE'


def test_auction_start_count():
    input_line = parse.LogLine(AUCTION_OPEN)
    result = parse.auction_start(input_line)
    assert result['item_count'] == 1

    input_line = parse.LogLine(AUCTION_OPEN_DOUBLE)
    result = parse.auction_start(input_line)
    assert result['item_count'] == 2

    input_line = parse.LogLine(AUCTION_OPEN_DOUBLE_2)
    result = parse.auction_start(input_line)
    assert result['item_count'] == 2


def test_auction_award():
    line = parse.LogLine(
        "[Wed Jun 12 22:49:34 2019] You tell your raid, '!correction !award Cloak of Flames !to Lyfeless 100'")
    result = parse.auction_award(line)
    assert result['winners'] == ['Lyfeless']
    assert result['bids'] == ['100']


def test_auction_award_2():
    line = parse.LogLine(
        "[Wed Jun 12 22:49:34 2019] You tell your raid, '!correction !award Cloak of Flames !to Lyfeless's alt 100, Quaff 50'")
    result = parse.auction_award(line)
    assert result['winners'] == ["Lyfeless's alt", 'Quaff']
    assert result['bids'] == ['100', '50']


def test_auction_award_3():
    line = parse.LogLine(
        "[Wed Jun 23 23:24:34 2019] You tell your raid, '!correction !award Cloak of Flames !to Baz 30'")
    result = parse.auction_award(line)
    assert result['winners'] == ['Baz']
    assert result['bids'] == ['30']


PREGISTER = "[Wed Jun 12 23:07:49 2019] You told Lyfeless, '!preregister Singing Steel Breastplate 55 '"
PREREGISTER_ALT = "[Wed Jun 12 23:07:49 2019] You told Lyfeless, '!preregister Singing Steel Breastplate 55 box'"


def test_preregister():
    line = parse.LogLine(PREGISTER)
    assert parse.preregister_match(line)
    result = parse.preregister(line)
    reset = result[0]
    bid = result[1]

    assert reset['action'] == 'PREREGISTER-RESET'
    assert bid['action'] == 'PREREGISTER'
    assert bid['item_name'] == 'Singing Steel Breastplate'
    assert bid['value'] == 55
    assert not bid['is_alt']


def test_preregister_alt():
    line = parse.LogLine(PREREGISTER_ALT)
    assert parse.preregister_match(line)
    result = parse.preregister(line)
    reset = result[0]
    bid = result[1]

    assert reset['action'] == 'PREREGISTER-RESET'
    assert bid['action'] == 'PREREGISTER'
    assert bid['item_name'] == 'Singing Steel Breastplate'
    assert bid['value'] == 55
    assert bid['is_alt']
    assert bid['status_flag'] == 'ALT'


WAITLIST_ADD = "[Wed Jun 12 23:07:49 2019] You tell your raid, '!waitlist add Foobar'"


def test_waitlist():
    line = parse.LogLine(WAITLIST_ADD)
    assert parse.waitlist_match(line)
    result = parse.waitlist(line)
    print(result)
    assert result['action'] == 'WAITLIST_ADD'
