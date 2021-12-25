import pathlib
import random

from .m3u8Playlist import m3u8Reader


class RackReader:

    def __init__(self, rackRoot):
        self.racks = []
        self.rack_lists = []
        for i in pathlib.Path(rackRoot).resolve().iterdir():
            if i.is_dir():
                self.racks.append(m3u8Reader(i, 'index.*'))

    def get_song(self, rack_idx=0):
        if rack_idx == -1:
            print(self.racks)
            if len(self.rack_lists) == 0:
                for i in self.racks:
                    self.rack_lists.append((i.get_list(),i))
                random.shuffle(self.rack_lists)
            if len(self.rack_lists[0][0]) == 0:
                for _ in self.racks:
                    self.rack_lists.pop(0)
            sl = self.rack_lists[0][0].pop(0)
            sl = pathlib.Path(self.rack_lists[0][1].path[0]) / sl
            return sl, self.rack_lists[0][1].get_cover(sl)
        else:
            return self.racks[rack_idx].get_song()

    def get_rack_name(self, rack_idx=0):
        return self.racks[rack_idx]