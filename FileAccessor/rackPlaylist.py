import pathlib

from .m3u8Playlist import m3u8Reader


class RackReader:

    def __init__(self, rackRoot):
        self.racks = []
        for i in pathlib.Path(rackRoot).resolve().iterdir():
            if i.is_dir():
                self.racks.append(m3u8Reader(i, 'index.*'))

    def get_song(self, rack_idx=0):
        return self.racks[rack_idx].get_song()

    def get_rack_name(self, rack_idx=0):
        return self.racks[rack_idx]