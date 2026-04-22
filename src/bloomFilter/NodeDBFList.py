import threading
# from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from bloomFilter import bloomFilter as bf
from collections import deque
from datetime import datetime


class NodeDBFList:
    def __init__(self, t: int, n: int, m: int):
        self.t = t
        self.n = n
        self.m = m
        self.DBFs = deque([bf.bloomFilter(self.n, self.m)])
        self.DBF_lock = threading.Lock()

        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self._DBF_add, "interval", seconds=t * 6)
        self.scheduler.start()

    def _DBF_add(self):
        """
        Adds a DBF to the list
        """
        time = datetime.now().strftime("%H:%M:%S.%f")[:-4]
        
        with self.DBF_lock:
            new_DBF = bf.bloomFilter(self.n, self.m)
            self.DBFs.appendleft(new_DBF)

            dbf_nums = len(self.DBFs)
            print('{:<12} [TASK {:<3}] | {:<20} | {:<24} | '.format(time, '7b', 'DBF CREATE', '') + f'total DBFs = {dbf_nums}; DBF id = {new_DBF._get_id()}; set bits = {new_DBF._get_set_bits()}')
            
            if (
                len(self.DBFs) > 6
            ):  # if there's more than 6 remove, this is essentially delete on 36t/60
                dbf_count_before = len(self.DBFs)
                self.DBFs.pop()
                dbf_count_after = len(self.DBFs)
                
                print('{:<12} [TASK {:<3}] | {:<20} | {:<24} |'.format(time, '7b', 'DBF DELETE', '') + f'before = {dbf_count_before} DBFs; after = {dbf_count_after}')

    def curr_DBF(self):
        with self.DBF_lock:

            return self.DBFs[0]

    def get_curr_DBF_queue(self):
        with self.DBF_lock:
            return self.DBFs.copy()

    def stop(self):
        self.scheduler.shutdown()
