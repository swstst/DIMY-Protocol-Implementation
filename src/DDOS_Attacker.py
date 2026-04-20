import sys
import threading
import socket
import random
import time
import logging
from queue import *
from bitarray import bitarray
from msgFormatter import msgFormatter as MessageFormatter

# Attacker goal: prevent valid EncIDs from being constructed which leads to false negatives.

# Given 't' time, an attacker can replay received shares with a modified share value. Clients will then receive the share with a valid HashID - adding to their 'k' shares received. 

# However, since the share has been modified, construction of shares will fail. Therefore affecting client's ability to effectively construct a valid EncID with a valid close contact. 

class Attacker:
      def __init__(self, t: int, k: int, n: int, p: int):
            self.recv_port = 5000
            self.send_port = 5000

            self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            self.t = t
            self.k = k
            self.n = n
            self.p = p

            # does it need a DBF list?

            self.stop_event = threading.Event()
            # does it need a uplaod qbf event?

            # No current EphID required
            # Does not generate secret shares
            # Does not have a hashID

            self.shares_queue = Queue()

            # does it need this since shares are modified then sent right away?
            self.recv_shares = Queue()

            self.log_msg = MessageFormatter.MessageFormatter(origin='attacker')


      def get_shares(self) -> None:
            while not self.stop_event.is_set():
                  data, addr = self.recv_sock.recvfrom(37)

                  if not data:
                        continue

                  # process data
                  d = bytearray(data)
                  key, ephID = d[0:3], d[3:]

                  # if probability < defined probability, drop message
                  p = random.randrange(0, 100)
                  if p < self.p:
                        continue

            self.log_msg.recv(sender=f"client_{key.hex()}", data={'hash id': f"{key.hex()}", 'share': f"{ephID[:3].hex()}.."})
            
            # store data safely in queue to prevent race conditions
            self.recv_shares.put([key, ephID])

      def modify_shares(self, share:bytearray) -> bytearray:
            '''
            Flips a random bit in the array
            '''
            temp = bitarray().frombytes(share)
            i = random.randrange(3, len(temp))

            temp[i] ^= 1

            return bytearray(temp)
            
      def broadcast_fake_shares(self) -> None:
            '''
            Broadcasts fake shares every 1 second to prevent clients from constructing valid shares.
            '''
            curr_share = False
            
            while not self.stop_event.is_set():
                  # An attacker is more likely to succeed the more bogus shares it broadcasts. 
                  time.sleep(1)

                  try:
                        curr_share = self.recv_shares.get(block=False)
                        prev_share = curr_share.copy()
                        
                  except Exception as e:
                        print(e)
                        # case 1: no received shares at all because no clients exists so don't bother broadcasting bogus shares.
                        if curr_share == False:
                              continue
                        
                        # case 2: no new client shares received, keep modifying the previous share
                        curr_share = prev_share

                  # modify the share
                  bogus_share = self.modify_shares(curr_share)

                  # broadcast the share
                  self.send_sock(bogus_share, ('255.255.255.255', self.send_port))

      def run(self) -> None:
            # enable address reuse for receiving socket
            self.recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # set up broadcasting socket
            self.send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
      
            try:
                  self.recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

            except AttributeError:
                  pass

            self.recv_sock.bind(('', self.recv_port))
            
            get_shares_thread = threading.Thread(target=self.get_shares, daemon=False)
            broadcast_fake_shares_thread = threading.Thread(target=self.broadcast_fake_shares, daemon=False)
            # print log thread
            
            get_shares_thread.start()
            broadcast_fake_shares_thread.start()
            # print log thread start

      def stop_all_processes(self):
            self.stop_event.set()


if __name__ == '__main__':
      logger = logging.getLogger(__name__)
      
      t, k, n, p = sys.argv[1:5]

      assert (int(t) in {15,18,21,24,27,30}), logger.error(msg="Invalid value 't' must be one of {15, 18, 21, 24, 27, 30}")
      assert (int(k) >= 3 and int(k) <= int(n)), logger.error(msg="Invalid value 'k' must be >= 3 and < 'n'")
      assert (int(n) >= 5), logger.error(msg="Invalid value 'n' must be >= 5")
      assert (int(p) in {30, 40, 50, 60, 70}), logger.error(msg="Invalid value 'p' must be one of {30, 40, 50, 60, 70}")
      
      attacker = Attacker(t=18, k=4, n=6, p=40)
      attacker.run()
      
      