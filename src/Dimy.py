import sys
import threading
import socket
import pickle
import random
import time
import logging
from queue import *
from Crypto.Hash import SHA256
from datetime import datetime

from ephID import ID
from bloomFilter.NodeDBFList import NodeDBFList
from bloomFilter.bloomFilter import bloomFilter
from msgFormatter import msgFormatter as MessageFormatter


class Client:
    def __init__(self, t: int, k: int, n: int, p: int, has_covid: bool):

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
        self.stop_qbf_upload = threading.Event()
         
        self.curr_EphID = None
        self.curr_secret = None
        self.curr_HashID = None

        self.prev_EphID = None
        self.prev_secret = None

        self.hashID_queue = Queue(maxsize=2)
        self.shares_queue = Queue()

        # shares received within 't'-seconds
        self.recv_shares = Queue()
        self.share_ids_counter = dict()

        self.EphIDs = Queue()

        self.has_COVID = has_covid

        self.log_msg = MessageFormatter.MessageFormatter(origin=f'client')


    def gen_EphID_shares(self) -> None:
        """
        The thread process to generate EphIDs every t (EphID_time)
        """
        while not self.stop_event.is_set():
            start_timer = time.perf_counter()

            # save previous (pk, sk) for logging
            self.prev_EphID = self.curr_EphID
            self.prev_secret = self.curr_secret
        
            # generate new EphID
            self.curr_EphID, self.curr_secret = ID.gen_EphID()
            # generate new HashID based on EphID
            hash_EphID = bytearray(
                SHA256.new(data=self.curr_EphID.to_bytes(32, byteorder="big")).digest()
            )[0:3]

            self.log_msg.log_local(task=1, id=hash_EphID.hex(), action="EPHID GEN", data={'EphID': f"{self.curr_EphID.to_bytes(32, byteorder='big')[0:6].hex()}.."})

            self.hashID_queue.put(hash_EphID)

            # split new EphID into n shares
            new_shares = ID.gen_shares(new_EphID=self.curr_EphID, k=self.k, n=self.n)
            
            self.log_msg.log_local(task=2, id=hash_EphID.hex(), action="SSS SPLIT", data={'EphID': f"{self.curr_EphID.to_bytes(32, byteorder='big')[0:6].hex()}..", 'total shares': self.n})
            self.log_msg.log_local(task=2, id=hash_EphID.hex(), action="SSS GEN", data={'Shares generated:': ''})

            # store shares in broadcast queue
            self.shares_queue.put(new_shares)
            
            fshares = [f"share {i}: {share.hex()}" for i, share in enumerate(new_shares)]
            self.log_msg.log_list_data(fshares)

            delay = time.perf_counter() - start_timer 
            
            time.sleep(self.t - delay)


    def broadcast_shares(self) -> None:
        """
        Distribute the secret shares every 3 seconds
        """
        while not self.stop_event.is_set():
            
            shares = self.shares_queue.get(block=True)
            self.curr_HashID = self.hashID_queue.get(block=True)

            for i, share in enumerate(shares):
                start_timer = time.perf_counter()
                
                msg = self.curr_HashID + share
               
                self.UDP_SEND_SOCK.sendto(msg, ('255.255.255.255', self.UDP_SEND_PORT))

                self.log_msg.send(task='3A', id=self.curr_HashID.hex(), receiver="ALL", action="SHARE BROADCAST", data={'EphID Hash': f"{self.curr_HashID.hex()}", 'share id': i, 'value': f"{share[:6].hex()}.."})

                delay = time.perf_counter() - start_timer 

                time.sleep(3 - delay)

        # close UDP connection
        self.UDP_SEND_SOCK.close()

    def udp_receiver(self) -> None:
        """
        Listens for broadcasted shares continuously 
        """        
        # Listening on UDP port for message drops and broadcast shares
        while not self.stop_event.is_set():

            # should be receiving 32 + 3 bytes at a time
            data, addr = self.UDP_RECV_SOCK.recvfrom(37)

            if not data:
                continue

            # process data:
            d = bytearray(data)
            key, ephID = d[0:3], d[3:]

            # if message is own share, drop it
            if key == self.curr_HashID:
                continue

            # if probability < defined probability, drop message
            p = 100 #random.randrange(0, 100)
            if p < self.p:
                self.log_msg.recv(task='3B', sender=f"client {key.hex()}", action="SHARE DROP", data={'reason':'probability', 'p': f'{self.p}', 'rand': p})
                continue

            self.log_msg.recv(task='3A', sender=f"client {key.hex()}", action="SHARE RECV", data={'EphID': f"{ephID[:6].hex()}.."})
            
            # store data safely in queue to prevent race conditions
            self.recv_shares.put([key, ephID])

            # keep track of shares received that belong to the same ephID
            self.update_recv_share_ids_count(key, f"{ephID[:6].hex()}..")

        # close UDP connection
        self.UDP_RECV_SOCK.close()


    def update_recv_share_ids_count(self, key, share) -> None:
        """
        Count number of shares recevied from the same EphID share
        """

        if len(self.share_ids_counter) == 0 or key.hex() not in self.share_ids_counter.keys():
            self.share_ids_counter[key.hex()] = {'count': 1, 'shares': [share]}

        else:
            self.share_ids_counter[key.hex()]['count'] += 1
            self.share_ids_counter[key.hex()]['shares'].append(share)

        self.log_msg.recv(task='3C', sender=f"client {key.hex()}", action="COUNT SHARES", data={'EphID Hash': key.hex(), 'shares': f"{self.share_ids_counter[key.hex()]['shares']}", 'count': f"{self.share_ids_counter[key.hex()]['count']}/{self.n}"})
    
    
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

                num_shares = len(ephID_shares)

                # do nothing if not enough shares received
                if num_shares < self.k:
                    continue

                self.log_msg.recv(task='4a', sender=f'client {hash_id.hex()}', action='RECONSTRUCT ATTEMPT', data={'number of shares used': f'{num_shares}/{self.n}'})
                self.log_msg.log_list_data([f"share {i}: {share.hex()}" for i, share in enumerate(ephID_shares)])

                try:
                    # otherwise, reconstruct the shares
                    temp_ephID = ID.combine_shares(ephID_shares, self.k)

                    self.log_msg.recv(task='4a', sender=f'client {hash_id.hex()}', action='RECONSTRUCT SUCCESS', data={'Reconstructed EphID': f'{temp_ephID[:6].hex()}..'} )

                except ValueError as e:
                    self.log_msg.recv(task='4a', sender=f'client {hash_id.hex()}', action='RECONSTRUCT FAILED', data={'error': e} )
                    continue

                ephID_hash = SHA256.new(temp_ephID).digest()[0 : len(hash_id)]

                # verify reconstructed shares
                if ephID_hash != hash_id:                    
                    continue

                self.log_msg.recv(task='4b', sender=f'client {hash_id.hex()}', action='HASH VERIFY', data={'computed': ephID_hash.hex(), 'expected': hash_id.hex(), 'status': f'Hash match {ephID_hash == hash_id}'})

                valid_ephID = temp_ephID
                self.EphIDs.put(valid_ephID)

                # for logging
                private_key = self.prev_secret
                public_key = self.prev_EphID

                self.log_msg.log_local(task='5a', id = self.curr_HashID.hex(), action="ECDH INIT", data={'ECDH Parameters': ''})
                self.log_msg.log_list_data([f'private key: {private_key}', f'public key: {public_key}'])
                self.log_msg.recv(task='5a', sender=f'client {hash_id.hex()}', action="ECDH RECV PK", data={'public key (from EphID)': f"{valid_ephID.hex()}"})

                # successful reconstruction of shares can proceed to generate EncID. 
                encID = int(ID.ECDH(pk=valid_ephID, sk=private_key))
                self.log_msg.recv(task='5a', sender=f'client {hash_id.hex()}', action="ECDH COMPUTE", data={'EncID': f"{encID}"})
                
                # put encID into bloom filter
                curr_filter = self.DBF_list.curr_DBF()
                filter_before = curr_filter._get_set_bits()
                curr_filter.add_element(encID.to_bytes(32, byteorder='big'))
                filter_after = curr_filter._get_set_bits()

                self.log_msg.log_local(task=6, id=self.curr_HashID.hex(), action='DBF INSERT', data={'DBF': curr_filter._get_id(),'DBF set positions': filter_before})
                self.log_msg.log_local(task='7a', id=self.curr_HashID.hex(), action='DBF UPDATE', data={'DBF': curr_filter._get_id(),'DBF after': filter_after})
                

    def combine_DBFs(self):
        """
        Combines all available DBFs into a single bloom filter.

        """
        aggr_bloomFilter = bloomFilter(n=self.n, m=800_000)
        curr_DBF_list = self.DBF_list.get_curr_DBF_queue()
        
        curr_date = datetime.now()

        for dbf in curr_DBF_list:
            aggr_bloomFilter.merge_filter(dbf)
            oldest_date = min(curr_date, dbf.date)

        self.log_msg.log_local(task=None, id=self.curr_HashID.hex(), action='DBF COMBINE', data={'source DBFs': [dbf._get_id() for dbf in curr_DBF_list]})

        return aggr_bloomFilter, oldest_date

    def make_cbf(self) -> None:
        CBF, oldest_date = self.combine_DBFs()

        # check if entire bitarray == 0
        if (~CBF.filter).all(): print('all 0s')

        # check if entire bitarray == 1
        if (CBF.filter).all(): print('all 1s')

        self.log_msg.log_local(task=9, id=self.curr_HashID, action='CBF MAKE', data={'CBF': CBF._get_id(), 'set bits': CBF._get_set_bits(), 'time': oldest_date.strftime("%H:%M:%S.%f")[:-4]})

        return CBF

    def make_qbf(self):
        combined_BF, oldest_date = self.combine_DBFs()
        combined_BF.change_date(oldest_date)
        qbf = combined_BF

        self.log_msg.log_local(task=8, id=self.curr_HashID.hex(), action='QBF MAKE', data={'QBF': qbf._get_id(), 'oldest DBF': oldest_date.strftime("%H:%M:%S.%f")[:-4], 'set bits': qbf._get_set_bits()})

        return qbf

    def send(self, data, bf_type:str):
        # set up new TCP connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', 55000))

        self.log_msg.log_local(task='config', id=self.curr_HashID.hex(), action="TCP INIT", data={'TCP port': 55000})

        sock.sendall(pickle.dumps((bf_type.encode(), data)))

        n = 9 if bf_type == 'CBF' else '10a'
        self.log_msg.send(task=n, id=self.curr_HashID.hex(), receiver='server', action=f'UPLOAD {bf_type}', data={'status': 'CONNECTED'})

        resp = sock.recv(1024).decode()

        sock.shutdown(1)

        sock.close()

        return resp

    def upload_bf_to_server(self):
        
        # in seconds (t * 6 * 6) / 60 = (t * 6 / 10)
        dt =  self.t * 6
        # For simulating testing positive for COVID and uploading CBF
        # sent qbf counter
        num_qbf_sent = 0
        # qbfs sent until tested positive for COVID
        threshold = 0
        
        while not self.stop_event.is_set() and not self.stop_qbf_upload.is_set():
            time.sleep(dt)

            if num_qbf_sent >= threshold and self.has_COVID:
                cbf = self.make_cbf()
                
                resp = self.send(data=cbf, bf_type='CBF')

                self.stop_qbf_upload.set()

                continue

            # get new QBF 
            qbf = self.make_qbf()
             
            resp = self.send(data=qbf, bf_type='QBF')

            num_qbf_sent += 1

            if resp == 'MATCH FOUND':
                self.log_msg.recv(task='10b', sender='server', action='RISK MATCH', data={'match': 'TRUE', 'message': 'Exposure detected'})
                '''
                # The probability of contracting COVID-19 after exposure varies widely, 
                # generally ranging from roughly 2% for brief, close contact (under an hour) 
                # up to over 40% for #sustained household contact.
                '''

                self.has_COVID = True if random.randrange(0, 1000) < 2 else False
            else:
                self.log_msg.recv(task='10b', sender='server', action='RISK NO MATCH', data={'match': 'FALSE', 'message': 'No exposure'})
                
                

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

    # comment out for now
    t, k, n, p = (int(i) for i in sys.argv[1:5])

    assert (t in {15,18,21,24,27,30}), logger.error(msg="Invalid value 't' must be one of {15, 18, 21, 24, 27, 30}")
    assert (k >= 3 and k <= n), logger.error(msg="Invalid value 'k' must be >= 3 and < 'n'")
    assert (n >= 5), logger.error(msg="Invalid value 'n' must be >= 5")
    assert (p in {30, 40, 50, 60, 70}), logger.error(msg="Invalid value 'p' must be one of {30, 40, 50, 60, 70}")

    # cmdline arg to mark COVID patient
    try:
        has_covid = True if sys.argv[5] else False
    except IndexError as e:
        has_covid = False

    if t and k and n and p:
        client = Client(t=t, k=k, n=n, p=p, has_covid=has_covid)
    else:
        client = Client(t=t, k=k, n=n, p=p, has_covid=has_covid)

    client.run()

    threading.Event().wait()