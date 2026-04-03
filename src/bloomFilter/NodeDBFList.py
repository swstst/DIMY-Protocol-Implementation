import threading
from apscheduler.schedulers.blocking import BlockingScheduler
from bloomFilter import bloomFilter 
from collections import deque

class NodeDBFList():
    def __init__(self, t: int, n: int, m: int):
        self.t = t
        self.n = n
        self.m = m
        self.DBFs = deque()
        self.DBF_lock = threading.lock()

        self.scheduler = BlockingScheduler()
        self.scheduler.add_job(self._DBF_add, 'interval', seconds=t*6)
        self.scheduler.start()
   
    # TODO maybe add a __repr__ in the bloomFilter class? to have beautiful prints

    def _DBF_add(self):
        """
        Adds a DBF to thelist
        """
        with self.DBF_lock:
            new_DBF = bloomFilter(self.n, self.m)
            self.DBFs.appendleft(new_DBF)

            if len(self.DBFs) > 6: # if there's more than 6 remove, this is essentially delete on 36t/60
                self.DBFs.pop()

    def curr_DBF(self):
        with self.DBF_lock:
            return self.DBFs[0]

    def stop(self):
        self.scheduler.shutdown()
