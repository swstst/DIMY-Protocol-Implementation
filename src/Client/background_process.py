"""
This is the background processes class,
where all the processes run.
"""

import threading
import time

from queue import *
from ID import *
from Crypto.Hash import SHA256
class backgroundProcess:
    def __init__(self, t, k, n, broadcast_addr, broadcast_port, udp_socket):
        
        self.BROADCAST_ADDR = broadcast_addr
        self.BROADCAST_PORT = broadcast_port
        self.SOCKET = udp_socket
        
        self.t = t
        self.k = k
        self.n = n

        # self.EphID_ready_event = threading.Event()
        self.stop_event = threading.Event()
        self.secrets_ready_event = threading.Event()
        
        self.curr_EphID = None
        self.curr_HashID = Queue(maxsize=2)
        self.shares_queue = Queue()

    def gen_EphID_shares_every_t(self):
        """
        The thread process to generate EphIDs every t (EphID_time)
        """        
        while not self.stop_event.is_set():

            # generate new EphID
            self.curr_EphID = gen_EphID(self.t)
            print("New EphID generated")
            print(self.curr_EphID, end='\n\n')

            # generate new HashID based on EphID
            hash_EphID = bytearray(SHA256.new(data=self.curr_EphID.to_bytes(32, byteorder='big')).digest())[0:4]
            self.curr_HashID.put(hash_EphID)
            print("New HashID generated")
            print(hash_EphID, end='\n\n')

            # split new EphID into n shares
            new_shares = gen_shares(new_EphID=self.curr_EphID, k=self.k, n=self.n) 
            print("New secret shares generated")
            for i, share in enumerate(new_shares):
                print(i, ":", share[:5], "...")
                
            print()

            # store shares in broadcast queue
            self.shares_queue.put(new_shares)
            
            # wait t seconds before generating new shares
            time.sleep(self.t)

    
    def broadcast_shares(self):
        """
        The thread process to distribute the secrets every 3 seconds
        """        
        print("Started broadcasting on port", self.BROADCAST_PORT, end='\n')
        
        while not self.stop_event.is_set():
            
            shares = self.shares_queue.get(block = True)
            hashID = self.curr_HashID.get(block = True)
            
            for share in shares:
                msg = hashID + share

                print("-" * 5, "SEND:", msg, end='\n\n')
                
                # broadcast share over UDP
                self.SOCKET.sendto(share,(self.BROADCAST_ADDR, self.BROADCAST_PORT))
                
                # wait 3 seconds before broadcasting new shares
                time.sleep(3)

    def ID_processes(self):
        """
        Run all the threads
        
        EphID_gen_thread will run on it's own the whole time, 
        SSS_thread will run the whole time as well but repeats every time new shares are developed
        
        """
        
        gen_EphID_shares_thread = threading.Thread(target=self.gen_EphID_shares_every_t, daemon=True)
        broadcast_thread = threading.Thread(target=self.broadcast_shares, daemon=False)

        gen_EphID_shares_thread.start()
        broadcast_thread.start()

        # TO DO: graceful shutdown

        # run = True
        
        # while run:
        #     # listen for keyboard interrupt
        #     try:
        #         pass
            
        #     except KeyboardInterrupt:
                
        #         print("\nShutting down client...")
        #         self.stop_all_processes()

        #         run = False


    def stop_all_processes(self):
        self.stop_event.set()

