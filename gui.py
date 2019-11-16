import tkinter
from tkinter import ttk
from tkinter import filedialog
from tkinter import simpledialog
from tkinter import messagebox
import asyncio
import threading
import queue
import sys
import traceback
import datetime as dt
import os

import api_client
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

        self.button = tkinter.Button(master, text="Load log file (Ctrl-F)", command=self.open_log_file)
        self.button.grid(row=2, column=0)

        self.button = tkinter.Button(master, text="Auction details (Ctrl-D)",
                                     command=self.open_details_window)
        self.button.grid(row=2, column=1)

        self.button = tkinter.Button(master, text="Award DKP (Ctrl-W)", command=self.open_award_dkp_window)
        self.button.grid(row=2, column=2)

        self.button = tkinter.Button(master, text="Close (Ctrl-Q)", command=self.confirm_quit)
        self.button.grid(row=2, column=3)

        self.master.protocol("WM_DELETE_WINDOW", self.confirm_quit)

        self.thread = None  # thread to asynchronously read data from the log file

        self.queue = queue.Queue()  # holds actions from the log file that update the state of the world
        self.state = auction.AuctionState()

        self.api_token = None

        menu = tkinter.Menu(self.frame, tearoff=0)
        menu.add_command(label="Copy grats message (Ctrl-G)", command=self.copy_grats_message)
        menu.add_command(label="Copy all concluded auctions (Ctrl-Shift-C)", command=self.copy_report)
        menu.add_command(label="Copy concluded auctions from selection (Ctrl-C)", command=self.copy_report_from_selection)
        menu.add_command(label="Charge DKP (Ctrl-B)", command=self.charge_dkp)

        def popup(event):
            print("popup was called")
            self.tree.focus()
            menu.post(event.x_root, event.y_root)

        # attach popup to canvas
        self.tree.bind("<Control-Button-1>", popup)
        self.tree.bind("<Button-3>", popup)

        # add keyboard shortcuts
        self.tree.bind("<Control-f>", lambda _: self.open_log_file())
        self.tree.bind("<Control-c>", lambda _: self.copy_report_from_selection())
        self.tree.bind("<Control-C>", lambda _: self.copy_report())
        self.tree.bind("<Control-g>", lambda _: self.copy_grats_message())
        self.tree.bind("<Control-q>", lambda _: self.confirm_quit())
        self.tree.bind("<Control-d>", lambda _: self.open_details_window())
        self.tree.bind("<Control-b>", lambda _: self.charge_dkp())
        self.tree.bind("<Control-w>", lambda _: self.open_award_dkp_window())

        self.master.after(1, self.tree.focus_force)
        print("LOADED")

    def confirm_quit(self):
        confirm = messagebox.askyesno('', 'Really quit?')
        if confirm:
            if self.thread is not None:
                self.thread.stop()
            self.master.destroy()
            sys.exit()

    def open_award_dkp_window(self):
        if self.api_token is None:
            self.ask_api_token()
        AwardDkpWindow(self.master, self.api_token)

    def open_details_window(self):
        iid = self.tree.focus()
        auction = self.state.get_auction_by_iid(iid)
        DetailsWindow(self.master, auction)

    def open_log_file(self):
        self.clear_data()
        filename = filedialog.askopenfilename()
        if filename:
            f = open(filename)
            self.load_data_from_log_file(f)

    def copy_grats_message(self):
        iid = self.tree.focus()
        vals = self.tree.item(iid)['values']
        try:
            message = '/rs Grats {} on {} for {} dkp'.format(vals[3], vals[0], vals[4])
            self.master.clipboard_clear()
            self.master.clipboard_append(message)
            print(message)
        except IndexError:
            print("can't copy grats message, nothing selected")
            return

    def copy_report(self):
        report = self._text_report(self.tree.get_children())
        self.master.clipboard_clear()
        self.master.clipboard_append(report)

    def copy_report_from_selection(self):
        report = self._text_report(self.tree.selection())
        self.master.clipboard_clear()
        self.master.clipboard_append(report)

    def charge_dkp(self):
        if self.api_token is None:
            self.ask_api_token()
        selected = self.tree.selection()

        charges = []
        for row_id in selected:
            row = self.tree.item(row_id)
            timestamp = row['text']
            vals = row['values']
            if vals[2] != 'Concluded':
                continue
            item = vals[0]
            winners = [x.strip() for x in vals[3].split(',')]
            costs = [vals[4]] if type(vals[4]) is int else [int(x) for x in vals[4].split(',')]
            time = dt.datetime.strptime(timestamp, '%a, %d %b %Y %H:%M').strftime('%Y-%m-%dT%H:%M:%SZ')

            for winner, cost in zip(winners, costs):
                if winner != 'ROT':
                    charges.append({'character': winner,
                                    'item_name': item,
                                    'value': cost,
                                    'time': time,
                                    'notes': '',
                                    'token': self.api_token})
        charges_human_readable = ['{} to {} for {}'.format(x['item_name'], x['character'], x['value'])
                                  for x in charges]
        confirm = messagebox.askyesno('', '\n'.join(charges_human_readable) + "\n\nCharge DKP?")
        if confirm:
            for charge, msg in zip(charges, charges_human_readable):
                result = api_client.charge_dkp(**charge)
                if result.status_code == 201:
                    messagebox.showinfo("", "Charged {}".format(msg))
                else:
                    err_msg = '{} could not be charged to {}\nSend Quaff a bug report\n\n{}'\
                        .format(charge['item_name'], charge['character'], result.text)
                    messagebox.showerror('Failed to charge', err_msg)
                print('charge completed with status code {}'.format(result.status_code))

    def write_report(self):
        filename = filedialog.asksaveasfilename()
        f = open(filename, 'w')
        f.write(self._text_report(self.tree.get_children()))
        f.close()

    def _text_report(self, auction_iids):
        report = []
        for row_id in auction_iids:
            row = self.tree.item(row_id)
            timestamp = row['text']
            vals = row['values']
            print(vals, vals[2])
            if vals[2] == 'Concluded':
                item = vals[0]
                winner = vals[3]
                cost = vals[4]
                report_line = '{}: {} to {} for {}'.format(timestamp, item, winner, cost) if winner != 'ROT' \
                              else '{}: {} rotted'.format(timestamp, item)
                report.append(report_line)
        print("text report: ", report)
        return '\n'.join(report)

    def clear_data(self):
        if self.thread is not None:
            self.thread.stop()
        self.tree.delete(*self.tree.get_children())
        self.queue = queue.Queue()
        self.state = auction.AuctionState()

    def load_data_from_log_file(self, file_obj):
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

    def ask_api_token(self):
        token = simpledialog.askstring('', 'Please provide an API token (get it from Quaff)')
        self.api_token = token.strip()


class DetailsWindow:
    def __init__(self, master, auction):
        self.auction = auction  # save a reference to the auction dict
        self.window = tkinter.Toplevel(master)
        self.window.title('Auction details: {}'.format(auction['item']))
        columns = ['name', 'bid', 'alt?', 'comment']
        self.tree = ttk.Treeview(self.window, columns=columns)
        self.tree.heading('#0', text='name')
        self.tree.heading('#1', text='bid')
        self.tree.heading('#2', text='alt?')
        self.tree.heading('#3', text='comment')
        self.tree.grid()
        self.close_button = tkinter.Button(self.window, text="Close", command=self.window.destroy).grid()
        self.redraw()

    def redraw(self):
        self.tree.delete(*self.tree.get_children())
        for name, bid in sorted(self.auction['bids'].items(), key=lambda x: x[1]['value']):
            values = (bid['value'], 'yes' if bid['alt'] else 'no', bid['comment'])
            self.tree.insert('', 0, text=name, values=values)
        self.window.after(1000, self.redraw)


class AwardDkpWindow:
    def __init__(self, master, api_token):
        self.filename = filedialog.askopenfilename()
        short_filename = os.path.split(self.filename)[-1]

        self.window = tkinter.Toplevel(master)
        self.window.title('Award DKP')

        self.file_label = tkinter.Label(self.window, text=short_filename)
        self.file_label.grid(row=0, column=0, columnspan=2, sticky=tkinter.E+tkinter.W)

        self.type_choice = tkinter.StringVar(self.window)
        choices = ['Time', "Boss Kill", "Other"]
        self.type_choice_menu = tkinter.OptionMenu(self.window, self.type_choice, *choices)
        self.type_choice_menu.grid(row=1, column=1, columnspan=2, sticky=tkinter.E+tkinter.W)

        self.value_label = tkinter.Label(self.window, text="DKP")
        self.value_entry = tkinter.Entry(self.window)
        self.value_label.grid(row=2, column=0, sticky=tkinter.W)
        self.value_entry.grid(row=2, column=1, sticky=tkinter.W)

        self.attendance_var = tkinter.IntVar(value=1)
        self.attendance_label = tkinter.Label(self.window, text="Counts for attendance?")
        self.attendance_entry = tkinter.Checkbutton(self.window, variable=self.attendance_var)
        self.attendance_label.grid(row=3, column=0, sticky=tkinter.W)
        self.attendance_entry.grid(row=3, column=1, sticky=tkinter.W)

        self.notes_label = tkinter.Label(self.window, text="Notes")
        self.notes_entry = tkinter.Entry(self.window)
        self.notes_label.grid(row=4, column=0, sticky=tkinter.W)
        self.notes_entry.grid(row=4, column=1, sticky=tkinter.W)

        self.award_button = tkinter.Button(self.window, text="Award DKP", command=self.award_dkp)
        self.close_button = tkinter.Button(self.window, text="Cancel", command=self.window.destroy)
        self.award_button.grid(row=5, column=0)
        self.close_button.grid(row=6, column=0)

        self.api_token = api_token

    def award_dkp(self):
        try:
            value = int(self.value_entry.get())
        except ValueError:
            messagebox.showerror("", "DKP must be a number")
            return

        try:
            type = {'Time': 'TA',
                    'Boss Kill': 'BK',
                    'Other': '?'}[self.type_choice.get()]
        except KeyError:
            messagebox.showerror("", "Must choose time, boss kill, or other")
            return

        try:
            result = api_client.award_dkp_from_dump(self.filename,
                                                    type,
                                                    value,
                                                    self.attendance_var.get(),
                                                    self.notes_entry.get(),
                                                    self.api_token
                                                    )
        except ValueError:
            messagebox.showerror("", "Action Failed, no DKP awarded")
            raise
        if result.status_code == 201:
            messagebox.showinfo("", "DKP awarded")
            self.window.destroy()
        else:
            messagebox.showerror("", "Server error, no DKP awarded\n\n{}".format(result.text))


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

    def stop(self):
        self.file_obj.close()

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
                try:
                    action = parse.handle_line(line)
                    if action is not None:
                        print('enqueued a line', line)
                        self.queue.put(('', action))
                except Exception:
                    print('PARSE ERROR')
                    print('LINE', line)
                    print(traceback.format_exc())
                    print('')
        print('thread completed')


def main():
    root = tkinter.Tk()
    root.title('Phoenix Ascended Auction Manager')
    d = MainPage(root)
    root.mainloop()


if __name__ == '__main__':
    main()

