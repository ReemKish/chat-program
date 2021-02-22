#!/usr/bin/env python
import socket
import sys
import queue
import struct

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

    COMMANDS = ["/help", "/quit", "/view-managers", "/tell", "/kick", "/promote", "/demote", "/mute", "/unmute"]
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
        self.send(self.username)

    def send(self, msg):
        self.srv_soc.send(struct.pack('>I', len(msg)) + msg.encode())

    def recv(self):
        packet = self.recv_raw()
        if packet:
            return packet.decode()

    def recv_raw(self):
        raw_msglen = self.recvn(4)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        return self.recvn(msglen)

    def recvn(self, n):
        """Returns n bytes of the server socket data.
        """
        data = bytearray()
        while len(data) < n:
            packet = self.srv_soc.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data


def main():
    # Get username:
    try:
        username = sys.argv[1]
    except IndexError:  # no commandline args received
        username = input("Choose a username: ")
    # Get port (if supplied):
    try:
        port = int(sys.argv[2])
    except Exception:
        port = DEFAULT_PORT
    print("Press T to start typing...")
    # Connect to server:
    client = Client(username)
    client.connect(DEFAULT_IP, port)


if __name__ == "__main__":
    main()
