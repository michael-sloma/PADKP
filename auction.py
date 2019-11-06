import uuid
import datetime as dt

MAIN_BEATS_ALTS_BID = 10


class AuctionState:
    def __init__(self):
        self.active_auctions = {}
        self.concluded_auctions = []

    def update(self, action):
        # before we do anything else, we check if any auctions need to be expired
        result = ActionResult()
        for item, auction in list(self.active_auctions.items()):
            if action['timestamp'] - auction['time'] > dt.timedelta(minutes=30):
                print("expiring an auction for", item)
                self.archive_current_auction(item)
                iid = auction['iid']
                item_count = auction['item_count']
                result.update_rows.append(Row(iid=iid, item=item, item_count=item_count, status='Expired'))

        if action['action'] == 'AUCTION_START':
            # create a new auction
            item = action['item_name']
            timestamp = action['timestamp']
            item_count = action['item_count']
            if item in self.active_auctions:
                return result
            iid = str(uuid.uuid1())
            self.active_auctions[item] = {'item': item, 'iid': iid, 'bids': {}, 'time': timestamp,
                                          'item_count':item_count}
            result.add_rows.append(Row(iid=iid, timestamp=timestamp, item=item, item_count=item_count, status='Open'))

        elif action['action'] == 'BID':
            item = action['item_name']
            player = action['player_name']
            bid = {'value': action['value'],
                   'comment': action['comment'],
                   'alt': action['alt']}
            if item not in self.active_auctions:
                return result
            self.active_auctions[item]['bids'][player] = bid

        elif action['action'] == 'AUCTION_CLOSE':
            update = self.handle_auction_close(action)
            if update:
                result.update_rows.append(update)

        elif action['action'] == 'AUCTION_CANCEL':
            item = action['item_name']
            if item not in self.active_auctions:
                return result

            iid = self.active_auctions[item]['iid']
            item_count = self.active_auctions[item]['item_count']
            del self.active_auctions[item]
            result.update_rows.append(Row(iid=iid, item=item, item_count=item_count, status='Cancelled'))

        elif action['action'] == 'AUCTION_AWARD':
            item = action['item_name']
            auction = self.get_most_recent_auction_by_name(item)
            iid = auction['iid']
            item_count = auction['item_count']

            winners = ', '.join(action['winners'])
            bids = ', '.join(action['bids'])
            result.update_rows.append(Row(iid=iid, item=item, item_count=item_count, status='Concluded',
                                          winner=winners, price=bids))
        elif action['action'] == 'FAILED_BID':
            line = action['data']
            result.status_messages.append(f'Failed to parse bid: {line}')
        return result

    def archive_current_auction(self, item):
        self.concluded_auctions.append(self.active_auctions[item])
        del self.active_auctions[item]

    def handle_auction_close(self, action):
        item = action['item_name']
        if item not in self.active_auctions:
            return None

        bids = self.active_auctions[item]['bids']
        iid = self.active_auctions[item]['iid']
        n_items = self.active_auctions[item]['item_count']
        n_bids = len(bids)

        # check if a main bid 5 or more. if so, alts can't beat mains
        sorted_bids = sort_bids(bids)

        tie = False
        # there are no bids. Item rots.
        if n_bids == 0:
            result = Row(iid=iid, item=item, item_count=n_items, status='Concluded', winner='ROT')
        # there are at least as many items as bidders. Everyone gets loot.
        elif n_bids <= n_items:
            winners = [x[0] for x in sorted_bids]
            prices = [str(x[1]['value']) for x in sorted_bids]
            while len(winners) < n_items:
                winners.append('ROT')
            result = Row(iid=iid, item=item, item_count=n_items, status='Concluded', winner=', '.join(winners),
                       price=', '.join(prices))
        # there more more bidders than items. We have to compare bids.
        else:
            lowest_winning_bid = sorted_bids[n_items-1][1]['value']
            next_lower_bid = sorted_bids[n_items][1]['value']
            if lowest_winning_bid == next_lower_bid:
                tie = True
                tied_bids = [x for x in sorted_bids if x[1]['value'] >= lowest_winning_bid]
                winners = ', '.join(x[0] for x in tied_bids)
                prices = ', '.join(str(x[1]['value']) for x in tied_bids)
                result = Row(iid=iid, item=item, item_count=n_items, status='Tied', winner=winners, price=prices)
            else:
                winning_bids = sorted_bids[:n_items]
                winners = ', '.join(x[0] for x in winning_bids)
                prices = ', '.join(str(x[1]['value']) for x in winning_bids)
                result = Row(iid=iid, item=item, item_count=n_items, status='Concluded', winner=winners, price=prices)
        if not tie:
            self.archive_current_auction(item)
        return result

    def get_auction_by_iid(self, iid):
        print('searching iid', iid)
        all_auctions_ever = list(self.active_auctions.values()) + self.concluded_auctions
        for auction in all_auctions_ever:
            if auction['iid'] == iid:
                return auction
        return None

    def get_most_recent_auction_by_name(self, item_name):
        print('searching by name', item_name)
        all_auctions_ever = list(self.active_auctions.values()) + self.concluded_auctions
        all_auctions_ever = sorted(all_auctions_ever, key=lambda auc: auc['time'], reverse=True)
        for auction in all_auctions_ever:
            if auction['item'] == item_name:
                return auction
        return None


def sort_bids(bids):
    max_main_bid = max([0] + [bid['value'] for bid in bids.values() if not bid['alt']])
    if max_main_bid >= MAIN_BEATS_ALTS_BID:
        # alts can't beat mains
        bid_comparison = lambda bid: (not bid[1]['alt'], bid[1]['value'])
    else:
        bid_comparison = lambda bid: bid[1]['value']
    return sorted(bids.items(), key=bid_comparison, reverse=True)


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
        self.status_messages = []


class Row:
    def __init__(self, iid, item, item_count, status, timestamp=None, winner='', price=''):
        self.iid = iid
        self.timestamp = timestamp
        self.item = item
        self.status = status
        self.winner = winner
        self.price = price
        self.item_count = item_count
