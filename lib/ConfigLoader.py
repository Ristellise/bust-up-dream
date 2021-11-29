import configparser
import pathlib


class Configurartion:

    def __init__(self, config_file):
        if pathlib.Path(config_file).resolve().is_file():
            self.parser = configparser.ConfigParser()
            f = pathlib.Path(config_file).resolve()
            self.parser.read(f)

    @property
    def site(self):
        return dict(self.parser['site'].items())

    @property
    def social(self):
        return dict(self.parser['social'].items())
