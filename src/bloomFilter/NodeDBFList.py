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
        self.scheduler.add_job(_DBF_add, 'interval', seconds=t*6)
        self.scheduler.add_job(_DBF_remove, 'internal', seconds=(t*6)/600)
        self.scheduler.start()
   
    # TODO maybe add a __repr__ in the bloomFilter class? to have beautiful prints

    def _DBF_add(self):
        """
        Adds a DBF to thelist
        """
        with DBF_lock:
            new_DBF = bloomFilter(n, m)
            self.DBFs.appendleft(new_DBF)

    def _DBF_remove(self):
        with DBF_lock:
            self.DBFs.pop()

    def curr_DBF(self):
        with DBF_lock:
            return self.DBFs[0]

    def stop(self):
        self.scheduler.shutdown()
