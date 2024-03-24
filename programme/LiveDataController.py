import tkinter as tk
from tkinter import ttk, filedialog
from scapy import all, interfaces
from programme.SparcConfig import SparcConfig


class LiveDataController:
    def __init__(self):
        self.config = None
        self.nic = None
        self.view = LiveDataViewer(self)
        self.nic_list = []

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
            item_text = self.view.nic_table.item(item_selected[0], "value")
            print(item_text)
            self.nic = interfaces.dev_from_networkname(item_text[0])
            all.sniff(count=100, iface=self.nic, prn=self.show)

    def show(self, p):
        print(p)

    def stop_sniff(self):
        pass

    def open_sparc_config(self, file_path):
        self.config = SparcConfig(file_path)


class LiveDataViewer(tk.Tk):
    def __init__(self, controller):
        super().__init__()

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
        col = ["Name", "Value"]
        frame = tk.Frame(self)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        signal_table = ttk.Treeview(master=frame, columns=col, show='headings')
        signal_table.heading('Name', text='Name')
        signal_table.heading('Value', text='Value')
        signal_table.grid(column=0, row=0, sticky=tk.NSEW, padx=(5, 0), pady=(5, 0))
        signal_sb = tk.Scrollbar(frame)
        signal_sb.grid(column=1, row=0, sticky=tk.NSEW, padx=(0, 5), pady=(0, 5))
        signal_table.config(yscrollcommand=signal_sb.set)
        signal_sb.config(command=signal_table.yview)
        bt_open = tk.Button(frame, text='Open', command=self.open_dialog)
        bt_open.grid(column=0, row=1, sticky=tk.NSEW, padx=(5, 0), pady=(5, 0))

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