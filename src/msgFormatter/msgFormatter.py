from datetime import datetime
import queue
class MessageFormatter:
      def __init__(self, origin:str):
            self.origin = origin
            self.log_q = queue.Queue()

      def base_log(self, task: str | int | None, action: str, data=None) -> list:
            time = datetime.now().strftime("%H:%M:%S.%f")[:-4]
            task_tag = ("[TASK {:<3}]".format(task) if task != 'config' else '[{:<8}]'.format('CONFIG')) if type(task) != type(None) else ""
            type_tag = "| {:<20} |".format(action)
            fdata = '; '.join(f"{k} = {v}" for k, v in data.items()) if data else ''
            
            return [time, task_tag, type_tag, fdata]

      def log_local(self, task: str | int | None, id: str | None, action:str, data=None) -> None:
            time, task_tag, type_tag, fdata = self.base_log(task, action, data)
            origin = self.origin if self.origin != 'client' else f'client {id}'
            
            s = f'{"{:<12}".format(time)} {task_tag} {type_tag} {"{:<24}".format(origin)} | {fdata}' 

            self.log_q.put(s)

      def log_list_data(self, data: list) -> None:
            for i in data:
                  s = (" " * 76) +i
                  self.log_q.put(s)

            self.log_q.put('\n')

      def send(self, task: str | int | None, id: str | None, receiver: str, action:str, data=None) -> None:
            time, task_tag, type_tag, fdata = self.base_log(task, action, data)
            origin = self.origin if self.origin != 'client' else f'client {id}'

            s = f'{"{:<12}".format(time)} {task_tag} {type_tag} {"{:<24}".format(f"{origin} -> {receiver}")} | {fdata}' 
            
            self.log_q.put(s)

      def recv(self, task: str | int | None, sender: str, action:str, data=None):
            time, task_tag, type_tag, fdata = self.base_log(task, action, data)

            s = f'{"{:<12}".format(time)} {task_tag} {type_tag} {"{:<24}".format(f"From {sender}")} | {fdata}' 
            
            self.log_q.put(s)
            

      def log_conn(self, receiver: str, data=None, task=None) -> None:
            time = datetime.now().strftime("%H:%M:%S.%f")[:-4]
            fdata = '' if task==None else "TASK {:<3} | ".format(task) + '; '.join(f"{k} = {v}" for k, v in data.items())

            log = "{:<12} [S-->C] | {:<10} | {:<10} -> {:<10}".format((time, 'SERVER', self.origin, receiver))

            s =("{:<68} |".format(log), fdata)

            self.log_q.put(s)
            
      def print_logs(self):
            while True:
                  msg = self.log_q.get()
                  print(msg)