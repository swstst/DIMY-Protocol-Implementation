import socket, pickle
import deque
from datetime import datetime

from random import randint


class Server:
    def __init__(self):
        self.ADDR = "127.0.0.1"
        self.PORT = 55000

        self.TCP_SOCK = socket(socket.AF_INET, socket.SOCK_STREAM)

        self.CBFs = deque()

    def _QBF_matching(self, QBF) -> bool:
        for cbf in self.CBFs:

            if QBF.date > cbf.date:
                return False

            matching = QBF.filter & cbf.filter

            if matching.count(1) >= QBF.k:
                return True
        return False

    def start(self):
        self.TCP_SOCK.bind((self.ADDR, self.PORT))

        self.TCP_SOCK.listen()

        while True:
            conn, addr = self.TCP_SOCK.accept()

            with conn:
                data = conn.recv(1024)
                if not data:
                    break

                payload = pickle.load(data)

                header, BF = payload

                # TODO: PLEASE CHECK IF MY SOCKETS ARE RIGHT

                if header == "CBF":
                    self.CBFs.appendleft(BF)
                    conn.sendall("200")
                elif header == "QBF":
                    match = self._QBF_matching(QBF=BF)
                    if match:
                        conn.sendall("MATCH FOUND")
                    else:
                        conn.sendall("NO MATCH")
                else:
                    conn.sendall("WRONG INPUT")
