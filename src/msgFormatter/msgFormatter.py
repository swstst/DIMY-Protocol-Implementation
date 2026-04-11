from datetime import datetime

class MessageFormatter:
      def __init__(self, origin:str):
            self.origin = origin

      def log_local(self, action:str, data) -> None:
            assert action in ['INIT', 'UPDATE', 'CREATED', 'EXIT'], f"{self.origin} ERROR! Not valid option"
            
            time = datetime.now().strftime("%H:%M:%S")
            fdata = '; '.join(f"{k}={v}" for k, v in data.items())
            
            print("{:<8} [{:<5}] [{:^10}] {:<10} |".format(time, 'LOCAL', action, self.origin), fdata)

      def log_conn(self, receiver: str, data) -> None:
            time = datetime.now().strftime("%H:%M:%S")
            fdata = '; '.join(f"{k}={v}" for k, v in data.items())
            
            print("{:<8} [S-->C] [{:^10}] {:<10} -> {:<10} |".format(time, 'SERVER', self.origin, receiver), fdata)
            

      def send(self, receiver:str, action:str, data) -> None:
            assert action in ['SEND QBF', 'SEND CBF', 'SEND DBF', 'MATCH', 'ERROR'], f"{self.origin} ERROR! Not valid option"

            time = datetime.now().strftime("%H:%M:%S")
            fdata = '; '.join(f"{k}={v}" for k, v in data.items())

            x = 'S' if self.origin == 'server' else 'C'
            y = 'S' if receiver == 'server' else 'C'

            print("{:<8} [{:<5}] [{:^10}] {:<10} -> {:<10} |".format(time, f"{x}-->{y}", action, self.origin, receiver), fdata)
            

      def recv(self, sender:str, data) -> None:                        
            time = datetime.now().strftime("%H:%M:%S")
            fdata = '; '.join(f"{k}={v}" for k, v in data.items())

            x = 'S' if sender == 'server' else 'C'
            y = 'S' if self.origin == 'server' else 'C'
            
            print("{:<8} [{:<5}] [{:^10}] {:<10} -> {:<10} |".format(time, f"{x}-->{y}", 'RECV', sender, self.origin), fdata)