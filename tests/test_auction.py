import auction
import parse


def test_whole_auction_case_1():
    auc = auction.AuctionState("Tester")
    lines = [
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open Cloak of Flames'",
        "[Wed Jun 12 23:07:49 2019] Foobar -> Quaff: Cloak of Flames  10",
        "[Wed Jun 12 23:07:49 2019] Playerone -> Quaff: Cloak of Flames  10",
        "[Wed Jun 12 23:07:49 2019] Playerone -> Quaff: Cloak of Flames  11",
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids closed Cloak of Flames '",
    ]
    for line in lines:
        # we assume that every action was parsed properly. parse failures will cause a type error here
        actions = parse.handle_line(line, set(['Cloak of Flames']))
        if not isinstance(actions, list):
            actions = [actions]
        for action in actions:
            auc.update(action)
    finished_auction = auc.concluded_auctions[0]
    assert finished_auction['item'] == 'Cloak of Flames'
    assert len(finished_auction['bids']) == 4


def test_whole_auction_case_2():
    auc = auction.AuctionState("Tester")
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
        actions = parse.handle_line(
            line, set(['Cloak of Flames', 'Green Dragon Scale']))
        if not isinstance(actions, list):
            actions = [actions]
        for action in actions:
            auc.update(action)
    # bids are tied, auction wasn't completed
    assert len(auc.concluded_auctions) == 0
    tied_auction = list(auc.active_auctions.values())[0]
    assert tied_auction['item'] == 'Green Dragon Scale'
    assert len(tied_auction['bids']) == 8


def test_whole_auction_case_3():
    auc = auction.AuctionState("Tester")
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
        actions = parse.handle_line(line, set(['Amulet of Necropotence']))
        # we assume that every action was parsed properly. parse failures will cause a type error here
        if not isinstance(actions, list):
            actions = [actions]
        for action in actions:
            update = auc.update(action)

    assert len(auc.concluded_auctions) == 1
    assert len(update.update_rows) == 1
    assert update.update_rows[0].winner == 'Foo'


def test_whole_auction_case_4():
    auc = auction.AuctionState("Tester")
    lines = [
        "[Wed Jun 23 23:24:33 2019] You tell your raid, '!Bids open !2 Cloak of Flames'",
        "[Wed Jun 23 23:07:49 2019] Foo -> Quaff: Cloak of Flames  35",
        "[Wed Jun 23 23:07:49 2019] Bar -> Quaff: Cloak of Flames  56",
        "[Wed Jun 23 23:24:33 2019] You tell your raid, '!Bids closed Cloak of Flames '",
        "[Wed Jun 23 23:24:34 2019] You tell your raid, '!correction !award Cloak of Flames !to Baz 30'",
    ]
    for line in lines:
        actions = parse.handle_line(line, set(['Cloak of Flames']))
        # we assume that every action was parsed properly. parse failures will cause a type error here
        if not isinstance(actions, list):
            actions = [actions]
        for action in actions:
            update = auc.update(action)
    assert len(auc.concluded_auctions) == 1
    assert update.update_rows[0].winner == 'Baz'
    assert update.update_rows[0].price == '30'


def test_whole_auction_case_5():
    """ test that a tied bid above the alt threshold is correctly awarded to the main"""
    auc = auction.AuctionState("Tester")
    lines = [
        "[Wed Jun 12 23:01:33 2019] You tell your raid, '!Bids open Green Dragon Scale'",
        "[Wed Jun 12 23:03:49 2019] Foobar -> Quaff: Green Dragon Scale  10",
        "[Wed Jun 12 23:04:49 2019] Grunt -> Quaff: Green Dragon Scale  10 alt",
        "[Wed Jun 12 23:05:49 2019] Papapa -> Quaff: Green Dragon Scale  5",
        "[Wed Jun 12 23:07:33 2019] You tell your raid, '!Bids closed Green Dragon Scale'",
    ]
    for line in lines:
        actions = parse.handle_line(
            line, set(['Cloak of Flames', 'Green Dragon Scale']))
        if not isinstance(actions, list):
            actions = [actions]
        for action in actions:
            auc.update(action)
    # bids are tied, auction wasn't completed
    assert len(auc.concluded_auctions) == 1


def test_failed_bid_case():
    auc = auction.AuctionState("Tester")
    lines = [
        "[Wed Jun 23 23:24:33 2019] You tell your raid, '!Bids open !2 Cloak of Flames'",
        "[Wed Jun 23 23:07:49 2019] Foo -> Quaff: Cloak of Flames  35",
        "[Wed Jun 23 23:07:49 2019] Bar -> Quaff: Cloak of Flames  56",
        "[Wed Jun 23 23:07:49 2019] Bar -> Quaff: I don't understand the rules, help?",
    ]
    for line in lines:
        actions = parse.handle_line(line, set(['Cloak of Flames']))
        # we assume that every action was parsed properly. parse failures will cause a type error here
        if not isinstance(actions, list):
            actions = [actions]
        for action in actions:
            update = auc.update(action)
    assert update.status_messages[0] == "Failed to parse bid: Bar -> Quaff: I don't understand the rules, help?"


def test_preregister_bid():
    auc = auction.AuctionState("Tester")
    lines = [
        "[Wed Jun 12 23:24:32 2019] You told Grunt, '!preregister Cloak of Flames 20'",
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open Cloak of Flames'",
        "[Wed Jun 12 23:07:49 2019] Foobar -> Quaff: Cloak of Flames  10",
        "[Wed Jun 12 23:07:49 2019] Playerone -> Quaff: Cloak of Flames  10",
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids closed Cloak of Flames '",
    ]
    for line in lines:
        # we assume that every action was parsed properly. parse failures will cause a type error here
        actions = parse.handle_line(line, set(['Cloak of Flames']))
        if not isinstance(actions, list):
            actions = [actions]
        for action in actions:
            update = auc.update(action)
    finished_auction = auc.concluded_auctions[0]
    assert finished_auction['item'] == 'Cloak of Flames'
    assert len(finished_auction['bids']) == 6
    assert update.update_rows[0].winner == 'Tester'
    assert update.update_rows[0].price == '20'


def test_preregister_bid_alt():
    auc = auction.AuctionState("Tester")
    lines = [
        "[Wed Jun 12 23:24:32 2019] You told Grunt, '!preregister Cloak of Flames 20 alt'",
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open Cloak of Flames'",
        "[Wed Jun 12 23:07:49 2019] Foobar -> Quaff: Cloak of Flames  5",
        "[Wed Jun 12 23:07:49 2019] Playerone -> Quaff: Cloak of Flames  5",
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids closed Cloak of Flames '",
    ]
    for line in lines:
        # we assume that every action was parsed properly. parse failures will cause a type error here
        actions = parse.handle_line(line, set(['Cloak of Flames']))
        if not isinstance(actions, list):
            actions = [actions]
        for action in actions:
            update = auc.update(action)
    finished_auction = auc.concluded_auctions[0]
    assert finished_auction['item'] == 'Cloak of Flames'
    assert len(finished_auction['bids']) == 6
    assert update.update_rows[0].winner == "Tester's alt"
    assert update.update_rows[0].price == '20'


def test_whole_auction_multibid_case_1():
    auc = auction.AuctionState("Tester")
    lines = [
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open Cloak of Flames'",
        "[Wed Jun 12 23:07:49 2019] Foobar -> Quaff: Cloak of Flames  10",
        "[Wed Jun 12 23:07:49 2019] Playerone -> Quaff: Cloak of Flames  10",
        "[Wed Jun 12 23:07:49 2019] Playerone -> Quaff: Cloak of Flames  11, 15 alt",
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids closed Cloak of Flames '",
    ]
    for line in lines:
        # we assume that every action was parsed properly. parse failures will cause a type error here
        actions = parse.handle_line(line, set(['Cloak of Flames']))
        if not isinstance(actions, list):
            actions = [actions]
        for action in actions:
            update = auc.update(action)
    finished_auction = auc.concluded_auctions[0]
    assert finished_auction['item'] == 'Cloak of Flames'
    assert len(finished_auction['bids']) == 4
    assert update.update_rows[0].winner == "Playerone"
    assert update.update_rows[0].price == '11'


def test_whole_auction_multibid_case_2():
    auc = auction.AuctionState("Tester")
    lines = [
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open Cloak of Flames !2'",
        "[Wed Jun 12 23:07:49 2019] Foobar -> Quaff: Cloak of Flames  5",
        "[Wed Jun 12 23:07:49 2019] Playerone -> Quaff: Cloak of Flames  10",
        "[Wed Jun 12 23:07:49 2019] Playerone -> Quaff: Cloak of Flames  11, 15 alt",
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids closed Cloak of Flames '",
    ]
    for line in lines:
        # we assume that every action was parsed properly. parse failures will cause a type error here
        actions = parse.handle_line(line, set(['Cloak of Flames']))
        if not isinstance(actions, list):
            actions = [actions]
        for action in actions:
            update = auc.update(action)
    finished_auction = auc.concluded_auctions[0]
    assert finished_auction['item'] == 'Cloak of Flames'
    assert len(finished_auction['bids']) == 4
    assert update.update_rows[0].winner == "Playerone, Playerone's alt"
    assert update.update_rows[0].price == '11, 15'


def test_sort_bids_1():
    bids = [{'player': 'Adam', 'value': 100, 'comment': '', 'status_flag': 'alt', 'is_alt': True, 'tier': 0, 'cmp': (0, 100)},
            {'player': 'Mandy', 'value': 6, 'comment': '',
             'status_flag': None, 'is_alt': False, 'tier': 0, 'cmp': (1, 6)},
            {'player': 'Mike', 'value': 5, 'comment': '',
             'status_flag': None, 'is_alt': False, 'tier': 0, 'cmp': (0, 5)}
            ]
    sorted = auction.sort_bids(bids)
    print(sorted)
    ordering = [x['player'] for x in sorted]

    # a main that bids 6 or more beats an alt, no matter they they bid
    # an alt that bids 6 or more can beat a main that bid 5 or less
    assert ordering == ['Mandy', 'Adam', 'Mike']


def test_sort_bids_2():
    bids = [{'player': 'Adam', 'value': 100, 'comment': '', 'status_flag': 'alt', 'is_alt': True, 'tier': 0, 'cmp': (0, 100)},
            {'player': 'Frank', 'value': 11, 'comment': '',
                'status_flag': 'fnf', 'is_alt': False, 'tier': 1, 'cmp': (1, 11)},
            {'player': 'Mandy', 'value': 10, 'comment': '',
                'status_flag': None, 'is_alt': False, 'tier': 1, 'cmp': (1, 10)}
            ]
    sorted = auction.sort_bids(bids)
    print(sorted)
    ordering = [x['player'] for x in sorted]

    # the alt is totally frozen out because the bid was 6 or higher
    # the FNF beats the main because the main did not bid 11 or higher
    assert ordering == ['Frank', 'Mandy', 'Adam']
