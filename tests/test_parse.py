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
BID_TELL_WINDOW = "[Wed Jun 12 23:07:49 2019] Playertwo -> Quaff: Singing Steel Breastplate 55"
BIDS_CLOSED = "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids closed Singing Steel Breastplate'"


def test_auction_open():
    input_line = parse.LogLine(AUCTION_OPEN)
    result = parse.auction_start(input_line)
    assert result['item_name'] == 'Singing Steel Breastplate'


def test_auction_bid_tell_window():
    input_line = parse.LogLine(BID_TELL_WINDOW)
    result = parse.auction_bid(input_line)
    assert result['item_name'] == 'Singing Steel Breastplate'
    assert result['player_name'] == 'Playertwo'
    assert result['value'] == 55
    assert result['action'] == 'BID'


def test_auction_award():
    input_line = parse.LogLine(BIDS_CLOSED)
    result = parse.auction_close(input_line)
    assert result['item_name'] == 'Singing Steel Breastplate'
    assert result['action'] == 'AUCTION_CLOSE'

