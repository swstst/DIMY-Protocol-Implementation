import gen_ID
import threading

class client:
    def __init__(self, t, k, n):
        assert(t in {15,18,21,24,27,30})
        assert(k >= 3)
        assert(n >= 5)

        self.time_cycle = t     
        self.k = k
        self.n = n
