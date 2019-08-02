import uuid


class AuctionState:
    def __init__(self):
        self.active_auctions = {}
        self.concluded_auctions = []

    def update(self, action):
        if action['action'] == 'AUCTION_START':
            # create a new auction
            item = action['item_name']
            timestamp = action['timestamp']
            if item in self.active_auctions:
                return None
            iid = uuid.uuid1()
            self.active_auctions[item] = {'item': item, 'iid': iid, 'bids': {}}
            return ActionResult(add_rows=[Row(iid=iid, timestamp=timestamp, item=item, status='Open')])

        elif action['action'] == 'BID':
            item = action['item_name']
            player = action['player_name']
            value = action['value']
            if item not in self.active_auctions:
                return None
            self.active_auctions[item]['bids'][player] = value

        elif action['action'] == 'AUCTION_CLOSE':
            item = action['item_name']
            if item not in self.active_auctions:
                return None
            bids = self.active_auctions[item]['bids']
            if bids:
                winner, winning_bid = max(bids.items(), key=lambda x: x[1])
            else:
                winner = 'ROT'
                winning_bid = ''

            iid = self.active_auctions[item]['iid']
            self.concluded_auctions.append(self.active_auctions[item])
            del self.active_auctions[item]

            return ActionResult(update_rows=[Row(iid=iid, item=item, status='Concluded', winner=winner,
                                                 price=winning_bid)])

        elif action['action'] == 'AUCTION_CANCEL':
            item = action['item_name']
            if item not in self.active_auctions:
                return

            iid = self.active_auctions[item]['iid']
            del self.active_auctions[item]
            return {'new_rows': [],
                    'update_rows': [{'iid': iid, 'item': item, 'status': 'Cancelled', 'winner': '', 'price': ''}]}


class ActionResult:
    def __init__(self, add_rows=None, update_rows=None):
        if add_rows is not None:
            self.add_rows = add_rows
        else:
            self.add_rows = []
        if update_rows is not None:
            self.update_rows = update_rows
        else:
            self.update_rows = []


class Row:
    def __init__(self, iid, item, status, timestamp=None, winner='', price=''):
        self.iid = iid
        self.timestamp = timestamp
        self.item = item
        self.status = status
        self.winner = winner
        self.price = price
