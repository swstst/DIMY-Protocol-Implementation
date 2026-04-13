import sys
import threading
import socket
import pickle
import random
import time
import logging
from queue import *
from Crypto.Hash import SHA256
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

from ephID import ID

from bloomFilter.NodeDBFList import NodeDBFList
from bloomFilter.bloomFilter import bloomFilter

from msgFormatter import msgFormatter as MessageFormatter


# Keep logs in a queue.

class Client:
    def __init__(self, t: int, k: int, n: int, p: int):

        self.CLIENT_ID = random.randrange(1000, 10_000)

        self.UDP_RECV_PORT = 5000
        self.UDP_SEND_PORT = 5000

        # UDP socket for receiving shares
        self.UDP_RECV_SOCK = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # UDP socket for broadcasting shares
        self.UDP_SEND_SOCK = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        self.t = t
        self.k = k
        self.n = n
        self.p = int(p)

        self.DBF_list = NodeDBFList(t, n, m=800_000)

        self.stop_event = threading.Event()
         
        self.curr_EphID = None
        self.curr_secret = None
        self.curr_HashID = None

        self.hashID_queue = Queue(maxsize=2)
        self.shares_queue = Queue()

        # shares received within 't'-seconds
        self.recv_shares = Queue()
        self.share_ids_counter = dict()

        self.EphIDs = Queue()

        self.has_COVID = False

        self.log_msg = MessageFormatter.MessageFormatter(origin=f'client_{self.CLIENT_ID}')

    def gen_EphID_shares(self) -> None:
        """
        The thread process to generate EphIDs every t (EphID_time)
        """
        while not self.stop_event.is_set():
            start_timer = time.perf_counter()
        
            # generate new EphID
            self.curr_EphID, self.curr_secret = ID.gen_EphID(self.t)
            self.log_msg.log_local(action="CREATED", data={'type': 'EphID', 'data': f"{str(self.curr_EphID)[:5]}.."})

            # generate new HashID based on EphID
            hash_EphID = bytearray(
                SHA256.new(data=self.curr_EphID.to_bytes(32, byteorder="big")).digest()
            )[0:3]

            self.hashID_queue.put(hash_EphID)
            self.log_msg.log_local(action="CREATED", data={'type': 'HashID', 'data': f"{hash_EphID[:].hex()}.."})

            # split new EphID into n shares
            new_shares = ID.gen_shares(new_EphID=self.curr_EphID, k=self.k, n=self.n)
                
            fshares = ', '.join(f"{share[:2].hex()}.." for share in new_shares[:self.n])
            self.log_msg.log_local(action="CREATED", data={'type': 'Secret Shares', 'data': f"[{fshares}]"})

            # store shares in broadcast queue
            self.shares_queue.put(new_shares)

            delay = time.perf_counter() - start_timer 
            
            time.sleep(self.t - delay)


    def broadcast_shares(self) -> None:
        """
        Distribute the secret shares every 3 seconds
        """
        while not self.stop_event.is_set():
            
            shares = self.shares_queue.get(block=True)
            self.curr_HashID = self.hashID_queue.get(block=True)

            for share in shares:
                start_timer = time.perf_counter()
                
                msg = self.curr_HashID + share
                
                # broadcast share over UDP
                self.UDP_SEND_SOCK.sendto(msg, ('255.255.255.255', self.UDP_SEND_PORT))
                
                self.log_msg.send(receiver="client", action="SEND SHARE", data={'hash id': f"{msg[:3].hex()}..", 'share': f"{msg[3:6].hex()}.."})

                delay = time.perf_counter() - start_timer 

                time.sleep(3 - delay)


    def udp_receiver(self) -> None:
        """
        Listens for broadcasted shares continuously 
        """        
        # Listening on UDP port for message drops and broadcast shares
        while not self.stop_event.is_set():

            # should be receiving 32 + 3 bytes at a time
            data, addr = self.UDP_RECV_SOCK.recvfrom(35)

            if not data:
                continue

            # process data:
            d = bytearray(data)
            key, ephID = d[0:3], d[3:]

            # if message is own share, drop it
            if key == self.curr_HashID:
                continue

            # if probability < defined probability, drop message
            # p = random.randrange(0, 100)

            # if p < self.p:
            #     continue

            self.log_msg.recv(sender=f"client_{key.hex()}", data={'hash id': f"{key.hex()}", 'share': f"{ephID[:3].hex()}.."})
            
            # store data
            self.recv_shares.put([key, ephID])

            # keep track of shares received that belong to the same ephID
            self.update_recv_share_ids_count(key)



    def update_recv_share_ids_count(self, key) -> None:
        """
        Count number of shares recevied from the same EphID share
        """

        # blocking 
        if len(self.share_ids_counter) == 0 or key.hex() not in self.share_ids_counter.keys():
            self.share_ids_counter[key.hex()] = 1

        else:
            self.share_ids_counter[key.hex()] += 1


    def clear_share_ids_count_cache(self) -> None:
        """
        Free up space of same EphID share counter every t-seconds
        """
        self.share_ids_counter.clear()
        

    # def check_for_k_shares(self) -> tuple:
    #     # blocking
    #     while not self.stop_event.is_set():
            
    #         time.sleep(self.t)
            
    #         for k in self.share_ids_counter.keys():
    #             if self.share_ids_counter[k] == self.k:
    #                 self.clear_share_ids_count_cache()
    #                 return True, k
                
    
    def reconstruct_shares(self):
        """
        Check if k-shares have been received for any clients given t seconds.
        """
        delay = self.t
        elapsed_time = 0

        while not self.stop_event.is_set():
            
            # attempt to reconstruct received shares every t-interval
            time.sleep(delay - elapsed_time)

            # make a copy of the received shares queue
            recv_shares_copy = self.recv_shares

            # get length of received shares copy to prevent race conditions
            num_recv_shares = recv_shares_copy.qsize()

            # temporary hash map to store and process received shares
            shares = dict()

            # remove processed shares from recv_shares queue
            for _ in range(num_recv_shares):

                data = self.recv_shares.get()

                k, v = bytes(data[0]), data[1]

                if k not in shares.keys():
                    shares[k] = [v]

                    continue

                shares[k].append(v)

            for hash_id, ephID_shares in shares.items():

                # do nothing if not enough shares received
                if len(ephID_shares) < self.k:
                    continue

                # otherwise, reconstruct the shares
                temp_ephID = ID.combine_shares(ephID_shares)

                ephID_hash = SHA256.new(temp_ephID).digest()[0 : len(hash_id)]

                # verify reconstructed shares
                if ephID_hash != hash_id:
                    continue

                valid_ephID = temp_ephID

                # successful reconstruction of shares can proceed to generate EncID. 
                self.log_msg.log_local(action="CREATED", data={'type': 'reconstructed EphID', 'data': f"{valid_ephID[:4].hex()}.."})
                            
                self.EphIDs.put(valid_ephID)

                encID = ID.ECDH(valid_ephID, self.curr_secret)
                self.log_msg.log_local(action="CREATED", data={'type': 'EncID', 'data': f"{str(encID)[:4]}.."})

                # put encID into bloom filter
                curr_filter = self.DBF_list.curr_DBF()
                curr_filter.add_element(encID)

                self.log_msg.log_local(action="UPDATED", data={'msg': 'Added EncID to DBF', 'data': len(self.DBF_list.curr_DBF())})


    def combine_DBFs(self):
        """
        Combines all available DBFs into a single bloom filter.

        """
        aggr_bloomFilter = bloomFilter(n=6, m=800_000)
        curr_DBF_list = self.DBF_list.get_curr_DBF_queue()

        oldest_date = datetime.now()
        for dbf in curr_DBF_list:
            aggr_bloomFilter.merge_filter(dbf)
            oldest_date = min(oldest_date, dbf.date)

        return aggr_bloomFilter, oldest_date

    def make_cbf(self) -> None:
        CBF, _ = self.combine_DBFs()

        self.log_msg.log_local(action="CREATED", data={'type': 'CBF', 'data': CBF})

    def make_qbf(self):
        combined_BF, oldest_date = self.combine_DBFs()
        combined_BF.change_date(oldest_date)
        qbf = combined_BF
        
        self.log_msg.log_local(action="CREATED", data={"type": "QBF", "data": (oldest_date.strftime("%H:%M:%S.%f")[:-3], len(qbf.filter))})

        return qbf

    def send(self, data, bf_type:str):
        # set up new TCP connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', 55000))

        self.log_msg.log_local(action="INIT", data={'TCP port': self.UDP_RECV_PORT, 'TCP port': '55000'})

        bf = pickle.dumps((bf_type, data))

        sock.sendall(bf)

        self.log_msg.send(receiver="server", action=f"SEND {bf_type}", data={bf_type: data})

        resp = sock.recv(1024).decode()

        sock.shutdown(1)

        sock.close()

        self.log_msg.recv(sender="server", data={'msg': resp})

        return resp

    def upload_bf_to_server(self):
        
        # in seconds (t * 6 * 6)
        dt = self.t * 2
        # dt = self.t * 6 * 6

        # sent qbf counter
        p = 0
        
        while not self.stop_event.is_set():
            
            time.sleep(dt)

            if p == 10 and self.has_COVID:
                cbf = self.make_cbf()
                
                resp = self.send(data=cbf, bf_type='CBF')

            # get new QBF
            qbf = self.make_qbf()
             
            resp = self.send(data=qbf, bf_type='QBF')

            p += 1

            if resp == 'MATCH FOUND':
                self.log_msg.recv(sender="server", data={'msg': f"{resp} - is a close contact."})
                # bonus: use some probability var to change self.has_COVID to true after receiving match.
                

    def run(self):
        """
        Main process

        udp_recv_thread will start as soon as client has been instantiated
        gen_EphID_shares_thread will run on it's own the whole time,
        broadcast_thread will start once self.shares_queue is not empty

        """

        # enable address reuse for receiving socket
        self.UDP_RECV_SOCK.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # set up broadcasting socket
        self.UDP_SEND_SOCK.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        try:
            self.UDP_RECV_SOCK.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError:
            pass

        # start listening on receiving UDP port
        self.UDP_RECV_SOCK.bind(('', self.UDP_RECV_PORT))
        
        self.log_msg.log_local(action="INIT", data={'status': 'listening', 'port': self.UDP_SEND_PORT })
        
        # init threads
        udp_recv_thread = threading.Thread(target=self.udp_receiver, daemon=False)
        broadcast_shares_thread = threading.Thread(target=self.broadcast_shares, daemon=False)
        gen_EphID_thread = threading.Thread(target=self.gen_EphID_shares, daemon=False)
        reconstruct_ephID_thread = threading.Thread(target=self.reconstruct_shares, daemon=False)
        upload_to_server_thread = threading.Thread(target=self.upload_bf_to_server, daemon=False)
        print_log_thread = threading.Thread(target=self.log_msg.print_logs, daemon=False)

        # start threads
        udp_recv_thread.start()
        broadcast_shares_thread.start()
        gen_EphID_thread.start()
        reconstruct_ephID_thread.start()
        upload_to_server_thread.start()
        print_log_thread.start()

    def stop_all_processes(self):
        self.stop_event.set()


if __name__ == "__main__":
    logger = logging.getLogger(__name__)

    # # comment out for now
    # # graceful invalid input handling
    # t, k, n, p = sys.argv[1:5]

    # assert (int(t) in {15,18,21,24,27,30}), logger.error(msg="Invalid value 't' must be one of {15, 18, 21, 24, 27, 30}")
    # assert (int(k) >= 3 and int(k) <= int(n)), logger.error(msg="Invalid value 'k' must be >= 3 and < 'n'")
    # assert (int(n) >= 5), logger.error(msg="Invalid value 'n' must be >= 5")
    # assert (int(p) in {30, 40, 50, 60, 70}), logger.error(msg="Invalid value 'p' must be one of {30, 40, 50, 60, 70}")
    
    print('starting client')
    client = Client(t=15, k=3, n=5, p=30)

    print('created client')
    print()
    print()

    client.run()

    threading.Event().wait()
    