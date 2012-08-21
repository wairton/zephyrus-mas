import zmq
ctx = zmq.Context()
socket = ctx.socket(zmq.SUB)
socket.connect('tcp://127.0.0.1:6601')
socket.setsockopt(zmq.SUBSCRIBE, 'amb')
for i in range(10):
    msg = socket.recv()
    print msg
