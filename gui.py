import tkinter
from tkinter import ttk
import datetime as dt
import asyncio
import threading
import random
import queue
import uuid


class MainPage:
    def __init__(self, master):
        self.master = master
        self.queue = queue.Queue()
        self.frame = tkinter.Frame(self.master)

        columns = ['item', 'status', 'winner', 'price']
        self.tree = ttk.Treeview(self.master, columns=columns)
        self.tree.heading('#0', text='time')
        self.tree.heading('#1', text='item')
        self.tree.heading('#2', text='status')
        self.tree.heading('#3', text='winner')
        self.tree.heading('#4', text='price')
        self.tree.column('#0', stretch=tkinter.YES)
        self.tree.column('#1', stretch=tkinter.YES)
        self.tree.column('#2', stretch=tkinter.YES)
        self.tree.column('#3', stretch=tkinter.YES)
        self.tree.column('#4', stretch=tkinter.YES)
        self.tree.grid(row=20, columnspan=4, sticky='nsew')
        self.treeview = self.tree

        self.active_auctions = {}
        self.completed_auctions = []

        self.load_data_from_log()

    def load_data_from_log(self):
        """
            Button-Event-Handler starting the asyncio part in a separate
            thread.
        """
        # create Thread object
        max_size = 10
        self.thread = AsyncioThread(self.queue, max_size)

        #  timer to refresh the gui with data from the asyncio thread
        self.master.after(1000, self.refresh_data)  # called only once!

        # start the thread
        self.thread.start()


    def refresh_data(self):
        print('refresh data called')
        while not self.queue.empty():
            key, action = self.queue.get()
            print('read a piece of data:', action)
            self.handle_action(action)
        self.master.after(1000, self.refresh_data)

    def handle_action(self, action):
        if action['action'] == 'AUCTION_START':
            # create a new auction
            item = action['item_name']
            status = 'Active'
            winner = ''
            price = ''
            if item in self.active_auctions:
                return

            iid = uuid.uuid1()
            self.tree.insert('', 'end', text=action['timestamp'].strftime('%a, %d %b %Y %l:%M %p'),
                             values=(item, status, winner, price), iid=iid)
            self.active_auctions[item] = {'item': item, 'iid': iid, 'bids': {}}

        elif action['action'] == 'BID':
            item = action['item_name']
            player = action['player_name']
            value = action['value']
            if item not in self.active_auctions:
                return
            self.active_auctions[item]['bids'][player] = value

        elif action['action'] == 'AUCTION_CLOSE':
            item = action['item_name']
            if item not in self.active_auctions:
                return
            bids = self.active_auctions[item]['bids']
            if bids:
                winner, winning_bid = max(bids.items(), key=lambda x: x[1])
            else:
                winner = 'ROT'
                winning_bid = ''
            # update the UI
            gui_iid = self.active_auctions[item]['iid']
            new_values = (item, 'Concluded', winner, winning_bid)
            self.tree.item(gui_iid, values=new_values)

            self.completed_auctions.append(self.active_auctions[item])
            del self.active_auctions[item]


class AsyncioThread(threading.Thread):
    """ Asynchronously read lines from the log file, interpret them, and stick
    the resulting "action directives" in a queue that's shared between the gui
    and the thread """
    def __init__(self, queue, max_data):
        self.asyncio_loop = asyncio.get_event_loop()
        self.queue = queue
        self.max_data = max_data
        threading.Thread.__init__(self)

    def run(self):
        self.asyncio_loop.run_until_complete(self.do_data())

    async def do_data(self):
        """ Creating and starting 'maxData' asyncio-tasks. """
        while True:
            tasks = [
                self.create_dummy_data(key)
                for key in range(self.max_data)
            ]
            await asyncio.wait(tasks)

    async def create_dummy_data(self, key):
        """ Create data and store it in the queue. """
        sec = random.randint(0, 2)
        start = {'timestamp': dt.datetime.now(),
                 'item_name': 'Singing Steel Breastplate',
                 'action': 'AUCTION_START'}
        bid = {'timestamp': dt.datetime.now(),
               'item_name': 'Singing Steel Breastplate',
               'action': 'BID',
               'player_name': random.choice(['AAA', 'BBB', 'CCC', 'DDD']),
               'value': random.randint(5, 20)
        }
        close = {'timestamp': dt.datetime.now(),
                 'item_name': 'Singing Steel Breastplate',
                 'action': 'AUCTION_CLOSE'}
        await asyncio.sleep(sec)
        print('made some dummy data')
        data = random.choice([start, start, bid, bid, bid, close])
        self.queue.put((key, data))


def main():
    root = tkinter.Tk()
    d = MainPage(root)
    root.mainloop()


if __name__ == '__main__':
    main()

