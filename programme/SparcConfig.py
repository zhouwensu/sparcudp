import pandas as pd


class SparcConfig:
    def __init__(self, path):
        self.blank_lines = []
        self.path = path
        self.open_config()

    def open_config(self):

        with open(self.path, 'r') as f:
            i = 0
            target_str = "@"
            for line in f:

                if target_str in line[0]:
                    self.blank_lines.append(i)
                i = i+1
            print(self.blank_lines)


