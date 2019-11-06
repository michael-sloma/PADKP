import auction
import parse


def test_whole_auction_case_1():
    auc = auction.AuctionState()
    lines = [
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open Cloak of Flames'",
        "[Wed Jun 12 23:07:49 2019] Foobar -> Quaff: Cloak of Flames  10",
        "[Wed Jun 12 23:07:49 2019] Playerone -> Quaff: Cloak of Flames  10",
        "[Wed Jun 12 23:07:49 2019] Playerone -> Quaff: Cloak of Flames  11",
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids closed Cloak of Flames '",
    ]
    for line in lines:
        # we assume that every action was parsed properly. parse failures will cause a type error here
        action = parse.handle_line(line, set(['Cloak of Flames']))
        auc.update(action)
    finished_auction = auc.concluded_auctions[0]
    assert finished_auction['item'] == 'Cloak of Flames'
    assert len(finished_auction['bids']) == 2


def test_whole_auction_case_2():
    auc = auction.AuctionState()
    lines = [
        "[Wed Jun 12 23:01:33 2019] You tell your raid, '!Bids open Green Dragon Scale'",
        "[Wed Jun 12 23:02:49 2019] Foobar -> Quaff: Cloak of Flames  10",
        "[Wed Jun 12 23:03:49 2019] Foobar -> Quaff: Green Dragon Scale  10",
        "[Wed Jun 12 23:04:49 2019] Grunt -> Quaff: Green Dragon Scale  4",
        "[Wed Jun 12 23:05:49 2019] Papapa -> Quaff: Green Dragon Scale  5",
        "[Wed Jun 12 23:06:49 2019] Baz -> Quaff: Green Dragon Scale  10",
        "[Wed Jun 12 23:07:33 2019] You tell your raid, '!Bids closed Green Dragon Scale'",
    ]
    for line in lines:
        action = parse.handle_line(line, set(['Cloak of Flames', 'Green Dragon Scale']))
        auc.update(action)
    assert len(auc.concluded_auctions) == 0  # bids are tied, auction wasn't completed
    tied_auction = list(auc.active_auctions.values())[0]
    assert tied_auction['item'] == 'Green Dragon Scale'
    assert len(tied_auction['bids']) == 4


def test_whole_auction_case_3():
    auc = auction.AuctionState()
    lines = [
        "[Wed Jun 12 23:01:33 2019] You tell your raid, '!Bids open Amulet of Necropotence'",
        "[Wed Jun 12 23:07:49 2019] Foo -> Quaff: Amulet of Necropotence 90",
        "[Wed Jun 12 23:07:49 2019] Bar -> Quaff: Amulet of Necropotence 112 ALT",
        "[Wed Jun 12 23:07:49 2019] Baz -> Quaff: Amulet of Necropotence 75",
        "[Wed Jun 12 23:07:49 2019] Qux -> Quaff: Amulet of Necropotence 40",
        "[Wed Jun 12 23:07:49 2019] Quux -> Quaff: Amulet of Necropotence 2",
        "[Wed Jun 12 23:07:49 2019] Thud -> Quaff: Amulet of Necropotence 89",
        "[Wed Jun 12 23:07:49 2019] Waldo -> Quaff: Amulet of Necropotence 13",
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids closed Amulet of Necropotence'",
    ]
    for line in lines:
        action = parse.handle_line(line, set(['Amulet of Necropotence']))
        # we assume that every action was parsed properly. parse failures will cause a type error here
        update = auc.update(action)

    assert len(auc.concluded_auctions) == 1
    assert len(update.update_rows) == 1
    assert update.update_rows[0].winner == 'Foo'


def test_whole_auction_case_4():
    auc = auction.AuctionState()
    lines = [
        "[Wed Jun 23 23:24:33 2019] You tell your raid, '!Bids open !2 Cloak of Flames'",
        "[Wed Jun 23 23:07:49 2019] Foo -> Quaff: Cloak of Flames  35",
        "[Wed Jun 23 23:07:49 2019] Bar -> Quaff: Cloak of Flames  56",
        "[Wed Jun 23 23:24:33 2019] You tell your raid, '!Bids closed Cloak of Flames '",
        "[Wed Jun 23 23:24:34 2019] You tell your raid, '!correction !award Cloak of Flames !to Baz 30'",
    ]
    for line in lines:
        action = parse.handle_line(line, set(['Cloak of Flames']))
        # we assume that every action was parsed properly. parse failures will cause a type error here
        update = auc.update(action)
    assert len(auc.concluded_auctions) == 1
    assert update.update_rows[0].winner == 'Baz'
    assert update.update_rows[0].price == '30'

