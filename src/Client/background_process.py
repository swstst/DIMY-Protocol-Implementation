"""
This is the background processes class,
where all the processes run.
"""

import threading
import time

from queue import *

from ID import *

class backgroundProcess:
    def __init__(self, t, k, n, ip, broadcast_port, udp_socket):
        
        self.IP = ip
        self.BROADCAST_PORT = broadcast_port
        self.SOCKET = udp_socket
        
        self.t = t
        self.k = k
        self.n = n

        # self.EphID_ready_event = threading.Event()
        self.stop_event = threading.Event()
        self.secrets_ready_event = threading.Event()
        
        self.curr_EphID = None
        self.shares_queue = Queue()

    def gen_EphID_shares_every_t(self):
        """
        The thread process to generate EphIDs every t (EphID_time)
        """
        print("\n\ngen_EphID thread started")
        
        while not self.stop_event.is_set():

            # generate new EphID
            self.curr_EphID = gen_EphID(self.t)
            print("new EphID generated\n", self.curr_EphID)

            # split new EphID into n shares
            new_shares = gen_shares(new_EphID=self.curr_EphID, k=self.k, n=self.n) 
            print("new secret shares generated")
            for share in new_shares:
                print(share)

            # store shares in broadcast queue
            self.shares_queue.put(new_shares)
            

            # wait t seconds before generating new shares
            time.sleep(self.t)

    
    def broadcast_shares(self):
        """
        The thread process to distribute the secrets every 3 seconds
        """        
        print("\n\nsharedSecret thread started")

        print("started broadcasting on port", self.BROADCAST_PORT)
        
        while not self.stop_event.is_set():
            
            shares = self.shares_queue.get(block = True)
            
            for share in shares:
                # broadcast share over UDP
                self.SOCKET.sendto(share,(self.IP, self.BROADCAST_PORT))
                
                print("share sent", share)
                
                # wait 3 seconds before broadcasting new shares
                time.sleep(3)

    def ID_processes(self):
        """
        Run all the threads
        
        EphID_gen_thread will run on it's own the whole time, 
        SSS_thread will run the whole time as well but repeats every time new shares are developed
        
        """

        print("Starting background processes")
        
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

