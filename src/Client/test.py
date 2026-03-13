import threading

stop_event = threading.Event()

def background_task():
    while not stop_event.is_set():
        print('Hellow!')
        stop_event.wait(2.0)

thread = threading.Thread(target=background_task, daemon=True)
thread.start()

while True:
    x = input('something here:')
    print(x)

    if x == 'cancel':
        stop_event.set()
        break
