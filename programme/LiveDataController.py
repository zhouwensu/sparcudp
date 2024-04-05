import time
import tkinter as tk
from tkinter import ttk, filedialog
from scapy import all, interfaces
from scapy.layers.inet import UDP

from programme.SparcConfig import SparcConfig
import threading
import struct
import datetime


class LiveDataController:
    def __init__(self):
        self.udp_parser = None
        self.stop_flg = False
        self.udp_sniff_thread = None
        self.config = None
        self.nic = None
        self.view = LiveDataViewer(self)
        self.is_sniffing = False
        self.nic_list = []
        self.is_config_loaded = False
        self.package_counter = 0

    def log(self, text):
        now = datetime.datetime.now()
        time_now = now.strftime("%Y-%m-%d %H:%M:%S")
        text_var = time_now + "\t" + text
        self.view.log_to_text(text_var)

    def parse_udp(self):

        while not self.stop_flg:
            if self.config.has_data:
                for index in self.config.index_list:
                    if self.config.data_type[index] == 0:
                        self.config.data[index] = struct.unpack('f', self.config.data_bytes[4 * index:4 * index + 4])
                    elif self.config.data_type[index] == 1:
                        self.config.data[index] = struct.unpack('i', self.config.data_bytes[4 * index:4 * index + 4])
                    elif self.config.data_type[index] == 2:
                        self.config.data[index] = struct.unpack('?', self.config.data_bytes[4 * index:4 * index + 4])
            time.sleep(0.20)

    def update_signal_frame(self):
        for name, source, index in zip(self.config.signal_list['name'], self.config.signal_list['source'],
                                       self.config.signal_list['index']):
            self.view.signal_table.insert('', index=tk.END, value=[name, source], iid=index)

    def run(self):
        self.view.mainloop()

    def open_dialog(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Sparc Config", ("*.txt",)), ('all files', '.*')])
        if len(file_path) == 0:
            return
        else:
            self.open_sparc_config(file_path)

    def get_nic(self):
        self.view.nic_table.delete(*self.view.nic_table.get_children())
        self.nic_list = all.get_working_ifaces()
        for nic in self.nic_list:
            nic_str = str(nic)
            ip = all.get_if_addr(nic_str)
            name = all.network_name(nic_str)
            self.view.nic_table.insert('', index=tk.END, value=[name, ip])

    def start_sniff(self):

        item_selected = self.view.nic_table.selection()
        if len(item_selected) != 0:
            if self.config is not None:
                item_text = self.view.nic_table.item(item_selected[0], "value")
                self.nic = interfaces.dev_from_networkname(item_text[0])
                self.udp_sniff_thread = threading.Thread(target=all.sniff, kwargs={"count": 0, "iface": self.nic,
                                                                                   'store': False,
                                                                                   "stop_filter": self.set_rawdata,
                                                                                   "filter": 'src host ''192.168.1.2'
                                                                                   },
                                                         daemon=True)
                self.udp_sniff_thread.start()
                self.view.signal_frame.after(100, self.show_signal)
                self.udp_parser = threading.Thread(target=self.parse_udp, daemon=True)
                self.udp_parser.start()
                self.is_sniffing = True
                self.log("Start Sniffing with "+str(item_text))
            else:
                self.log("No Config Loaded")
        else:
            self.log("No Network Card Selected")

    def set_rawdata(self, p):
        if p.haslayer(UDP):
            data_raw = p[UDP].payload.load
            self.config.data_bytes = data_raw
            self.package_counter = self.package_counter + 1
            if not self.config.has_data:
                self.config.has_data = True
        return self.stop_flg

    def show_signal(self):

        for index, value in self.config.data.items():
            self.view.signal_table.set(index, "value", str(value))
        if not self.stop_flg:
            self.view.signal_frame.after(100, self.show_signal)

    def stop_sniff(self):
        if self.is_sniffing and not self.stop_flg:
            self.stop_flg = True
            self.udp_parser.join()
            self.stop_flg = False
            self.is_sniffing = False
            self.log("Sniffing Stopped" + ", " + str(self.package_counter) + " packages received.")

    def open_sparc_config(self, file_path):
        self.config = SparcConfig(file_path)
        if self.config.is_loaded:
            self.update_signal_frame()
        else:
            self.config = None


class LiveDataViewer(tk.Tk):
    def __init__(self, controller):
        super().__init__()

        self.signal_table = None
        self.bt_refresh = None
        self.bt_start = None
        self.bt_stop = None
        self.nic_table = None
        self.title("SPARC UDP")
        self.iconbitmap("STARS.ico")

        self.geometry('800x600')
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.controller = controller

        # Add Tree Viewer
        self.nic_frame = self.init_nic_frame()
        self.nic_frame.grid(column=0, row=0, sticky=tk.N)
        self.signal_frame = self.init_signal_frame()
        self.signal_frame.grid(column=1, row=0, sticky=tk.NSEW, columnspan=2)

        self._log_label = tk.Label(self, text="Log")

        self._log_label.grid(column=0, row=1, sticky=tk.W, padx=(5, 0))
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._log_text = tk.Text(self, height=5)
        self._log_text.grid(column=0, row=2, columnspan=2, padx=(5, 0), pady=(0, 5), sticky=tk.NSEW)
        text_sb = tk.Scrollbar(self)
        text_sb.grid(column=2, row=2, sticky=tk.NSEW, padx=(0, 5), pady=(0, 5))
        self._log_text.config(yscrollcommand=text_sb.set)
        text_sb.config(command=self._log_text.yview)

    def start_sniff(self):
        self.controller.start_sniff()

    def get_nic(self):
        self.controller.get_nic()

    def stop_sniff(self):
        self.controller.stop_sniff()

    def open_dialog(self):
        self.controller.open_dialog()

    def init_signal_frame(self):
        col = ["name", "source", "value"]
        frame = tk.Frame(self)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        signal_table = ttk.Treeview(master=frame, columns=col, show='headings')
        signal_table.heading('name', text='Name')
        signal_table.heading('source', text='Source')
        signal_table.heading('value', text='Value')
        signal_table.column("name", width=150)
        signal_table.column("source", width=500)
        signal_table.grid(column=0, row=0, sticky=tk.NSEW, padx=(5, 0), pady=(5, 0))
        signal_sb = tk.Scrollbar(frame)
        signal_sb.grid(column=1, row=0, sticky=tk.NSEW, padx=(0, 5), pady=(0, 5))
        signal_table.config(yscrollcommand=signal_sb.set)
        signal_sb.config(command=signal_table.yview)
        bt_open = tk.Button(frame, text='Open', command=self.open_dialog)
        bt_open.grid(column=0, row=1, sticky=tk.NSEW, padx=(5, 0), pady=(5, 0))
        self.signal_table = signal_table

        return frame

    def init_nic_frame(self):
        frame = tk.Frame(self)
        col = ["Name", "IP"]
        self.nic_table = ttk.Treeview(master=frame, columns=col, show='headings')
        self.nic_table.heading("Name", text='Name')
        self.nic_table.heading('IP', text="IP")
        self.nic_table.column("Name", width=200)
        self.nic_table.column("IP", width=100)
        self.nic_table.grid(column=0, row=0, sticky=tk.NSEW, padx=(5, 0), pady=(5, 0), columnspan=3)
        self.bt_refresh = tk.Button(frame, text='Refresh', command=self.get_nic)
        self.bt_refresh.grid(column=0, row=1, sticky=tk.NSEW, padx=(5, 0), pady=(5, 0))
        self.bt_start = tk.Button(frame, text='Start', command=self.start_sniff)
        self.bt_start.grid(column=1, row=1, sticky=tk.NSEW, padx=(5, 0), pady=(5, 0))
        self.bt_stop = tk.Button(frame, text='Stop', command=self.stop_sniff)
        self.bt_stop.grid(column=2, row=1, sticky=tk.NSEW, padx=(5, 0), pady=(5, 0))

        return frame

    def log_to_text(self, text_var):
        self._log_text.insert('end', text_var)
        self._log_text.insert('insert', '\n')
