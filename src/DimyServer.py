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
        self.format_msg.log_local(action="INIT", data={'msg': "new Client Connected"})

        # data sent by client will always be QBF/CBF = 100kB = 800_000b
        TOTAL_SIZE = 800_000
        # receive data 2000b at a time
        BUFF_SIZE = 2000
        
        recv_data_size = 0

        try:
            while recv_data_size <= TOTAL_SIZE:
                data = bytearray()
                
                while True:
                    part = client_socket.recv(BUFF_SIZE)
                    data.extend(part)
                    
                    if len(part) < BUFF_SIZE:
                        break
                
                if not data:
                    break

                header, bf = pickle.loads(data)

                if header == "CBF":
                    self.CBFs.appendleft(bf)
                    client_socket.sendall('200'.encode())

                elif header == "QBF":
                    match = self._QBF_matching(QBF=bf)
                    if match:
                        client_socket.sendall("MATCH FOUND".encode())
                    else:
                        client_socket.sendall("NO MATCH".encode())

                else:
                    client_socket.sendall("WRONG INPUT".encode())

                self.format_msg.recv(sender="client", data={'type': header, 'data length': len(data)})

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
