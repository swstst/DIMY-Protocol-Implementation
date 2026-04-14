import threading
import socket, pickle
# from datetime import datetime
# from bitarray import bitarray
# from random import randint
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
        # prevent race condition
        cbfs = self.CBFs.copy()

        print(len(cbfs))

        if not len(cbfs):
            return False 

        qbf_oldest_date, qbf_newest_date = QBF.date_range
        
        for cbf in cbfs:
            cbf_oldest_date, cbf_newest_date = cbf.date_range
            
            # if QBF creation time is before CBF upload, then ignore
            if qbf_newest_date < cbf_oldest_date or qbf_oldest_date > cbf_newest_date:
                print("QBF", QBF.date.strftime("%H:%M:%S.%f")[:-4], "CBF", f"[{cbf_oldest_date.strftime("%H:%M:%S.%f")[:-4]} - {cbf_newest_date.strftime("%H:%M:%S.%f")[:-4]}]" )
                break
            
            matching = QBF.filter ^ cbf.filter 

            if matching.all():
                return False
            elif matching.count(1) >= QBF.k:
                print(matching.count(1), QBF.k)
                return True

        return False


    def make_client_thread(self, client_socket):
        """
        Handles each client connection
        """   
        self.format_msg.log_local(action="INIT", data={'msg': "new Client Connected"})

        # data sent by client will always be QBF/CBF = 100kB = 800_000b
        TOTAL_SIZE = 800_000
        # receive data 2000b at a time
        BUFF_SIZE = 4096
        
        data = b''

        try:            
            # read data in chunks
            while len(data) <= TOTAL_SIZE:
                chunk = client_socket.recv(BUFF_SIZE)

                data += chunk
                    
                if len(chunk) < BUFF_SIZE:
                    break

            header, bf = pickle.loads(data)

            header = header.decode()

            self.format_msg.recv(sender="client", data={'type': header, 'data length': len(data)})

            if header == "CBF":
                self.CBFs.appendleft(bf)
                
                client_socket.sendall("200".encode())

                self.format_msg.send(receiver="client", action="RESPONSE", data={'status': '200'})

            elif header == "QBF":
                match = self._QBF_matching(QBF=bf)
                
                if match:
                    client_socket.sendall("MATCH FOUND".encode())
                    
                    self.format_msg.send(receiver="client", action="RESPONSE", data={'msg': 'MATCH FOUND'})
                    
                else:
                    client_socket.sendall("NO MATCH".encode())
                    
                    self.format_msg.send(receiver="client", action="RESPONSE", data={'msg': 'NO MATCH'})

            else:
                client_socket.sendall("WRONG INPUT".encode())
                
                self.format_msg.send(receiver="client", action="RESPONSE", data={'msg': 'WRONG INPUT'})
                
        except ConnectionResetError:
            print("Client disconnected abruptly")

        finally:
            # close the connection after
            client_socket.close()            
    
    def start(self):
        self.TCP_SOCK.bind((self.ADDR, self.PORT))

        self.TCP_SOCK.listen()

        # pretty print
        self.format_msg.log_local(action="INIT", data={'addr': self.ADDR, 'port': self.PORT})
        print_log_thread = threading.Thread(target=self.format_msg.print_logs, daemon=False)
        print_log_thread.start()

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
