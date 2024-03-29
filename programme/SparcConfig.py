import pandas as pd


class SparcConfig:
    def __init__(self, path):
        self.data = {}
        self.data_bytes = None
        self.has_data = False
        self.index_list = None
        self.blank_lines = []
        self.path = path
        self.signal_list = None
        self.open_config()

    def open_config(self):

        with open(self.path, 'r') as f:
            i = 0
            target_str = "@"
            for line in f:

                if target_str in line[0]:
                    self.blank_lines.append(i)
                i = i + 1
        data = pd.read_csv(self.path, sep='\t', names=["name", "source", "save_flg"],
                           skiprows=self.blank_lines)
        data_send = data.query('name.str.startswith("SendValue")', engine="python")

        self.index_list = data_send['name'].str.split(pat="_", n=1).str[1].astype('int')
        self.signal_list = data_send.copy()
        self.signal_list['index'] = self.index_list
        for item in self.index_list:
            self.data[item] = 0

        self.signal_list = self.signal_list.sort_values('index')
