import pathlib
import random
import zlib

from .fooPlaylist import PlaylistReader


class m3u8Reader(PlaylistReader):

    def __init__(self, m3u8_root, filename_glob, retry_attempts=5):
        super().__init__()
        self.queued = []
        self.m3u8 = None
        self.fs = None
        self.check = None
        self.songs = []
        self.retry = retry_attempts
        self.path = (m3u8_root, filename_glob)

    def read_pl(self):
        m3u8_n = list(pathlib.Path(self.path[0]).glob(self.path[1]))[-1]
        fs_n = m3u8_n.read_text(encoding="utf-8 sig").strip()
        n_chk = (zlib.crc32(fs_n.encode()) & 0xffffffff)
        if self.check != n_chk:
            self.m3u8 = m3u8_n
            self.fs = fs_n
            self.check = n_chk
            self.songs = fs_n.split("\n")
            t_songs = []
            for i in self.songs:
                i = i.strip()
                if i.startswith('#'):
                    pass
                else:
                    t_songs.append(i)
            self.songs = t_songs

    def get_song(self):
        self.read_pl()
        err = 0
        while True:
            if err == self.retry:
                raise FileNotFoundError(f"Attempted {self.retry} times for a valid song. Playlist broken.")
            if len(self.queued) <= 0:
                self.queued = self.songs.copy()
                random.shuffle(self.queued)
            song = pathlib.Path(self.path[0]).joinpath(self.queued.pop(0))
            if not song.resolve().exists():
                err += 1
            else:
                break
        cover = list(pathlib.Path(song).resolve().parent.glob("cover.*"))
        if len(cover) == 0:
            cover = list(pathlib.Path(song).resolve().parent.glob("Cover.*"))
            if len(cover) == 0:
                return song, self.fallback_cover()
        return song, cover

    def fallback_cover(self):
        for item in pathlib.Path(self.path[0]).iterdir():
            if item.suffix == '.jpg' or item.suffix == '.jpeg':
                if item.name.lower().startswith("cover"):
                    return str(item.resolve())
        return None
