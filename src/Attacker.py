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

