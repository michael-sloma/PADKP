import pytest
import parse

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
AUCTION_OPEN_WITH_COMMENT = "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open Singing Steel Breastplate|| TELLS TO ME'"
AUCTION_OPEN_WITH_COMMENT_2 = "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open Singing Steel Breastplate || TELLS TO ME'"
AUCTION_OPEN_WITH_WHITESPACE_1 = "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open Singing Steel Breastplate || TELLS TO ME'"
AUCTION_OPEN_WITH_WHITESPACE_2 = "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open   Singing Steel Breastplate || TELLS TO ME'"
AUCTION_OPEN_WITH_WHITESPACE_3 = "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open Singing Steel Breastplate  || TELLS TO ME'"
AUCTION_OPEN_WITH_WHITESPACE_4 = "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids         open Singing Steel Breastplate  || TELLS TO ME'"
AUCTION_OPEN_DOUBLE = "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open Singing Steel Breastplate !2 || THERE ARE TWO'"
AUCTION_OPEN_DOUBLE_2= "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open !2 Singing Steel Breastplate  || THERE ARE TWO'"

BID_TELL_WINDOW = "[Wed Jun 12 23:07:49 2019] Playertwo -> Quaff: Singing Steel Breastplate 55"
BID_TELL_WINDOW_2 = "[Wed Jun 12 23:07:49 2019] Playertwo -> Quaff: Singing Steel Breastplate 55 "
BID_TELL_WINDOW_3 = "[Wed Jun 12 23:07:49 2019] Playertwo -> Quaff: Singing Steel Breastplate  55"
BID_TELL_WINDOW_4 = "[Wed Jun 12 23:07:49 2019] Playertwo -> Quaff:  Singing Steel Breastplate 55"
BID_TELL_WINDOW_COMMENT = "[Wed Jun 12 23:07:49 2019] Playertwo -> Quaff:  Singing Steel Breastplate 55 || I can't even use it lol"
BID_TELL_WINDOW_ALT_1 = "[Wed Jun 12 23:07:49 2019] Playertwo -> Quaff: Singing Steel Breastplate 55 alt"
BID_TELL_WINDOW_ALT_2 = "[Wed Jun 12 23:07:49 2019] Playertwo -> Quaff: Singing Steel Breastplate 55 ALT"
BID_TELL_WINDOW_ALT_3 = "[Wed Jun 12 23:07:49 2019] Playertwo -> Quaff: Singing Steel Breastplate 55 box"

BIDS_CLOSED = "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids closed Singing Steel Breastplate'"
BIDS_CLOSED_WITH_ONE_WHITESPACE_AFTER = "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids closed Singing Steel Breastplate '"
BIDS_CLOSED_WITH_TWO_WHITESPACE_AFTER = "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids closed Singing Steel Breastplate  '"
BIDS_CLOSED_WITH_WHITESPACE_BEFORE = "[Wed Jun 12 23:24:33 2019] You tell your raid, ' !Bids closed Singing Steel Breastplate'"
BIDS_CLOSED_WITH_COMMENT = "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids closed Singing Steel Breastplate || tells to Quaff'"

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
     [('regular message', BID_TELL_WINDOW),
      ('whitespace', BID_TELL_WINDOW_2),
      ('whitespace', BID_TELL_WINDOW_3),
      ('whitespace', BID_TELL_WINDOW_4),
      ('comment', BID_TELL_WINDOW_COMMENT),
      ]
)
def test_auction_bid_tell_window(comment, bid_message):
    input_line = parse.LogLine(bid_message)
    result = parse.auction_bid(input_line)
    assert result['item_name'] == 'Singing Steel Breastplate'
    assert result['player_name'] == 'Playertwo'
    assert result['value'] == 55
    assert result['action'] == 'BID'


@pytest.mark.parametrize('comment, bids_closed_message',
    [('regular message', BIDS_CLOSED),
     ('comment message', BIDS_CLOSED_WITH_COMMENT),
     ('whitespace after', BIDS_CLOSED_WITH_ONE_WHITESPACE_AFTER),
     ('whitespace after', BIDS_CLOSED_WITH_TWO_WHITESPACE_AFTER),
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
