import socket
import select


HOST = '127.0.0.1'
PORT = 55000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
      server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
except AttributeError:
      pass

server.bind((HOST, PORT))
server.listen(50)
server.setblocking(False)

inputs = [server]
outputs = []

readable, writable, exceptional = select.select(inputs, outputs, inputs, 1.0)

message_queues: dict[socket.socket, list[bytes]] = {}

print(f"Non-blocking server on {HOST}:{PORT}")

while inputs:
    # select() returns readable, writable, exceptional sockets
    # Timeout of 1 second prevents indefinite blocking
    readable, writable, exceptional = select.select(inputs, outputs, inputs, 100)

    for sock in readable:
        if sock is server:
            # New incoming connection
            conn, addr = server.accept()
            print(f"New connection from {addr}")
            conn.setblocking(False)
            inputs.append(conn)
            message_queues[conn] = []
        else:
            # Existing client has data
            try:
                data = sock.recv(4096)
                if data:
                    # Queue response to be sent when socket is writable
                    message_queues[sock].append(data)
                    if sock not in outputs:
                        outputs.append(sock)
                else:
                    # Empty data = client disconnected
                    print(f"Client disconnected")
                    inputs.remove(sock)
                    if sock in outputs:
                        outputs.remove(sock)
                    del message_queues[sock]
                    sock.close()
            except ConnectionResetError:
                inputs.remove(sock)
                sock.close()

    for sock in writable:
        if message_queues.get(sock):
            # Send the next queued message
            msg = message_queues[sock].pop(0)
            sock.send(msg)
        else:
            # Nothing to send; stop watching for writability
            outputs.remove(sock)

    for sock in exceptional:
        print(f"Exception on socket {sock.getpeername()}")
        inputs.remove(sock)
        if sock in outputs:
            outputs.remove(sock)
        del message_queues[sock]
        sock.close()