class PlaylistReader:

    def read_pl(self):
        raise NotImplementedError()

    def get_song(self):
        raise NotImplementedError()

    def fallback_cover(self):
        raise NotImplementedError()