"""
This is the background processes class,
where all the processes run.
"""

import threading
import time
from ID import *
# import * from ID

class backgroundProcess:
    def __init__(self, t, k, n):
        self.stop_event = None
        self.EphID_time_var = t # this is t
        self.k = k
        self.n = n
        self.EphID_ready_event = threading.Event()
        self.secrets_ready_event = threading.Event()
        self.curr_EphID = None
        self.curr_secrets = None

    def gen_EphID_every_t(self):
        """
        The thread process to generate EphIDs every t (EphID_time)
        """
        while not self.stop_event.is_set():
            self.curr_EphID = gen_EphID(self.EphID_time)
            self.EphID_ready_event.set()

            self.stop_event.wait(self.EphID_time_var)

    def SharedSecret_gen_thread_process(self):
        """
        The thread process to generate Shared Secrets of every new EphIDs 
        once the EphIDs are generated
        """
        while not self.stop_event.is_set():
            self.EphID_ready_event.wait(self.EphID_time_var + 2) # Once EphID is ready this is released & code continues

            self.secrets = SharedSecret_gen(self.curr_EphID) # needs to take the new EphID as input
            
            self.EphID_ready_event.clear()
    
    def SharedSecret_Distribution(self, udp_socket, UDP_IP, UDP_SEND_PORT):
        print("started sending on", UDP_SEND_PORT)
        """
        The thread process to distribute the secrets
        """        
        while not self.stop_event.is_set():
            i = 0
            while True:
                # get next share to send
                share = self.curr_secrets[i]
                
                # wait 3 seconds
                time.sleep(3)

                # broadcast share over UDP
                udp_socket.sendto(share,(UDP_IP, UDP_SEND_PORT))

                # increment shares index
                i += 1

    def ID_processes(self):
        """
        Run all the threads
        
        EphID_gen_thread will run on it's own the whole time
        SharedSecret_gen_thread will wait and only run everytime EphID is generated and event is cleared
        SSS_thread will run the whole time as well but repeats every time new shares are developed
        """
        EphID_gen_thread = threading.Thread(target=self.gen_EphID_every_t, daemon=True)
        SharedSecret_gen_thread = threading.Thread(target=SharedSecret_gen, daemon=True)
        Broadcast_thread = threading.Thread(target=SharedSecret_Distribution, daemon=False)

        EphID_gen_thread.start()
        SharedSecret_gen_thread.start()
        Broadcast_thread.start()

    def stop_all_processes(self):
        self.stop_event.set()

