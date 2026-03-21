import threading
import socket
import random

import background_process

# UDP Configuration
UDP_IP = '127.0.0.1'

class client:
    def __init__(self, t, k, n, p):
        assert(t in {15,18,21,24,27,30})
        assert(k >= 3)
        assert(n >= 5)
        assert(p in {30, 40, 50, 60, 70})

        self.UDP_RECV_PORT = random.randrange(5000, 6000)
        self.UDP_SEND_PORT = random.randrange(7000, 8000)

        self.time_cycle = t     
        self.k = k
        self.n = n    

        # message drop received probability 
        self.p = int(p)

        # UDP socket for shares broadcast
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # start listening on receiving UDP port
        self.udp_sock.bind((UDP_IP, self.UDP_RECV_PORT))
        self.background_process_instance = background_process.backgroundProcess(t=self.time_cycle, k=self.k, n=self.n)
         
        # simultaneous UDP port listening
        self.udp_recv_thread = threading.Thread(target=self.receiver, daemon=False)

        # the following need to be moved to some client main thread
        self.background_process_instance.ID_processes()
        self.udp_recv_thread.start()
 

    def receiver(self):
        print("Started listening on port", self.UDP_RECV_PORT)
        # Listening on UDP port for message drops and broadcast shares
        while True:
            # temp buffer size is 1024 bytes
            data, addr = self.udp_sock.recvfrom(1024)

            if not data:
                continue
            
            p = random.random(0, 1)
                
            if p * 10 < self.p:
                print("message dropped")
                continue
            
            # store the data somewhere
            print(f"received data: {data}")

    def stop_everything(self):
        self.background_process_instance.stop_all_processes()

