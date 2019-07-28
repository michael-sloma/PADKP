import tkinter
from tkinter import ttk
import datetime as dt
import asyncio
import threading
import random
import queue


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

        test_data = [{'start_time': dt.datetime.now(),
                      'winner': 'Playerone',
                     'item': 'Singing Steel Breastplate',
                      'price': 20,
                      'status': 'Concluded'},
                     {'start_time': dt.datetime.now(),
                      'winner': None,
                     'item': 'Cloak of Flames',
                      'price': None,
                      'status': 'Active'}
        ]
        for _ in range(5):
            for p in test_data:
                self.tree.insert('', 'end', text=p['start_time'].strftime('%a, %d %b %Y %l:%M %p'),
                                 values=(p['item'], p['status'], p['winner'], p['price']))
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
            key, data = self.queue.get()
            print('read a piece of data:', data)
            self.tree.insert('', 'end', text=data['start_time'].strftime('%a, %d %b %Y %l:%M %p'),
                             values=(data['item'], data['status'], data['winner'], data['price']))
        self.master.after(1000, self.refresh_data)  # called only once!


class AsyncioThread(threading.Thread):
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
        sec = random.randint(1, 10)
        data = {'start_time': dt.datetime.now(),
                 'winner': 'Playerone',
                 'item': 'Singing Steel Breastplate',
                 'price': random.randint(1, 50),
                 'status': 'Concluded'}
        await asyncio.sleep(sec)
        print('made some dummy data')

        self.queue.put((key, data))


def main():
    root = tkinter.Tk()
    d = MainPage(root)
    root.mainloop()


if __name__ == '__main__':
    main()

