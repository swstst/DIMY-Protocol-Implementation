"""
RELAY ATTACK CODE
"""

import sys
import threading
import socket
import random
import time
from Crypto.Hash import SHA256
from datetime import datetime

from ephID import ID

from msgFormatter import msgFormatter as MessageFormatter


# Keep logs in a queue.

# UDP Configuration
UDP_BROADCAST_ADDR = "127.0.0.1"
class Client:
    def __init__(self, t: int, k: int, n: int, p: int):

        self.CLIENT_ID = random.randrange(1000, 10_000)

        self.UDP_RECV_PORT = 5000
        self.UDP_SEND_PORT = 5000

        # UDP socket for shares broadcast
        self.UDP_SOCK = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # In real world, I'm guessing this would need to be a hijack so maybe need to keep receiving input from OS
        self.t = t
        self.k = k
        self.n = n
        self.p = int(p)

        self.log_msg = MessageFormatter.MessageFormatter(origin=f'client_{self.CLIENT_ID}')


    def udp_rebroadcast_attack(self) -> None:
        """
        Listens for broadcasted shares continuously 
        """        
        # Listening on UDP port for message drops and broadcast shares
        while not self.stop_event.is_set():

            # should be receiving 32 + 3 bytes at a time
            data, addr = self.UDP_SOCK.recvfrom(35)

            if not data:
                continue

            # if probability < defined probability, drop message
            p = random.randrange(0, 100)

            if p < self.p:
                continue

            # rebroadcast share
            self.UDP_SOCK.sendto(data, (UDP_BROADCAST_ADDR, self.UDP_SEND_PORT))

            self.log_msg.recv(sender=f"client_{key.hex()}", data={'share': f"{ephID[:4].hex()}.."})
            


    def run(self):
        """
        Main process

        Just initializes the attack 
        """

        # enable address reuse
        self.UDP_SOCK.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.UDP_SOCK.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        except AttributeError:
            pass

        # start listening on receiving UDP port
        self.UDP_SOCK.bind((UDP_BROADCAST_ADDR, self.UDP_RECV_PORT))
        self.log_msg.log_local(action="INIT", data={'status': 'listening', 'port': self.UDP_SEND_PORT })
        
        # init threads
        udp_recv_thread = threading.Thread(target=self.udp_rebroadcast_attack, daemon=False)

        # start threads
        udp_recv_thread.start()

        


    def stop_all_processes(self):
        self.stop_event.set()


if __name__ == "__main__":
    # graceful invalid input handling
    # try:



    print('starting client')
    client = Client(t=15, k=3, n=5, p=30)

    print('created client')
    print()
    print()

    client.run() 
    

    # client.UDP_SOCK.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # try:
    #     client.UDP_SOCK.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    # except AttributeError:
    #     pass

    # # start listening on receiving UDP port
    # client.UDP_SOCK.bind((UDP_BROADCAST_ADDR, client.UDP_RECV_PORT))
    
    # client.log_msg.log_local(action="INIT", data={'UDP port': client.UDP_RECV_PORT, 'TCP port': '55000'})

    # # init threads
    # udp_recv_thread = threading.Thread(target=client.udp_receiver, daemon=False)
    # reconstruct_ephID_thread = threading.Thread(target=client.reconstruct_shares, daemon=False)

    # # start threads
    # udp_recv_thread.start()
    # reconstruct_ephID_thread.start()

    # client.scheduler.add_job(func=client.gen_EphID_shares, trigger='interval', seconds=client.t, coalesce=True, max_instances=50)
    
    # # broadcast shares over UDP every 3 seconds
    # client.scheduler.add_job(func=client.broadcast_shares, trigger='interval', seconds=3, coalesce=True, max_instances=50)
    
    # # reconstruct ephIDs once k-shares have been received
    # client.scheduler.start()

    # while True:
    #     time.sleep(0.01)
    
    

    # # Unpack arguments
    # t, k, n, p = sys.argv[1:5]
    
    # # Convert to integers
    # t, k, n, p = int(t), int(k), int(n), int(p)
    
    # # Create client class
    # client = Client(t=t, k=k, n=n, p=p)

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
