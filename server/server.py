from twisted.internet.protocol import Protocol, Factory
from twisted.python import failure
from twisted.internet import error
from threading import Thread
import json
import random
import os
from config import *
from _thread import start_new_thread
import multiprocessing
import time
import sys

connectionDone = failure.Failure(error.ConnectionDone())


class TCP(Protocol, Thread):
    solution_timeout = 30
    mistakes_freq = 8

    def __init__(self):
        self.user = None
        self.check_img = '1.jpg'
        self.solution_run = False
        self.receiving = False
        self.last_data_receive = 0
        super().__init__(target=self.solution_starter)
        self.start()

    def dataReceived(self, data):
        if b'request' in data:
            try:
                message = json.loads(data.decode('utf-8'))
                request = message['request']
                data = message['data']
            except (UnicodeDecodeError, ValueError, KeyError):
                self.send({"response": "error", "data": "Bad request"})
                return
            if request == 'auth':
                self.user = data
                self.send({"response": "auth_ok", "data": data})
                return
            self.send({"response": "unknown_command", "data": request})
            return

        if not self.user:
            self.send({"response": "error", "data": "Auth first"})
            return

        if self.solution_run:
            self.send({"response": "error", "data": "Solution already run"})
            return

        if not os.path.exists('solutions/' + self.user + '/'):
            self.send({"response": "error", "data": "Solution first"})
            return

        data = self.set_mistakes(data)
        with open('solutions/' + self.user + '/' + 'input', 'r+b') as f:
            f.write(data)
        print('part received')
        self.receiving = True
        self.last_data_receive = time.time()

    def solution_starter(self):
        while True:
            if self.receiving and (time.time() - self.last_data_receive > 2):
                self.receiving = False
                start_new_thread(self.run_solution, tuple())
            time.sleep(0.5)

    def send(self, data):
        if not data:
            return
        self.transport.write((json.dumps(data) + '\n').encode('utf-8'))

    def run_solution(self):
        self.solution_run = True
        pool = multiprocessing.Pool(1)
        code = pool.apply_async(os.system, ('python solutions/' + self.user + '/' + self.user + '.py',))
        code = code.get(self.solution_timeout)
        if code:
            self.solution_run = False
            self.send({"response": "solution_error", "data": code})
            return
        self.check()

    def check(self):
        with open('solutions/' + self.user + '/' + 'output', 'rb') as f:
            out = f.read()
        with open('check/' + self.check_img, 'rb') as f:
            img = f.read()

        errors = 0
        for i in min(out, img, key=lambda x: len(x)):
            if out[i] != img[i]:
                errors += 1
        err = (1 - errors / len(img)) * 100
        self.send({"response": "img_received", "data": round(err, 3)})

        with open('solutions/' + self.user + '/' + 'output', 'wb') as f:
            f.write(b'')
        with open('solutions/' + self.user + '/' + 'input', 'wb') as f:
            f.write(b'')

        self.solution_run = False

    def set_mistakes(self, data):
        data = list(data)
        for i in range(len(data)):
            byte = list(self.get_bin(data[i]))
            for j in range(len(byte)):
                if random.randint(0, self.mistakes_freq) == 0:
                    byte[j] = str(random.randint(0, 1))
            data[i] = int(''.join(byte), 2)
        return bytes(data)

    @staticmethod
    def get_bin(num):
        return (8 - len(bin(num)[2:])) * '0' + bin(num)[2:]


class Server(Thread):
    def __init__(self, ip='0.0.0.0', port=TCP_PORT):
        from twisted.internet import reactor

        self.ip = ip
        self.port = port

        self.reactor = reactor
        f = Factory()
        f.protocol = TCP
        reactor.listenTCP(port, f)
        super().__init__()

    def run(self):
        print('Start at %s:%s' % (self.ip, self.port))
        self.reactor.run()


if __name__ == '__main__':
    s = Server()
    s.run()
