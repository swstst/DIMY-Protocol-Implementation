import gen_ID
import threading
import time
import socket
import random
import sys

# UDP Configuration
UDP_IP = '127.0.0.1'
UDP_RECV_PORT = 8000
UDP_SEND_PORT = 8001
class client:
    def __init__(self, t, k, n, p):
        assert(t in {15,18,21,24,27,30})
        assert(k >= 3)
        assert(n >= 5)
        assert(p in {30, 40, 50, 60, 70})

        self.time_cycle = t     
        self.k = k
        self.n = n    

        # message drop received probability 
        self.p = int(p)

        # UDP socket for shares broadcast
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # start listening on receiving UDP port
        self.udp_sock.bind((UDP_IP, UDP_RECV_PORT))
        
        # simultaneous broadcast shares 
        self.broadcast_thread = threading.Thread(target=self.timer_3s, daemon=False)
        
        # simultaneous UDP port listening
        self.udp_recv_thread = threading.Thread(target=self.receiver, daemon=False)

        # the following need to be moved to some client main thread
        self.broadcast_thread.start()
        self.udp_recv_thread.start()
        

    def broadcast_shares(self, shares):
        
        i = 0
        
        while True:
            # get next share to send
            share = shares[i]
            
            # wait 3 seconds
            time.sleep(3)

            # broadcast share over UDP
            self.udp_sock.sendto(share,(UDP_IP, UDP_SEND_PORT))

            # increment shares index
            i += 1

    def message_drop(self):
        # how frequently does this need to be?
        
        msg = b'Hi'
        

        if probability*10 < self.p:
            # drop message
            ...

    def receiver(self):
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


if __name__ == '__main__':
    # Create client class

    ...