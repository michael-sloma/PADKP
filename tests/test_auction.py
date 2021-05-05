import auction
import parse
import responses
import json


@responses.activate
def test_whole_auction_case_1():
    auc = auction.AuctionState("Tester")
    lines = [
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open Cloak of Flames'",
        "[Wed Jun 12 23:07:49 2019] Foobar tells you, 'Cloak of Flames  10'",
        "[Wed Jun 12 23:07:49 2019] Playerone tells you, 'Cloak of Flames  10'",
        "[Wed Jun 12 23:07:49 2019] Playerone tells you, 'Cloak of Flames  11'",
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids closed Cloak of Flames '",
    ]

    body = {'message': 'Cloak of Flames awarded to - Playerone for 11', 'warnings': []}

    responses.add(responses.POST,
                  'http://padkp.net/api/resolve_auction/', json=body)
    for line in lines:
        # we assume that every action was parsed properly. parse failures will cause a type error here
        actions = parse.handle_line(line, set(['Cloak of Flames']))
        if not isinstance(actions, list):
            actions = [actions]
        for action in actions:
            auc.update(action)
    data = json.loads(responses.calls[0].request.body)
    finished_auction = auc.concluded_auctions['Cloak of Flames']
    assert finished_auction['item'] == 'Cloak of Flames'
    assert len(finished_auction['bids']) == 4
    assert data['bids'] == [{'name': 'Foobar', 'bid': 10, 'tag': ''}, {
        'name': 'Playerone', 'bid': 11, 'tag': ''}]
    assert data['item_name'] == 'Cloak of Flames'
    assert data['item_count'] == 1


@responses.activate
def test_whole_auction_case_3():
    auc = auction.AuctionState("Tester")
    lines = [
        "[Wed Jun 12 23:01:33 2019] You tell your raid, '!Bids open Amulet of Necropotence'",
        "[Wed Jun 12 23:07:49 2019] Foo tells you, 'Amulet of Necropotence 90'",
        "[Wed Jun 12 23:07:49 2019] Bar tells you, 'Amulet of Necropotence 112 ALT'",
        "[Wed Jun 12 23:07:49 2019] Baz tells you, 'Amulet of Necropotence 75'",
        "[Wed Jun 12 23:07:49 2019] Qux tells you, 'Amulet of Necropotence 40'",
        "[Wed Jun 12 23:07:49 2019] Quux tells you, 'Amulet of Necropotence 2'",
        "[Wed Jun 12 23:07:49 2019] Thud tells you, 'Amulet of Necropotence 89'",
        "[Wed Jun 12 23:07:49 2019] Waldo tells you, 'Amulet of Necropotence 13'",
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids closed Amulet of Necropotence'",
    ]

    body = {'message': 'Cloak of Flames awarded to - Foo for 1',
            'warnings': ['bad bid 1', 'bad bid 2']}
    responses.add(responses.POST,
                  'http://padkp.net/api/resolve_auction/', json=body)

    for line in lines:
        actions = parse.handle_line(line, set(['Amulet of Necropotence']))
        # we assume that every action was parsed properly. parse failures will cause a type error here
        if not isinstance(actions, list):
            actions = [actions]
        for action in actions:
            update = auc.update(action)

    data = json.loads(responses.calls[0].request.body)

    assert len(auc.concluded_auctions) == 1
    assert len(update.update_rows) == 1
    assert update.update_rows[0].winner == 'Cloak of Flames awarded to - Foo for 1'
    assert data['bids'] == [{'name': 'Foo', 'bid': 90, 'tag': ''},
                            {'name': "Bar's alt", 'bid': 112, 'tag': 'ALT'},
                            {'name': 'Baz', 'bid': 75, 'tag': ''},
                            {'name': 'Qux', 'bid': 40, 'tag': ''},
                            {'name': 'Quux', 'bid': 2, 'tag': ''},
                            {'name': 'Thud', 'bid': 89, 'tag': ''},
                            {'name': 'Waldo', 'bid': 13, 'tag': ''}]
    assert update.update_rows[0].warnings == 'bad bid 1, bad bid 2'


def test_failed_bid_case():
    auc = auction.AuctionState("Tester")
    lines = [
        "[Wed Jun 23 23:24:33 2019] You tell your raid, '!Bids open !2 Cloak of Flames'",
        "[Wed Jun 23 23:07:49 2019] Foo tells you, 'Cloak of Flames  35'",
        "[Wed Jun 23 23:07:49 2019] Bar tells you, 'Cloak of Flames  56'",
        "[Wed Jun 23 23:07:49 2019] Bar tells you, 'I don't understand the rules, help?",
    ]
    for line in lines:
        actions = parse.handle_line(line, set(['Cloak of Flames']))
        # we assume that every action was parsed properly. parse failures will cause a type error here
        if not isinstance(actions, list):
            actions = [actions]
        for action in actions:
            update = auc.update(action)
    assert update.status_messages[0] == "Failed to parse bid: Bar tells you, 'I don't understand the rules, help?"


@responses.activate
def test_preregister_bid():
    auc = auction.AuctionState("Tester")
    lines = [
        "[Wed Jun 12 23:24:32 2019] You told Grunt, '!preregister Cloak of Flames 20'",
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open Cloak of Flames'",
        "[Wed Jun 12 23:07:49 2019] Foobar tells you, 'Cloak of Flames  10'",
        "[Wed Jun 12 23:07:49 2019] Playerone tells you, 'Cloak of Flames  10'",
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids closed Cloak of Flames '",
    ]

    body = {'message': 'Cloak of Flames awarded to - Tester for 1', 'warnings': []}
    responses.add(responses.POST,
                  'http://padkp.net/api/resolve_auction/', json=body)

    for line in lines:
        # we assume that every action was parsed properly. parse failures will cause a type error here
        actions = parse.handle_line(line, set(['Cloak of Flames']))
        if not isinstance(actions, list):
            actions = [actions]
        for action in actions:
            update = auc.update(action)

    data = json.loads(responses.calls[0].request.body)
    finished_auction = auc.concluded_auctions['Cloak of Flames']
    assert finished_auction['item'] == 'Cloak of Flames'
    assert len(finished_auction['bids']) == 6
    assert update.update_rows[0].winner == 'Cloak of Flames awarded to - Tester for 1'
    assert data['bids'] == [{'name': 'Tester', 'bid': 20, 'tag': ''},
                            {'name': "Foobar", 'bid': 10, 'tag': ''},
                            {'name': 'Playerone', 'bid': 10, 'tag': ''}]


@responses.activate
def test_preregister_bid_alt():
    auc = auction.AuctionState("Tester")
    lines = [
        "[Wed Jun 12 23:24:32 2019] You told Grunt, '!preregister Cloak of Flames 20 alt'",
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open Cloak of Flames'",
        "[Wed Jun 12 23:07:49 2019] Foobar tells you, 'Cloak of Flames  5'",
        "[Wed Jun 12 23:07:49 2019] Playerone tells you, 'Cloak of Flames  5'",
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids closed Cloak of Flames '",
    ]

    body = {'message': 'Cloak of Flames awarded to - Tester for 1', 'warnings': []}
    responses.add(responses.POST,
                  'http://padkp.net/api/resolve_auction/', json=body)
    for line in lines:
        # we assume that every action was parsed properly. parse failures will cause a type error here
        actions = parse.handle_line(line, set(['Cloak of Flames']))
        if not isinstance(actions, list):
            actions = [actions]
        for action in actions:
            update = auc.update(action)

    data = json.loads(responses.calls[0].request.body)
    finished_auction = auc.concluded_auctions['Cloak of Flames']

    assert finished_auction['item'] == 'Cloak of Flames'
    assert len(finished_auction['bids']) == 6
    assert update.update_rows[0].winner == 'Cloak of Flames awarded to - Tester for 1'
    assert data['bids'] == [{'name': 'Tester\'s alt', 'bid': 20, 'tag': 'ALT'},
                            {'name': "Foobar", 'bid': 5, 'tag': ''},
                            {'name': 'Playerone', 'bid': 5, 'tag': ''}]


@responses.activate
def test_whole_auction_multibid_case_1():
    auc = auction.AuctionState("Tester")
    lines = [
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open Cloak of Flames'",
        "[Wed Jun 12 23:07:49 2019] Foobar tells you, 'Cloak of Flames  10'",
        "[Wed Jun 12 23:07:49 2019] Playerone tells you, 'Cloak of Flames  10'",
        "[Wed Jun 12 23:07:49 2019] Playerone tells you, 'Cloak of Flames  11, 15 alt'",
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids closed Cloak of Flames '",
    ]

    body = {'message': 'Cloak of Flames awarded to - Tester for 1', 'warnings': []}
    responses.add(responses.POST,
                  'http://padkp.net/api/resolve_auction/', json=body)
    for line in lines:
        # we assume that every action was parsed properly. parse failures will cause a type error here
        actions = parse.handle_line(line, set(['Cloak of Flames']))
        if not isinstance(actions, list):
            actions = [actions]
        for action in actions:
            update = auc.update(action)
    finished_auction = auc.concluded_auctions['Cloak of Flames']
    data = json.loads(responses.calls[0].request.body)

    assert finished_auction['item'] == 'Cloak of Flames'
    assert len(finished_auction['bids']) == 4
    assert update.update_rows[0].winner == 'Cloak of Flames awarded to - Tester for 1'
    assert data['bids'] == [{'name': 'Foobar', 'bid': 10, 'tag': ''},
                            {'name': "Playerone", 'bid': 11, 'tag': ''},
                            {'name': 'Playerone\'s alt', 'bid': 15, 'tag': 'ALT'}]


@responses.activate
def test_whole_auction_cancel_pre_close_case():
    auc = auction.AuctionState("Tester")
    lines = [
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open Cloak of Flames'",
        "[Wed Jun 12 23:07:49 2019] Foobar tells you, 'Cloak of Flames  10'",
        "[Wed Jun 12 23:07:49 2019] Playerone tells you, 'Cloak of Flames  10'",
        "[Wed Jun 12 23:07:49 2019] Playerone tells you, 'Cloak of Flames  11, 15 alt'",
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Cancel Cloak of Flames '",
    ]

    for line in lines:
        # we assume that every action was parsed properly. parse failures will cause a type error here
        actions = parse.handle_line(line, set(['Cloak of Flames']))
        if not isinstance(actions, list):
            actions = [actions]
        for action in actions:
            update = auc.update(action)

    assert len(auc.concluded_auctions) == 0
    assert auc.active_auctions == {}


@responses.activate
def test_whole_auction_cancel_after_close_case():
    auc = auction.AuctionState("Tester")
    lines = [
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open Cloak of Flames'",
        "[Wed Jun 12 23:07:49 2019] Foobar tells you, 'Cloak of Flames  10'",
        "[Wed Jun 12 23:07:49 2019] Playerone tells you, 'Cloak of Flames  10'",
        "[Wed Jun 12 23:07:49 2019] Playerone tells you, 'Cloak of Flames  11, 15 alt'",
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids closed Cloak of Flames '",
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Cancel Cloak of Flames '",
    ]

    body = {'message': 'Cloak of Flames awarded to - Tester for 1', 'warnings': []}
    responses.add(responses.POST,
                  'http://padkp.net/api/resolve_auction/', json=body)
    responses.add(responses.POST,
                  'http://padkp.net/api/cancel_auction/', json=body)

    for line in lines:
        # we assume that every action was parsed properly. parse failures will cause a type error here
        actions = parse.handle_line(line, set(['Cloak of Flames']))
        if not isinstance(actions, list):
            actions = [actions]
        for action in actions:
            update = auc.update(action)

    close_finger = json.loads(responses.calls[0].request.body)['fingerprint']
    cancel_finger = json.loads(responses.calls[1].request.body)['fingerprint']

    assert len(auc.concluded_auctions) == 0
    assert auc.active_auctions == {}
    assert close_finger == cancel_finger


@responses.activate
def test_whole_auction_correction_after_close_case():
    auc = auction.AuctionState("Tester")
    lines = [
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open Cloak of Flames'",
        "[Wed Jun 12 23:07:49 2019] Foobar tells you, 'Cloak of Flames  10'",
        "[Wed Jun 12 23:07:49 2019] Playerone tells you, 'Cloak of Flames  10'",
        "[Wed Jun 12 23:07:49 2019] Playerone tells you, 'Cloak of Flames  11, 15 alt'",
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids closed Cloak of Flames '",
        "[Wed Jun 23 23:24:34 2019] You tell your raid, '!correction !award Cloak of Flames !to Baz 30'",
    ]

    body = {'message': 'Cloak of Flames awarded to - Tester for 1', 'warnings': []}
    responses.add(responses.POST,
                  'http://padkp.net/api/resolve_auction/', json=body)
    responses.add(responses.POST,
                  'http://padkp.net/api/correct_auction/', json=body)

    for line in lines:
        # we assume that every action was parsed properly. parse failures will cause a type error here
        actions = parse.handle_line(line, set(['Cloak of Flames']))
        if not isinstance(actions, list):
            actions = [actions]
        for action in actions:
            update = auc.update(action)

    close_finger = json.loads(responses.calls[0].request.body)['fingerprint']
    correct_finger = json.loads(responses.calls[1].request.body)['fingerprint']
    data = json.loads(responses.calls[1].request.body)

    assert len(auc.concluded_auctions) == 1
    assert close_finger == correct_finger
    assert data['bids'] == [{'name': 'Baz', 'bid': '30'}]


@responses.activate
def test_whole_auction_correction_after_close_multibid_case():
    auc = auction.AuctionState("Tester")
    lines = [
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids open !2 Cloak of Flames'",
        "[Wed Jun 12 23:07:49 2019] Foobar tells you, 'Cloak of Flames  10'",
        "[Wed Jun 12 23:07:49 2019] Playerone tells you, 'Cloak of Flames  10'",
        "[Wed Jun 12 23:07:49 2019] Playerone tells you, 'Cloak of Flames  11, 15 alt'",
        "[Wed Jun 12 23:24:33 2019] You tell your raid, '!Bids closed Cloak of Flames '",
        "[Wed Jun 23 23:24:34 2019] You tell your raid, '!correction !award Cloak of Flames !to Baz 30, Foobar 15'",
    ]

    body = {'message': 'Cloak of Flames awarded to - Tester for 1', 'warnings': []}
    responses.add(responses.POST,
                  'http://padkp.net/api/resolve_auction/', json=body)
    responses.add(responses.POST,
                  'http://padkp.net/api/correct_auction/', json=body)

    for line in lines:
        # we assume that every action was parsed properly. parse failures will cause a type error here
        actions = parse.handle_line(line, set(['Cloak of Flames']))
        if not isinstance(actions, list):
            actions = [actions]
        for action in actions:
            update = auc.update(action)

    close_finger = json.loads(responses.calls[0].request.body)['fingerprint']
    correct_finger = json.loads(responses.calls[1].request.body)['fingerprint']
    data = json.loads(responses.calls[1].request.body)

    assert len(auc.concluded_auctions) == 1
    assert close_finger == correct_finger
    assert data['bids'] == [{'name': 'Baz', 'bid': '30'}, {
        'name': 'Foobar', 'bid': '15'}]
