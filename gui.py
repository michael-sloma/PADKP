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
import re

import api_client
import parse
import auction
import timestamps
import config


def prompt_api_token(f):
    def with_check_api_token(self, *args, **kwargs):
        if self.api_token is None or not self.api_token_asked:
            self.ask_api_token()
            if self.api_token:
                self.api_token_asked = True
        return f(self, *args, **kwargs)
    return with_check_api_token


class MainPage:
    def __init__(self, master):
        self.master = master
        self.frame = tkinter.Frame(self.master)

        menu_bar = tkinter.Menu(master)
        file_menu = tkinter.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open log file (Ctrl-F)", command=self.open_log_file)
        file_menu.add_command(label="Choose raid dump directory (Ctrl-R)", command=self.choose_raid_dump_dir)
        file_menu.add_command(label="Enter API token (Ctrl-T)", command=self.ask_api_token)
        file_menu.add_command(label="Close (Ctrl-Q)", command=self.confirm_quit)
        menu_bar.add_cascade(label="File", menu=file_menu)

        auction_menu = tkinter.Menu(menu_bar, tearoff=0)
        auction_menu.add_command(label="See auction details (Ctrl-D)", command=self.open_details_window)
        auction_menu.add_command(label="Copy grats message (Ctrl-G)", command=self.copy_grats_message)
        auction_menu.add_command(label="Copy all concluded auctions (Ctrl-Shift-C)", command=self.copy_report)
        auction_menu.add_command(label="Copy concluded auctions from selection (Ctrl-C)", command=self.copy_report_from_selection)
        auction_menu.add_command(label="Charge DKP (Ctrl-B)", command=self.charge_dkp)
        menu_bar.add_cascade(label="Auctions", menu=auction_menu)

        dkp_menu = tkinter.Menu(menu_bar, tearoff=0)
        dkp_menu.add_command(label="Award DKP (Ctrl-W)", command=self.open_award_dkp_window)
        menu_bar.add_cascade(label="Awards", menu=dkp_menu)

        waitlist_menu = tkinter.Menu(menu_bar, tearoff=0)
        waitlist_menu.add_command(label="View waitlist", command=self.open_waitlist_window)
        menu_bar.add_cascade(label="Waitlist", menu=waitlist_menu)

        master.config(menu=menu_bar)

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
        self.tree.grid(row=1, columnspan=4, sticky='nsw')

        self.button = tkinter.Button(master, text="Load log file (Ctrl-F)", command=self.open_log_file)
        self.button.grid(row=2, column=0)

        self.button = tkinter.Button(master, text="Auction details (Ctrl-D)",
                                     command=self.open_details_window)
        self.button.grid(row=2, column=1)

        self.button = tkinter.Button(master, text="Award DKP (Ctrl-W)", command=self.open_award_dkp_window)
        self.button.grid(row=2, column=2)

        self.button = tkinter.Button(master, text="Close (Ctrl-Q)", command=self.confirm_quit)
        self.button.grid(row=2, column=3)

        self.status_window = tkinter.Text(master, height= 10, wrap="word")
        self.status_window.grid(row=4, columnspan=4, sticky='nsew')
        self.scroll = tkinter.Scrollbar(master, orient="vertical", command=self.status_window.yview)
        self.scroll.grid(row=4, column=4, sticky='nse')
        self.status_window.configure(state='normal')
        self.status_window.configure(yscrollcommand=self.scroll.set)
        self.status_window.see("end")
        self.status_window.configure(state='disabled')

        self.raid_dump_pane = ttk.Treeview(master, columns=['time'], selectmode='browse')
        self.raid_dump_pane.grid(row=3, column=0, columnspan=4, sticky='ew')
        self.raid_dump_pane.heading('#0', text='dump')
        self.raid_dump_pane.heading('#1', text='time')
        self.raid_dump_files = set()

        self.master.protocol("WM_DELETE_WINDOW", self.confirm_quit)

        self.thread = None  # thread to asynchronously read data from the log file

        self.queue = queue.Queue()  # holds actions from the log file that update the state of the world
        self.state = auction.AuctionState()

        def auction_context_menu_popup(event):
            self.tree.focus()
            auction_context_menu.post(event.x_root, event.y_root)
        self.tree.bind("<Control-Button-1>", auction_context_menu_popup)
        self.tree.bind("<Button-3>", auction_context_menu_popup)
        auction_context_menu = tkinter.Menu(self.frame, tearoff=0)
        auction_context_menu.add_command(label="Copy grats message (Ctrl-G)", command=self.copy_grats_message)
        auction_context_menu.add_command(label="Copy all concluded auctions (Ctrl-Shift-C)", command=self.copy_report)
        auction_context_menu.add_command(label="Copy concluded auctions from selection (Ctrl-C)", command=self.copy_report_from_selection)
        auction_context_menu.add_command(label="Charge DKP (Ctrl-B)", command=self.charge_dkp)

        def raid_dump_context_menu_popup(event):
            self.raid_dump_pane.focus()
            raid_dump_context_menu.post(event.x_root, event.y_root)
        self.raid_dump_pane.bind("<Control-Button-1>", raid_dump_context_menu_popup)
        self.raid_dump_pane.bind("<Button-3>", raid_dump_context_menu_popup)
        raid_dump_context_menu = tkinter.Menu(self.frame, tearoff=0)
        raid_dump_context_menu.add_command(label="Award DKP (Ctrl-W)", command=self.open_award_dkp_window)
        raid_dump_context_menu.add_command(label="Quick award DKP (Ctrl-Shift-W)", command=self.quick_award_dkp)
        raid_dump_context_menu.add_command(label="Award CASUAL RAID DKP (Ctrl-Shift-M)", command=self.casual_award_dkp)

        # add keyboard shortcuts
        self.master.bind("<Control-f>", lambda _: self.open_log_file())
        self.master.bind("<Control-c>", lambda _: self.copy_report_from_selection())
        self.master.bind("<Control-C>", lambda _: self.copy_report())
        self.master.bind("<Control-g>", lambda _: self.copy_grats_message())
        self.master.bind("<Control-q>", lambda _: self.confirm_quit())
        self.master.bind("<Control-d>", lambda _: self.open_details_window())
        self.master.bind("<Control-b>", lambda _: self.charge_dkp())
        self.master.bind("<Control-w>", lambda _: self.open_award_dkp_window())
        self.master.bind("<Control-Shift-W>", lambda _: self.quick_award_dkp())
        self.master.bind("<Control-Shift-M>", lambda _: self.casual_award_dkp())
        self.master.bind("<Control-t>", lambda _: self.ask_api_token())
        self.master.bind("<Control-r>", lambda _: self.choose_raid_dump_dir())

        self.master.after(1, self.tree.focus_force)

        self.my_name = ''
        self.config = config.load_saved_config()
        self.api_token_asked = False
        self.api_token = self.config.get('api_token', None)
        if 'log_file' in self.config and os.path.exists(self.config['log_file']):
            self.open_log_file(self.config['log_file'])

        if 'dump_path' in self.config and os.path.exists(self.config['dump_path']):
            self.show_raid_dumps()

        self.state.update({'action': 'initialize'}) # trigger the various events that happen "on update"
        print("LOADED")

    def choose_raid_dump_dir(self, path=None):
        self.raid_dump_pane.delete(*self.raid_dump_pane.get_children())
        self.raid_dump_files.clear()
        if path is None:
            path = filedialog.askdirectory()
        if path:
            self.config['dump_path'] = path
        self.show_raid_dumps()

    def show_raid_dumps(self):
        path = self.config.get('dump_path')
        if not os.path.exists(path):
            return
        raid_dump_files = sorted([x for x in os.listdir(path) if re.match(r'^RaidRoster_mangler-\d{8}-\d{6}.txt', x)])
        for rdf in raid_dump_files:
            if rdf not in self.raid_dump_files:
                display_time = timestamps.time_to_gui_display(timestamps.time_from_raid_dump(rdf))
                self.raid_dump_pane.insert('', 0, text=rdf, values=[display_time])
                self.raid_dump_files.add(rdf)
        self.master.after(1000, self.show_raid_dumps)

    def confirm_quit(self):
        confirm = messagebox.askyesno('', 'Really quit?')
        if confirm:
            config.write_config(self.config)
            if self.thread is not None:
                self.thread.stop()
            self.master.destroy()
            sys.exit()

    @prompt_api_token
    def open_award_dkp_window(self):
        filename = self.raid_dump_pane.item(self.raid_dump_pane.selection())['text']
        AwardDkpWindow(self.master, self.api_token, self.config.get('dump_path'), filename, self.state.waitlist)

    def open_waitlist_window(self):
        WaitlistWindow(self.master, self.state)

    @prompt_api_token
    def quick_award_dkp(self):
        dkp_value = 1
        attendance = 1
        notes = ''
        award_type = 'Time'
        selection = self.raid_dump_pane.selection()
        waitlist = list(self.state.waitlist)
        if not selection:
            messagebox.showerror("", "Select a raid dump!")
            return

        short_filename = self.raid_dump_pane.item(self.raid_dump_pane.selection())['text']
        filename = os.path.join(self.config.get('dump_path'), short_filename)
        try:
            result = api_client.award_dkp_from_dump(filename, award_type, dkp_value, attendance, waitlist, notes, self.api_token)
        except Exception:
            messagebox.showerror("", "Action Failed, no DKP awarded")
            raise
        if result.status_code == 201:
            messagebox.showinfo("", "Awarded {} DKP for Time from dump {}".format(dkp_value, short_filename))
        else:
            messagebox.showerror("", "Server error, no DKP awarded\n\n{}".format(result.text))

    @prompt_api_token
    def casual_award_dkp(self):
        dkp_value = 1
        attendance = 1
        notes = ''
        award_type = 'Time'
        selection = self.raid_dump_pane.selection()
        waitlist = list(self.state.waitlist)
        if not selection:
            messagebox.showerror("", "Select a raid dump!")
            return

        short_filename = self.raid_dump_pane.item(self.raid_dump_pane.selection())['text']
        filename = os.path.join(self.config.get('dump_path'), short_filename)
        try:
            result = api_client.award_casual_dkp_from_dump(filename, award_type, dkp_value, attendance, waitlist, notes, self.api_token)
        except Exception:
            messagebox.showerror("", "Action Failed, no DKP awarded")
            raise
        if result.status_code == 201:
            messagebox.showinfo("", "Awarded {} DKP for Time from dump {}".format(dkp_value, short_filename))
        else:
            messagebox.showerror("", "Server error, no DKP awarded\n\n{}".format(result.text))


    def open_details_window(self):
        iid = self.tree.focus()
        auction = self.state.get_auction_by_iid(iid)
        DetailsWindow(self.master, auction)

    def open_log_file(self, filename=None):
        self.clear_data()
        if filename is None:
            filename = filedialog.askopenfilename()
        if filename:
            f = open(filename)
            self.load_data_from_log_file(f)
            self.state.my_name = parse.get_name_from_log_file_path(filename)
            self.config['log_file'] = filename

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

    @prompt_api_token
    def charge_dkp(self):
        selected = self.tree.selection()

        charges = []
        for row_id in selected:
            row = self.tree.item(row_id)
            timestamp = row['text']
            vals = row['values']
            if vals[2] != 'Concluded':
                continue
            if vals[4] == '':
                continue
            item = vals[0]
            winners = [x.strip() for x in vals[3].split(',')]
            costs = [vals[4]] if type(vals[4]) is int else [int(x) for x in vals[4].split(',')]
            time = timestamps.time_from_gui_display(timestamp)

            for winner, cost in zip(winners, costs):
                if winner != 'ROT':
                    charges.append({'character': winner,
                                    'item_name': item,
                                    'value': cost,
                                    'time': timestamps.time_to_django_repr(time),
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
            self.tree.insert('', 0, text=timestamps.time_to_gui_display(new_row.timestamp),
                             values=(new_row.item, new_row.item_count, new_row.status, new_row.winner, new_row.price), iid=new_row.iid)
        for update_row in action_result.update_rows:
            self.tree.item(update_row.iid, values=(update_row.item, update_row.item_count, update_row.status, update_row.winner,
                                                   update_row.price))
            vals = self.tree.item(update_row.iid)['values']
            if update_row.status == 'Concluded':
                message = '/rs Grats {} on {} for {} dkp'.format(vals[3], vals[0], vals[4])
                self.master.clipboard_clear()
                self.master.clipboard_append(message)
            elif update_row.status == 'Tied':
                message = '/rs {} tied, hold a moment'.format(vals[3])
                self.master.clipboard_clear()
                self.master.clipboard_append(message)
                
        for message in action_result.status_messages:
            self.display_status_message(message)

    def ask_api_token(self):
        initial_value = self.api_token if self.api_token is not None else ''
        token = simpledialog.askstring('', 'Please provide an API token (get it from Quaff)',
                                       initialvalue=initial_value)
        self.api_token = token.strip()
        self.config['api_token'] = self.api_token

    def display_status_message(self, msg):
        self.status_window.configure(state='normal')
        self.status_window.insert('1.0', msg +"\n")
        #self.status_window.see("end")
        self.status_window.configure(state='disabled')


class DetailsWindow:
    def __init__(self, master, auction):
        self.auction = auction  # save a reference to the auction dict
        self.window = tkinter.Toplevel(master)
        self.window.title('Auction details: {}'.format(auction['item']))
        columns = ['name', 'bid', 'status_flag', 'alt?', 'comment']
        self.tree = ttk.Treeview(self.window, columns=columns)
        self.tree.heading('#0', text='name')
        self.tree.heading('#1', text='bid')
        self.tree.heading('#2', text='status flag')
        self.tree.heading('#3', text='alt?')
        self.tree.heading('#4', text='comment')
        self.tree.grid()
        self.close_button = tkinter.Button(self.window, text="Close", command=self.window.destroy).grid()
        self.redraw()

    def redraw(self):
        self.tree.delete(*self.tree.get_children())
        for name, bid in sorted(self.auction['bids'].items(), key=lambda x: x[1]['value']):
            status_flag = '' if bid['status_flag'] is None else bid['status_flag']
            is_alt = 'yes' if bid['is_alt'] else 'no'
            values = (bid['value'], status_flag, is_alt, bid['comment'])
            self.tree.insert('', 0, text=name, values=values)
        self.window.after(1000, self.redraw)


class WaitlistWindow:
    def __init__(self, master, state):
        self.state = state  # save a reference to the auction dict
        self.window = tkinter.Toplevel(master)
        self.window.title('Waitlist')
        columns = ['name', 'time']
        self.tree = ttk.Treeview(self.window, columns=columns)
        self.tree.heading('#0', text='name')
        self.tree.heading('#1', text='time')
        self.tree.grid()
        self.close_button = tkinter.Button(self.window, text="Close",
                                           command=self.window.destroy).grid()
        self.redraw()

    def redraw(self):
        self.tree.delete(*self.tree.get_children())
        for name, time in sorted(self.state.waitlist.items(), key=lambda x: x[1]):
            values = (time,)
            self.tree.insert('', 0, text=name, values=values)
        self.window.after(1000, self.redraw)


class AwardDkpWindow:
    def __init__(self, master, api_token, path, filename, waitlist):
        if filename:
            self.filename = os.path.join(path, filename)
        else:
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

        self.waitlist = list(waitlist)

        self.api_token = api_token

    def award_dkp(self):
        try:
            value = int(self.value_entry.get())
        except ValueError:
            messagebox.showerror("", "DKP must be a number")
            return

        if not self.type_choice.get():
            messagebox.showerror("", "Must choose time, boss kill, or other")
            return
        try:
            result = api_client.award_dkp_from_dump(self.filename,
                                                    self.type_choice.get(),
                                                    value,
                                                    self.attendance_var.get(),
                                                    self.waitlist,
                                                    self.notes_entry.get(),
                                                    self.api_token
                                                    )
            print(result)
        except Exception:
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
        self.active_items = set()
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
                    action = parse.handle_line(line, self.active_items)
                    if action is not None:
                        print('enqueued a line', line)
                        self.queue.put(('', action))
                        if action['action'] in ('AUCTION_START', 'SUICIDE_START'):
                            self.active_items.add(action['item_name'])
                        if action['action'] in ['AUCTION_CLOSE', 'AUCTION_CANCEL', 'AUCTION_AWARD', 'SUICIDE_CLOSE']:
                            self.active_items.discard(action['item_name'])
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


