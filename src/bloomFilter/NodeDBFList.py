import threading
# from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from bloomFilter import bloomFilter as bf
from collections import deque

class NodeDBFList:
    def __init__(self, t: int, n: int, m: int):
        self.t = t
        self.n = n
        self.m = m
        self.DBFs = deque()
        self.DBF_lock = threading.Lock()

        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self._DBF_add, "interval", seconds=t * 6)
        self.scheduler.start()

    # TODO maybe add a __repr__ in the bloomFilter class? to have beautiful prints

    def _DBF_add(self):
        """
        Adds a DBF to the list
        """
        with self.DBF_lock:
            new_DBF = bf.bloomFilter(self.n, self.m)
            self.DBFs.appendleft(new_DBF)

            if (
                len(self.DBFs) > 6
            ):  # if there's more than 6 remove, this is essentially delete on 36t/60
                self.DBFs.pop()

    def curr_DBF(self):
        with self.DBF_lock:
            return self.DBFs[0]

    def get_curr_DBF_queue(self):
        with self.DBF_lock:
            return self.DBFs

    def stop(self):
        self.scheduler.shutdown()
