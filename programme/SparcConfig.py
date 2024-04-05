import pandas as pd
from pandas.errors import ParserError


class SparcConfig:
    def __init__(self, path):
        self.data = {}
        self.data_type = {}
        self.data_bytes = None
        self.has_data = False
        self.blank_lines = []
        self.path = path
        self.signal_list = None
        self.is_loaded = False
        self.open_config()

    def open_config(self):

        with open(self.path, 'r') as f:
            i = 0
            target_str = "@"
            for line in f:

                if target_str in line[0]:
                    self.blank_lines.append(i)
                i = i + 1
        try:
            data = pd.read_csv(self.path, sep='\t', names=["name", "source", "save_flg"],
                               skiprows=self.blank_lines)
        except ParserError:
            pass
        else:
            data_send = data.query('name.str.startswith("SendValue")', engine="python")
            index_list = data_send['name'].str.split(pat="_", n=1).str[1].astype('int')
            data_type_string = data_send['source'].str.split(pat="_", ).str[-1]
            self.signal_list = data_send.copy()
            self.signal_list['index'] = index_list
            for item, item_type in zip(index_list, data_type_string):
                if 'i' in item_type[0]:
                    self.data[item] = 0
                    self.data_type[item] = 1  # integer
                elif 'b' in item_type[0]:
                    self.data[item] = False
                    self.data_type[item] = 2  # Logic
                else:
                    self.data[item] = 0
                    self.data_type[item] = 0  # double

            self.signal_list = self.signal_list.sort_values('index')
            self.is_loaded = True
