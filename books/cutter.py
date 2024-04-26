# Inspired by Bruno de Sá's https://github.com/bcunhasa/gerador-cutter

import csv
import unicodedata
from bisect import bisect_left

from django.conf import settings


def normalize(texto):
    return (
        unicodedata.normalize("NFKD", texto)
        .encode("ASCII", "ignore")
        .decode("ASCII")
    )


class CutterSingleton:
    _instance = None
    input_file = settings.BASE_DIR / "books" / "cutter.csv"

    def __init__(self):
        with open(self.input_file, encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # skip header
            self.names, self.codes = zip(*reader)

    def get(self, name):
        index = min(bisect_left(self.names, name), len(self.codes) - 1)

        return self.codes[index]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance


def get(value):
    return CutterSingleton().get(value)
