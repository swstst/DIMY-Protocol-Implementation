import math
from bitarray import bitarray
import mmh3
from datetime import datetime


class bloomFilter:
    def __init__(self, n: int, m: int):
        self.filter = bitarray(m).setall(0)  # supposed to be 100kB
        self.hash1 = mmh3.hash
        self.m = m  # Total number of bits, supposed to be 100kB
        self.n = n  # expected amount of elements to be input
        self.k = math.floor((m / n) * math.log(2))
        self.date = datetime.now()

    def __filter_positions__(self, item):
        h = self.hash1(item)
        h1 = h & 0xFFFFFFFFFFFFFFFF
        h2 = (h >> 64) | 1

        positions = []
        for i in range(k):
            pos = (h1 + i * h2) % self.m
            positions.append(pos)

        return positions

    def add_element(self, item) -> bool:
        positions = self.__filter_positions__(item)

        try:
            for pos in positions:
                self.filter[pos] = 1
        except:
            return False
        return True

    def check_membership(self, item) -> bool:
        positions = self.__filter_positions__(item)

        for pos in positions:
            if self.filter[pos] != 1:
                return False

        return True

    def merge_filter(self, BF1):
        assert(BF1.m != self.m or BF1.n != self.n)
        
        self.filter = self.filter | BF1.filter
        
        return

    def change_date(self, new_date):
        self.date = new_date
        return
