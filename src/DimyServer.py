import threading
import socket, pickle, struct
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

        if not len(cbfs):
            return False 
        
        for cbf in cbfs:
            
            # if QBF creation time is after CBF upload, then ignore
            if QBF.date > cbf.date:
                self.format_msg.log_local(task='10c', id=None, action='QBF CBF COMPARE', data={'In date range?': 'FALSE', f'QBF': QBF._get_id(), 'CBF': cbf._get_id()})
                break

            self.format_msg.log_local(task='10c', id=None, action='QBF CBF COMPARE', data={'In date range?': 'TRUE', f'QBF': QBF._get_id(), 'CBF': cbf._get_id()})
            matching = QBF.filter & cbf.filter 
            
            if matching.count(1) >= QBF.k:
                return True

        return False


    def make_client_thread(self, client_socket):
        """
        Handles each client connection
        """   
        self.format_msg.log_local(task='config', id=None, action="TCP CONNECT", data={'msg': "New client connected."})

        # receive data 2000b at a time
        BUFF_SIZE = 4096
        
        data = b''

        try:            
            # read data in chunks
            chunk = client_socket.recv(BUFF_SIZE)
            if not chunk:
                raise ConnectionError("Socket closed")

            TOTAL_SIZE = struct.unpack('!i', chunk[:4])[0] 
            first_chunk = chunk[4:]
            
            data += first_chunk 
            
            while len(data) < TOTAL_SIZE:
                chunk = client_socket.recv(BUFF_SIZE)
                if not chunk:
                    break
                data += chunk
                    

            header, bf = pickle.loads(data)

            header = header.decode()

            if header == "CBF":
                self.CBFs.appendleft(bf)
                
                client_socket.sendall("200".encode())

                self.format_msg.recv(task=9, sender='client', action="CBF UPLOAD", data={'status': 'SUCCESS', 'CBF': bf._get_id(), 'set bits': bf._get_set_bits(), 'date range': bf.date.strftime("%H:%M:%S.%f")[:-4]})

            elif header == "QBF":
                match = self._QBF_matching(QBF=bf)

                self.format_msg.recv(task='10c', sender='client', action='QBF RECV', data={'status': 'SUCCESS', 'QBF': bf._get_id(), 'set bits': bf._get_set_bits(), 'date range': bf.date.strftime("%H:%M:%S.%f")[:-4]})
                
                if match:
                    client_socket.sendall("MATCH FOUND".encode())
                    self.format_msg.log_local(task='10c', id=None, action='MATCH FOUND', data={'QBF': bf._get_id()})
                    
                else:
                    client_socket.sendall("NO MATCH".encode())
                    self.format_msg.log_local(task='10c', id=None, action='NO MATCH FOUND', data={'QBF': bf._get_id()})

            else:
                client_socket.sendall("WRONG INPUT".encode())
                
        except ConnectionResetError:
            print("Client disconnected abruptly")

        finally:
            # close the connection after
            client_socket.close()            
    
    def start(self):
        self.TCP_SOCK.bind((self.ADDR, self.PORT))

        self.TCP_SOCK.listen()

        # pretty print
        self.format_msg.log_local(task='config', id=None, action="TCP INIT", data={'addr': self.ADDR, 'port': self.PORT})
        
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
