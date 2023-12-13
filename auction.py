import uuid
import datetime as dt
import api_client

MAIN_BEATS_ALTS_BID = 11


class AuctionState:
    def __init__(self, my_name=''):
        self.active_auctions = {}
        self.preregistered_bids = {}
        self.concluded_auctions = {}
        self.my_name = my_name
        self.alt_name = my_name + "'s alt"
        self.waitlist = {}
        self.startup_time = None
        self.api_token = None

    def update(self, action):
        # before we do anything else, we check if any auctions need to be expired
        result = ActionResult()
        for item, auction in list(self.active_auctions.items()):
            if action['timestamp'] - auction['time'] > dt.timedelta(minutes=30):
                print("expiring an auction for", item)
                self.archive_current_auction(item)
                iid = auction['iid']
                item_count = auction['item_count']
                result.update_rows.append(
                    Row(iid=iid, item=item, item_count=item_count, status='Expired'))
        # expire old waitlist entries
        remove_from_waitlist = []
        for name in self.waitlist:
            if action['timestamp'] - self.waitlist[name] > dt.timedelta(hours=8):
                remove_from_waitlist.append(name)
        for name in remove_from_waitlist:
            del self.waitlist[name]

        # Don't parse events in log before the application starts
        if self.startup_time and action['timestamp'] < self.startup_time:
            return

        if action['action'] == 'initialize':
            self.startup_time = dt.datetime.now()
            self.api_token = action['api_token']
        elif action['action'] in ('AUCTION_START', 'SUICIDE_START', 'FLAG_START'):
            # create a new auction
            item = action['item_name']
            timestamp = action['timestamp']
            item_count = action['item_count']
            if item in self.active_auctions:
                return result
            iid = str(uuid.uuid1())
            self.active_auctions[item] = {'item': item, 'iid': iid, 'bids': {}, 'time': timestamp,
                                          'item_count': item_count, 'flag_auction': action['action'] == 'FLAG_START'}

            # if we've pre-registered a bid for this item, add it to the auction now
            if item in self.preregistered_bids:
                self.active_auctions[item]['bids'][self.my_name] = []
                self.active_auctions[item]['bids'][self.my_name+"'s alt"] = []
                for pre_bid in self.preregistered_bids[item]:
                    tier = _calculate_bid_tier(
                        pre_bid['value'], pre_bid['status_flag'], pre_bid['is_alt'])
                    name = self.alt_name if pre_bid['is_alt'] else self.my_name
                    bid = {'value': pre_bid['value'],
                           'comment': pre_bid['comment'],
                           'is_alt': pre_bid['is_alt'],
                           'status_flag': pre_bid['status_flag'],
                           'is_second_class_citizen': pre_bid['status_flag'] is not None,
                           'player': name,
                           'tier': tier,
                           'cmp': (tier, pre_bid['value'])
                           }
                    self.active_auctions[item]['bids'][name].append(bid)
                del self.preregistered_bids[item]

            result.add_rows.append(Row(
                iid=iid, timestamp=timestamp, item=item, item_count=item_count, status='Open'))

        elif action['action'] == 'RESET':
            item = action['item_name']
            if item not in self.active_auctions:
                return result
            player = action['player_name']
            if self.active_auctions[item]['flag_auction']:
                self.active_auctions[item]['bids'].pop(player, None)
            else:
                self.active_auctions[item]['bids'][player] = []
                self.active_auctions[item]['bids'][player+"'s alt"] = []

        elif action['action'] == 'BID':
            item = action['item_name']
            player = action['player_name']
            if action['is_alt']:
                player += "'s alt"
            tier = _calculate_bid_tier(
                action['value'], action['status_flag'], action['is_alt'])
            bid = {'value': action['value'],
                   'comment': action['comment'],
                   'is_alt': action['is_alt'],
                   'status_flag': action['status_flag'] or '',
                   'is_second_class_citizen': action['status_flag'] is not None,
                   'player': player,
                   'tier': tier,
                   'cmp': (tier, action['value'])
                   }
            if item not in self.active_auctions:
                return result
            if self.active_auctions[item]['flag_auction']:
                return result
            print('NEW BID', bid)
            self.active_auctions[item]['bids'][player].append(bid)

        elif action['action'] == 'FLAG_BID':
            item = action['item_name']
            player = action['player_name']
            if item not in self.active_auctions:
                return result
            if not self.active_auctions[item]['flag_auction']:
                return result
            print('NEW FLAG BID', {'item': item, 'player': player})
            self.active_auctions[item]['bids'][player] = True

        elif action['action'] == 'FLAG_SELF_BID':
            item = action['item_name']
            player = self.my_name
            if item not in self.active_auctions:
                return result
            print('NEW FLAG BID', {'item': item, 'player': player})
            self.active_auctions[item]['bids'][player] = True

        elif action['action'] == 'SUICIDE_BID':
            item = action['item_name']
            player = action['player_name']
            bid = {'value': '?',
                   'comment': None,
                   'alt': None}
            if item not in self.active_auctions:
                return result
            self.active_auctions[item]['bids'][player] = bid

        elif action['action'] == 'FLAG_CLOSE':
            update = self.handle_flag_close(action)
            if update:
                result.update_rows.append(update)

        elif action['action'] == 'AUCTION_CLOSE':
            update = self.handle_auction_close(action)
            if update:
                result.update_rows.append(update)

        elif action['action'] == 'AUCTION_CANCEL':
            item = action['item_name']
            if item in self.active_auctions:
                auction = self.active_auctions[item]
                iid = auction['iid']
                item_count = auction['item_count']
                del self.active_auctions[item]
                result.update_rows.append(
                    Row(iid=iid, item=item, item_count=item_count, status='Cancelled'))

            elif item in self.concluded_auctions:
                auction = self.concluded_auctions[item]
                iid = auction['iid']
                item_count = auction['item_count']
                bids = self.process_bids_for_export(auction['bids'])
                response = api_client.cancel_auction(
                    bids, item, item_count, iid, self.api_token)
                if response is None or response.status_code == 200:
                    del self.concluded_auctions[item]
                    result.update_rows.append(
                        Row(iid=iid, item=item, item_count=item_count, status='Cancelled'))
                else:
                    result.update_rows.append(
                        Row(iid=iid, item=item, item_count=item_count, status='Error', warnings=response.text))

        elif action['action'] == 'AUCTION_AWARD':
            item = action['item_name']
            auction = self.get_most_recent_auction_by_name(item)
            if auction is None:
                print('could not find the auction to award. typo or malformed command?')
                line = action['data']
                result.status_messages.append(
                    f'Failed to parse auction award: {line}')
                return result
            iid = auction['iid']
            item_count = auction['item_count']

            winners = ', '.join(action['winners'])+', '.join(action['bids'])

            winner_bids = [{'name': pair[0], 'bid': pair[1]}
                           for pair in zip(action['winners'], action['bids'])]

            bids = self.process_bids_for_export(auction['bids'])

            response = api_client.correct_auction(
                bids, item, item_count, winner_bids, iid, self.api_token)

            if response.status_code != 200:
                result.update_rows.append(Row(
                    iid=iid, item=item, item_count=item_count, status='Error', warnings=response.text))
            else:
                result.update_rows.append(Row(iid=iid, item=item, item_count=item_count, status='Corrected',
                                              winner=winners))
                if item in self.active_auctions:
                    self.archive_current_auction(item)

        elif action['action'] == 'FAILED_BID':
            if self.active_auctions:
                line = action['data']
                result.status_messages.append(f'Failed to parse bid: {line}')

        elif action['action'] == 'PREREGISTER-RESET':
            print('got a prereg reset', action)
            self.preregistered_bids[action['item_name']] = []

        elif action['action'] == 'PREREGISTER':
            print('got a prereg', action)
            self.preregistered_bids[action['item_name']].append(action)

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
        self.concluded_auctions[item] = self.active_auctions[item]
        del self.active_auctions[item]

    def process_bids_for_export(self, bids):
        bids = [item for sublist in bids.values() for item in sublist]
        bids = [{'name': bid['player'].replace("'s alt", ''), 'bid': bid['value'], 'tag': bid['status_flag']}
                for bid in bids]
        return bids

    def handle_auction_close(self, action):
        item = action['item_name']
        if item not in self.active_auctions:
            return None

        bids = self.process_bids_for_export(self.active_auctions[item]['bids'])

        iid = self.active_auctions[item]['iid']
        n_items = self.active_auctions[item]['item_count']

        response = api_client.resolve_auction(
            bids, item, n_items, iid, self.api_token)

        if response is None:
            result = Row(iid=iid, item=item, item_count=n_items,
                        status='Concluded', winner="offline", warnings="offline")

            self.archive_current_auction(item)
            return result

        if response.status_code != 200:
            self.active_auctions[item]['warnings'] = [response.text]
            return Row(iid=iid, item=item, item_count=n_items,
                       status='Error', warnings=response.text)

        warnings = response.json()['warnings']

        self.active_auctions[item]['warnings'] = warnings

        result = Row(iid=iid, item=item, item_count=n_items,
                     status='Concluded', winner=response.json()['message'], warnings=', '.join(warnings))

        self.archive_current_auction(item)
        return result

    def handle_flag_close(self, action):
        item = action['item_name']
        if item not in self.active_auctions:
            return None

        players = [c for c in self.active_auctions[item]['bids'].keys()]

        iid = self.active_auctions[item]['iid']
        n_items = self.active_auctions[item]['item_count']

        response = api_client.resolve_flags(
            players, item, n_items, self.api_token)


        if response.status_code != 200:
            return Row(iid=iid, item=item, item_count=n_items,
                       status='Error', warnings=response.text)

        warnings = response.json()['warnings']

        self.active_auctions[item]['warnings'] = warnings

        result = Row(iid=iid, item=item, item_count=n_items,
                     status='Concluded', winner=response.json()['message'], warnings=', '.join(warnings))

        self.archive_current_auction(item)
        return result

    def get_auction_by_iid(self, iid):
        print('searching iid', iid)
        all_auctions_ever = list(
            self.active_auctions.values()) + list(self.concluded_auctions.values())
        print(all_auctions_ever)
        for auction in all_auctions_ever:
            if auction['iid'] == iid:
                return auction
        return None

    def get_most_recent_auction_by_name(self, item_name):
        print('searching by name', item_name)
        if item_name in self.active_auctions:
            return self.active_auctions[item_name]
        if item_name in self.concluded_auctions:
            return self.concluded_auctions[item_name]
        return None


def calculate_bid_tier(bid):
    """ determine the priority for a bid, based on who sent it and how much they bid """
    _char_name, bid = bid
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
    def __init__(self, iid, item, item_count, status, timestamp=None, winner='', warnings=''):
        self.iid = iid
        self.timestamp = timestamp
        self.item = item
        self.status = status
        self.winner = winner
        self.warnings = warnings
        self.item_count = item_count
