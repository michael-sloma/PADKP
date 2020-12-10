import uuid
import datetime as dt

MAIN_BEATS_ALTS_BID = 11


class AuctionState:
    def __init__(self, my_name=''):
        self.active_auctions = {}
        self.preregistered_bids = {}
        self.concluded_auctions = []
        self.my_name = my_name
        self.waitlist = {}

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
        # expire old waitlist entries
        remove_from_waitlist = []
        for name in self.waitlist:
            if action['timestamp'] - self.waitlist[name] > dt.timedelta(hours=8):
                remove_from_waitlist.append(name)
        for name in remove_from_waitlist:
            del self.waitlist[name]

        if action['action'] in ('AUCTION_START', 'SUICIDE_START'):
            # create a new auction
            item = action['item_name']
            timestamp = action['timestamp']
            item_count = action['item_count']
            if item in self.active_auctions:
                return result
            iid = str(uuid.uuid1())
            self.active_auctions[item] = {'item': item, 'iid': iid, 'bids': {}, 'time': timestamp,
                                          'item_count': item_count}

            # if we've pre-registered a bid for this item, add it to the auction now
            if item in self.preregistered_bids:
                pre_bid = self.preregistered_bids[item]
                tier = _calculate_bid_tier(pre_bid['value'], pre_bid['status_flag'], pre_bid['is_alt'])
                bid = {'value': pre_bid['value'],
                       'comment': pre_bid['comment'],
                       'is_alt': pre_bid['is_alt'],
                       'status_flag': pre_bid['status_flag'],
                       'is_second_class_citizen': pre_bid['status_flag'] is not None,
                       'player': self.my_name,
                       'tier': tier,
                       'cmp': (tier, pre_bid['value'])
                       }
                self.active_auctions[item]['bids'][self.my_name] = bid
                del self.preregistered_bids[item]

            result.add_rows.append(Row(iid=iid, timestamp=timestamp, item=item, item_count=item_count, status='Open'))

        elif action['action'] == 'BID':
            item = action['item_name']
            player = action['player_name']
            if action['is_alt']:
                player += "'s alt"
            tier = _calculate_bid_tier(action['value'], action['status_flag'], action['is_alt'])
            bid = {'value': action['value'],
                   'comment': action['comment'],
                   'is_alt': action['is_alt'],
                   'status_flag': action['status_flag'],
                   'is_second_class_citizen': action['status_flag'] is not None,
                   'player': player,
                   'tier': tier,
                   'cmp': (tier, action['value'])
                   }
            if item not in self.active_auctions:
                return result
            print('NEW BID', bid)
            self.active_auctions[item]['bids'][player] = bid

        elif action['action'] == 'SUICIDE_BID':
            item = action['item_name']
            player = action['player_name']
            bid = {'value': '?',
                   'comment': None,
                   'alt': None}
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
            if auction is None:
                print('could not find the auction to award. typo or malformed command?')
                line = action['data']
                result.status_messages.append(f'Failed to parse auction award: {line}')
                return result
            iid = auction['iid']
            item_count = auction['item_count']

            winners = ', '.join(action['winners'])
            bids = ', '.join(action['bids'])
            result.update_rows.append(Row(iid=iid, item=item, item_count=item_count, status='Concluded',
                                          winner=winners, price=bids))
            if item in self.active_auctions:
                self.archive_current_auction(item)

        elif action['action'] == 'FAILED_BID':
            if self.active_auctions:
                line = action['data']
                result.status_messages.append(f'Failed to parse bid: {line}')

        elif action['action'] == 'PREREGISTER':
            print('got a prereg', action)
            self.preregistered_bids[action['item_name']] = action

        elif action['action'] == 'WAITLIST_ADD':
            print('got a waitlist entry', action)
            self.waitlist[action['name']] = action['timestamp']

        elif action['action'] in ['WAITLIST_REMOVE', 'WAITLIST_DELETE']:
            print('got a waitlist delete', action)
            if action['name'] in self.waitlist:
                del self.waitlist[action['name']]

        elif action['action'] == 'JOINED RAID':
            print('character joined raid', action)
            if action['name'] in self.waitlist:
                print('removing {} from waitlist'.format(action['name']))
                del self.waitlist[action['name']]

        elif action['action'] in ['WAITLIST_CLEAR', 'WAITLIST_PURGE']:
            print('got a waitlist clear', action)
            self.waitlist = {}

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
        sorted_bids = sort_bids(bids.values())

        tie = False
        # there are no bids. Item rots.
        if n_bids == 0:
            result = Row(iid=iid, item=item, item_count=n_items, status='Concluded', winner='ROT')
        # there are at least as many items as bidders. Everyone gets loot.
        elif n_bids <= n_items:
            winners = [x['player'] for x in sorted_bids]
            prices = [str(x['value']) for x in sorted_bids]
            while len(winners) < n_items:
                winners.append('ROT')
            result = Row(iid=iid, item=item, item_count=n_items, status='Concluded', winner=', '.join(winners),
                       price=', '.join(prices))
        # there more more bidders than items. We have to compare bids.
        else:
            lowest_winning_bid = sorted_bids[n_items-1]['cmp']
            next_lower_bid = sorted_bids[n_items]['cmp']
            if lowest_winning_bid == next_lower_bid:
                tie = True
                tied_bids = [x for x in sorted_bids if x['cmp'] >= lowest_winning_bid]
                winners = ', '.join(x['player'] for x in tied_bids)
                prices = ', '.join(str(x['value']) for x in tied_bids)
                result = Row(iid=iid, item=item, item_count=n_items, status='Tied', winner=winners, price=prices)
            else:
                winning_bids = sorted_bids[:n_items]
                winners = ', '.join(x['player'] for x in winning_bids)
                prices = ', '.join(str(x['value']) for x in winning_bids)
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


def calculate_bid_tier(bid):
    """ determine the priority for a bid, based on who sent it and how much they bid """
    char_name, bid = bid
    return _calculate_bid_tier(bid['value'], bid['status_flag'], bid['is_alt'])


def _calculate_bid_tier(value, status_flag, is_alt):
    """ determine the priority for a bid, based on who sent it and how much they bid """
    tier_2_threshold = 11
    tier_1_threshold = 6
    if not status_flag and value >= tier_2_threshold:
        return 2
    elif not is_alt and value >= tier_1_threshold:
        return 1
    else:
        return 0


def sort_bids(bids):
    """
    if the bid is 11 or higher and it's from a main, then the main wins
    an alt can beat a main that bid 10 or less
    """
    return sorted(bids, key=lambda bid: bid['cmp'], reverse=True)


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
