import threading
import select
import socket, pickle
from datetime import datetime
from bitarray import bitarray

from random import randint
from collections import deque

from msgFormatter import msgFormatter as MessageFormatter

class Server:
    def __init__(self):
        self.ADDR = "127.0.0.1"
        self.PORT = 55000

        self.TCP_SOCK = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.CBFs = deque()

        self.format_msg = MessageFormatter.MessageFormatter(origin='server')
        

    def _QBF_matching(self, QBF) -> bool:
        for cbf in self.CBFs:

            if QBF.date > cbf.date:
                return False

            matching = QBF.filter & cbf.filter

            if matching.count(1) >= QBF.k:
                return True
        return False


    def make_client_thread(self, client_socket):
        """
        Handles each client connection
        """   
        print('init new client')
        
        BUFF_SIZE = 1024

        try:
            while True:
                data = bytearray()
                while True:
                    part = client_socket.recv(BUFF_SIZE)
                    data.extend(part)
                    if len(part) < BUFF_SIZE:
                        break
                
                # this is really big dont print
                #print(data)

                if not data:
                    break

                header, bf = pickle.loads(data)

                print(data)

                match header:
                    case "CBF":
                        self.CBFs.appendleft(bf)
                        client_socket.sendall('200'.encode())
                        break

                    case "QBF":
                        match = self._QBF_matching(QBF=bf)
                        if match:
                            client_socket.sendall("MATCH FOUND".encode())
                        else:
                            client_socket.sendall("NO MATCH".encode())

                        break

                    case _:
                        client_socket.sendall("WRONG INPUT".encode())

                self.format_msg.recv(sender="client", data={'type': header, 'data': bf})

        except ConnectionResetError:
            print("Client disconnected abruptly")

        finally:
            # close the connection after
            client_socket.close()            
    
    def start(self):
        self.TCP_SOCK.bind((self.ADDR, self.PORT))

        # listens for up to at most 5 connections
        self.TCP_SOCK.listen()

        # pretty print
        self.format_msg.log_local(action="INIT", data={'addr': self.ADDR, 'port': self.PORT})

        while True:
            try:
                # accept client connections continuously
                conn, addr = self.TCP_SOCK.accept()

                client_thread = threading.Thread(target=self.make_client_thread, args=(conn,))
                client_thread.start()
                
            except ConnectionResetError as e:
                pass
                
        

if __name__ == '__main__':
    server = Server()
    server.start()
