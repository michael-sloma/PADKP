import tkinter
from tkinter import ttk
from tkinter import filedialog
import asyncio
import threading
import queue

import parse
import auction


class MainPage:
    def __init__(self, master):
        self.master = master
        self.frame = tkinter.Frame(self.master)

        columns = ['item', 'item_count', 'status', 'winner', 'price']
        self.tree = ttk.Treeview(self.master, columns=columns)
        self.tree.heading('#0', text='time')
        self.tree.heading('#1', text='item')
        self.tree.heading('#2', text='count')
        self.tree.heading('#3', text='status')
        self.tree.heading('#4', text='winner')
        self.tree.heading('#5', text='price')
        self.tree.column('#0', stretch=tkinter.YES)
        self.tree.column('#1', stretch=tkinter.YES)
        self.tree.column('#2', stretch=tkinter.YES)
        self.tree.column('#3', stretch=tkinter.YES)
        self.tree.column('#4', stretch=tkinter.YES)
        self.tree.column('#5', stretch=tkinter.YES)
        self.tree.grid(row=1, columnspan=4, sticky='nsew')

        self.button = tkinter.Button(master, text="Load log file", command=self.open_log_file)
        self.button.grid(row=2, column=0)

        self.button = tkinter.Button(master, text="Auction details",
                                     command=self.open_details_window)
        self.button.grid(row=2, column=1)

        self.thread = None  # thread to asynchronously read data from the log file

        self.queue = queue.Queue()  # holds actions from the log file that update the state of the world
        self.state = auction.AuctionState()

    def open_details_window(self):
        iid = self.tree.focus()
        selected_row = self.tree.item(iid)
        item = selected_row['values'][0]
        auction = self.state.get_auction_by_iid(iid)

        window = tkinter.Toplevel(self.master)
        window.title('Auction details: {}'.format(item))
        columns = ['name', 'bid']
        tree = ttk.Treeview(window, columns=columns)
        tree.heading('#0', text='name')
        tree.heading('#1', text='bid')
        for name, bid in sorted(auction['bids'].items(), key=lambda x: x[1]):
            tree.insert('', 0, text=name, values=(bid,))
        tree.grid()
        tkinter.Button(window, text="Close", command=window.destroy).grid()

    def open_log_file(self):
        filename = filedialog.askopenfilename()
        f = open(filename)
        self.load_data_from_log_file(f)

    def load_data_from_log_file(self, file_obj):
        if self.thread is not None:
            self.thread.file_obj.close()
        # create Thread object
        # TODO do we need to kill the old thread if it exists?
        self.thread = AsyncioThread(self.queue, file_obj=file_obj)

        #  timer to refresh the gui with data from the asyncio thread
        self.master.after(1000, self.update_gui)  # called only once!

        # start the thread
        self.thread.start()

    def update_gui(self):
        while not self.queue.empty():
            key, action = self.queue.get()
            print('read a piece of data:', action)
            action_result = self.state.update(action)
            self.show_result(action_result)
        self.master.after(1000, self.update_gui)

    def show_result(self, action_result):
        if action_result is None:
            return
        for new_row in action_result.add_rows:
            self.tree.insert('', 0, text=new_row.timestamp.strftime('%a, %d %b %Y %H:%M'),
                             values=(new_row.item, new_row.item_count, new_row.status, new_row.winner, new_row.price), iid=new_row.iid)
        for update_row in action_result.update_rows:
            self.tree.item(update_row.iid, values=(update_row.item, update_row.item_count, update_row.status, update_row.winner,
                                                   update_row.price))


class AsyncioThread(threading.Thread):
    """ Asynchronously read lines from the log file, interpret them, and stick
    the resulting "action directives" in a queue that's shared between the gui
    and the thread """
    def __init__(self, queue, file_obj=None, max_data=5):
        self.asyncio_loop = asyncio.get_event_loop()
        self.queue = queue
        self.max_data = max_data
        self.file_obj = file_obj
        threading.Thread.__init__(self)

    def run(self):
        self.asyncio_loop.run_until_complete(self.do_data())

    async def do_data(self):
        """ Read new lines from the log file and enqueue any new actions"""
        while True:
            try:
                line = self.file_obj.readline()
            except ValueError:
                break
            if line is None:
                await asyncio.sleep(1)
            else:
                action = parse.handle_line(line)
                if action is not None:
                    print('enqueued a line', line)
                    self.queue.put(('', action))
        print('thread completed')


def main():
    root = tkinter.Tk()
    root.title('Phoenix Ascended Auction Manager')
    d = MainPage(root)
    root.mainloop()


if __name__ == '__main__':
    main()

