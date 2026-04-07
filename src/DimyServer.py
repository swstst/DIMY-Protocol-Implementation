import socket

from random import randint


class Server:
      def __init__(self):
            self.ADDR = '127.0.0.1'
            self.PORT =  55000

            
            self.TCP_SOCK = socket(socket.AF_INET, socket.SOCK_STREAM)

            # CBF list

      def start(self):
            self.TCP_SOCK.bind((self.ADDR, self.PORT))

            self.TCP_SOCK.listen()

            