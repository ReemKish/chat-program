#!/usr/bin/env python
import socket
import sys
import queue
import time
try:
    import msvcrt
except ImportError:
    print("Platform not supported.")

#########################
DEFAULT_IP = '127.0.0.1'
DEFAULT_PORT = 8000  # port defaults to this if not given by the user
#########################


class Client:
    """Chat client. Connects to a chat server on a specific port.
    Instance attributes:
    username - client's username, will be displayed when sending messages.
    srv_soc - the socket connecting the client and the server.
    msg_que - queue of received messages waiting to be displayed.
    """

    BUFFER_SIZE = 1024  # how much data from a socket to read at a time.

    def __init__(self, username):
        """params:
        username - client's username, will be displayed when sending messages.
        admin - pass
        """
        self.username = username
        self.srv_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.msg_que = queue.Queue()

    def connect(self, ip, port):
        self.srv_soc.connect((ip, port))
        self.srv_soc.setblocking(0)
        self.srv_soc.send(self.username.encode())
        self.do()

    def do(self):
        while True:
            self.type_msg()
            self.recv_msgs()
            self.display_received_msgs()
            time.sleep(0.05)

    def type_msg(self):
        if msvcrt.kbhit() and msvcrt.getch() == b't':
            msg = input("... > ")
            self.send_msg(msg)

    def display_received_msgs(self):
        while not self.msg_que.empty():
            msg = self.msg_que.get()
            print(msg)

    def send_msg(self, msg):
        data = msg
        self.srv_soc.send(data.encode())

    def recv_msgs(self):
        try:
            data = self.srv_soc.recv(Client.BUFFER_SIZE).decode()
            if data:
                self.msg_que.put(data)
            else:  # connection is dead
                quit()
        except BlockingIOError:  # nothing to receive
            pass
        time.sleep(0.05)


def main():
    # Get username:
    try:
        username = sys.argv[1]
    except IndexError:  # no commandline args received
        username = input("Choose a username: ")
    # Get port (if supplied):
    try:
        port = 8000
    except Exception:
        port = DEFAULT_PORT
    print("Press T to start typing...")
    # Connect to server:
    client = Client(username)
    client.connect(DEFAULT_IP, port)


if __name__ == "__main__":
    main()
