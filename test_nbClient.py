import socket
import errno

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setblocking(False)
      
try:
      sock.connect_ex(("127.0.0.1", 55000))  # connect_ex doesn't raise on EINPROGRESS
      
except BlockingIOError as e:
      if e.errno == errno.EAGAIN:
            # No data available right now; try again later
            pass

state = "Connecting"


