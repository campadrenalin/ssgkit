from ssgkit.util import *

class TimeSeries(list):
    def __init__(self, *args, **kwargs):
        list.__init__(self, *args, **kwargs)
        self.sort(key = lambda page: page.date)

    # Analogous to dict.get, with safe defaulting
    def get(self, index, default = None):
        try:
            return self.__getitime__(index)
        except IndexError:
            return default

    def nav_for(self, current_page):
        try:
            i = self.index(current_page)
        except ValueError:
            return None

        return {
            previous : self.get(i-1),
            current  : self.get(i),
            next     : self.get(i+1),
        }
