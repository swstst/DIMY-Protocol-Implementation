import sys
import threading
import socket
import random
import time
from queue import *
from Crypto.Hash import SHA256
from apscheduler.schedulers.blocking import BlockingScheduler

from ephID import ID

from bloomFilter.NodeDBFList import NodeDBFList
from bloomFilter.bloomFilter import bloomFilter

# UDP Configuration
UDP_BROADCAST_ADDR = '127.0.0.1'

class Client:
    def __init__(self, t:int, k:int, n:int, p:int):

        self.CLIENT_ID = random.randrange(1000,10_000)
        
        self.UDP_RECV_PORT = 5000
        self.UDP_SEND_PORT = 5000

        # UDP socket for shares broadcast
        self.UDP_SOCK = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # TCP socket object to send CBF to server
        self.TCP_SOCK = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.t = t     
        self.k = k
        self.n = n    
        self.p = int(p)

        self.DBF_list = NodeDBFList(t, n, m)
        self.CBF = bloomFilter(n=6, m=800_000)
        self.QBF = bloomFilter(n=6, m=800_000)

        self.stop_event = threading.Event()
        self.secrets_ready_event = threading.Event()
        self.t_interval_event = threading.Event()
        self.gen_qbf_stop = threading.Event()

        self.curr_EphID = None
        self.curr_secret = None
        self.curr_HashID = None
        
        self.hashID_queue = Queue(maxsize=2)
        self.shares_queue = Queue()

        # shares received within 't'-seconds
        self.recv_shares = Queue()
        
        self.EphIDs = Queue()

        self.has_COVID = False
        


    def gen_EphID_shares_every_t(self):
        """
        The thread process to generate EphIDs every t (EphID_time)
        """        
        while not self.stop_event.is_set():

            # generate new EphID
            self.curr_EphID, self.curr_secret = ID.gen_EphID(self.t)
            print("Client", self.CLIENT_ID, ": New EphID generated")
            print(self.curr_EphID, end='\n\n')

            # generate new HashID based on EphID
            hash_EphID = bytearray(SHA256.new(data=self.curr_EphID.to_bytes(32, byteorder='big')).digest())[0:3]
            
            self.hashID_queue.put(hash_EphID)
            print("Client:", self.CLIENT_ID, "New HashID generated")
            print(hash_EphID, end='\n\n')

            # split new EphID into n shares
            new_shares = ID.gen_shares(new_EphID=self.curr_EphID, k=self.k, n=self.n) 
            print("Client", self.CLIENT_ID, ": New secret shares generated")
            for i, share in enumerate(new_shares):
                print(i, ":", share[:5], "...")
                
            print()

            # store shares in broadcast queue
            self.shares_queue.put(new_shares)
            
            # wait t seconds before generating new shares
            time.sleep(self.t)

        return
        

    def broadcast_shares(self):
        """
        The thread process to distribute the secrets every 3 seconds
        """        
        print("Started broadcasting on port", self.UDP_SEND_PORT, end='\n')
        
        while not self.stop_event.is_set():
            
            shares = self.shares_queue.get(block = True)
            self.curr_HashID = self.hashID_queue.get(block = True)
            
            for share in shares:
                msg = self.curr_HashID + share

                print("Client:", self.CLIENT_ID, "-" * 5, "SEND:", msg[:10], end='\n\n')
                
                # broadcast share over UDP
                self.UDP_SOCK.sendto(msg,(UDP_BROADCAST_ADDR, self.UDP_SEND_PORT))
                
                # wait 3 seconds before broadcasting new shares
                time.sleep(3)
        return
        
 
    def receiver(self):
        print("-" * 15,"RECV: Started listening on port", self.UDP_RECV_PORT, end='\n\n')
        
        # Listening on UDP port for message drops and broadcast shares
        while not self.stop_event.is_set():
            
            # should be receiving 32 + 3 bytes at a time
            data, addr = self.UDP_SOCK.recvfrom(35)

            if not data:
                continue

            # process data:
            d = bytearray(data)
            key, ephID = d[0:3], d[3:]

            if self.curr_HashID == key:
                continue

            p = random.randrange(0, 100)
                        
            if p < self.p:
                print("Client:", self.CLIENT_ID, "-" * 15, f"RECV: p = {p}, message dropped", end='\n\n')
                continue
            
            # store the data somewhere
            self.recv_shares.put([key, ephID])
            
            print("Client:", self.CLIENT_ID, "-" * 15, "RECV: got share", ephID, "...", end='\n\n')

        return

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

                ephID_hash = SHA256.new(temp_ephID).digest()[0:len(hash_id)]

                # verify reconstructed shares
                if ephID_hash != hash_id:
                    continue

                valid_ephID = temp_ephID
                    
                # successful reconstruction of shares can proceed to generate EncID.
                print("Client:", self.CLIENT_ID, "-" * 15, "!! Successful reconstruction of EphID", valid_ephID, end='\n\n')

                self.EphIDs.put(valid_ephID)
                
                encID = ID.ECDH(valid_ephID, self.curr_secret)
                
                # put encID into bloom filter
                curr_filter = self.DBF_list.curr_DBF()
                curr_filter.add_element(encID)
        

    def gen_cbf(self):
        """
        Combines all available DBFs into a single bloom filter - CBF.
        """
        curr_DBF_list = self.DBF_list.get_curr_DBF_queue()

        for dbf in curr_DBF_list:
            self.CBF.add_element(dbf)

        return True


    def tcp_client(self):

        while not self.stop_event.is_set():
            
            if self.has_COVID:
                
                self.gen_cbf()
                
                self.TCP_SOCK.sendall(self.CBF)

                resp = self.TCP_SOCK.recv(1024).decode()

                print(resp)
                
                # stop generating QBF
                self.gen_qbf_stop.set()
                
                return

            else:
                self.TCP_SOCK.sendall(self.qbf)
                
                resp = self.TCP_SOCK.recv(1024).decode()

                print(resp)

                if resp == 'COVID CLOSE CONTACT':
                    
                    self.has_COVID = True
                    
                    continue

        # close socket connection
        self.TCP_SOCK.close()

        return 


    def run(self):
        """
        Main process

        udp_recv_thread will start as soon as client has been instantiated
        gen_EphID_shares_thread will run on it's own the whole time, 
        broadcast_thread will start once self.shares_queue is not empty
        
        """
        
        # enable address reuse
        self.UDP_SOCK.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.UDP_SOCK.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            
        except AttributeError:
            pass         
    
        # start listening on receiving UDP port
        self.UDP_SOCK.bind((UDP_BROADCAST_ADDR, self.UDP_RECV_PORT))

        # connect to server
        self.TCP_SOCK.connect(('127.0.0.1', 55000))

        # init threads
        udp_recv_thread = threading.Thread(target=self.receiver, daemon=False)
        tcp_send_thread = threading.Thread(target=self.tcp_client, daemon=False)
        gen_EphID_shares_thread = threading.Thread(target=self.gen_EphID_shares_every_t, daemon=True)
        broadcast_thread = threading.Thread(target=self.broadcast_shares, daemon=False)
        reconstruct_ephID_thread = threading.Thread(target=self.reconstruct_shares, daemon=False)

        # start threads
        udp_recv_thread.start()
        tcp_send_thread.start()
        gen_EphID_shares_thread.start()
        broadcast_thread.start()
        reconstruct_ephID_thread.start()

        while True:
            try:
                pass
            except KeyboardInterrupt:
                print("Shutting down client...")
                self.stop_all_processes()

                udp_recv_thread.join()
                tcp_send_thread.join()
                gen_EphID_shares_thread.join()
                broadcast_thread.join()
                reconstruct_ephID_thread.join()

                print("Goodbye!")

                sys.exit(1)

    def stop_all_processes(self):
        self.stop_event.set()         


if __name__ == '__main__':
    # graceful invalid input handling
    # try:
    
    # Unpack arguments
    t, k, n, p = sys.argv[1:5]
    # Convert to integers
    t, k, n, p = int(t), int(k), int(n), int(p)
    # Create client class
    client = Client(t=t, k=k, n=n, p=p)
    client.run()

    # except ValueError as ve:
    #     # Handle invalid integer conversion
    #     for name, value in zip(["t", "k", "n", "p"], sys.argv[1:5]):
    #         if not value.isdigit():
    #             print(f"[!] Invalid value for '{name}': integer required")

    #         # match (name):
    #         #     case 't':
    #         #         if not t in {15,18,21,24,27,30}: print("[!] Invalid value: 't' must be {15, 18, 21, 24, 27, 30}")
                    
    #         #     case 'k':
    #         #         if not (k >= 3): print("[!] Invalid value: 'k' must be >= 3")
                    
    #         #     case 'n':
    #         #          if not (n >= 5): print("[!] Invalid value: 'n' must be >= 5")

    #         #     case 'p':
    #         #         if not p in {30, 40, 50, 60, 70}: print("[!] Invalid value: 'p' must be {30, 40, 50, 60, 70}")                 

    #     sys.exit(1)

    # except Exception as e:
    #     # Handle wrong number of arguments or other errors
    #     print("[!] Invalid number of arguments passed: Require 'python client.py <time> <k-value> <n-value> <probability>'.")
    #     sys.exit(1)
