from datetime import datetime
import queue
class MessageFormatter:
      def __init__(self, origin:str):
            self.origin = origin
            self.log_q = queue.Queue()
            
      def log_local(self, action:str, data=None) -> None:            
            time = datetime.now().strftime("%H:%M:%S.%f")[:-4]
            fdata = '; '.join(f"{k} = {v}" for k, v in data.items()) if data else ''

            log = "{:<12} [{:<5}] | {:<10} | {:<10}".format(time, 'LOCAL', action, self.origin)

            s =("{:<68} |".format(log), fdata)

            self.log_q.put(s)

      def log_conn(self, receiver: str, data) -> None:
            time = datetime.now().strftime("%H:%M:%S.%f")[:-4]
            fdata = '; '.join(f"{k} = {v}" for k, v in data.items())

            log = "{:<12} [S-->C] | {:<10} | {:<10} -> {:<10}".format((time, 'SERVER', self.origin, receiver))

            s =("{:<68} |".format(log), fdata)

            self.log_q.put(s)

      def send(self, receiver:str, action:str, data=None) -> None:
            time = datetime.now().strftime("%H:%M:%S.%f")[:-4]
            fdata = '; '.join(f"{k} = {v}" for k, v in data.items()) if data else ''

            match (self.origin):
                  case 'server':
                        x = 'S'
                        y = 'C'
                  case 'attacker':
                        x = 'A'
                        y = 'C'
                  case _:
                        x = 'C'
                        y = 'S'

            log = "{:<12} [{:<5}] | {:<10} | {:<10} -> {:<10}".format(time, f"{x}-->{y}", action, self.origin, receiver)

            s =("{:<68} |".format(log), fdata)

            self.log_q.put(s)
            
      def recv(self, sender:str, data=None) -> None:                        
            time = datetime.now().strftime("%H:%M:%S.%f")[:-4]
            fdata = '; '.join(f"{k} = {v}" for k, v in data.items()) if data else ''

            match (self.origin):
                  case 'server':
                        y = 'S'
                  case 'attacker':
                        y = 'A'
                  case _:
                        y = 'C'

            x = 'S' if sender == 'server' else 'C'

            log = "{:<12} [{:<5}] | {:<10} | {:<10} -> {:<10}".format(time, f"{x}-->{y}", 'RECV', sender, self.origin)

            s = ("{:<68} |".format(log), fdata)

            self.log_q.put(s)

      def print_logs(self):
            while True:
                  msg = self.log_q.get()
                  print(*msg)