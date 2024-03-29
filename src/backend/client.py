#!/usr/bin/env python
import sys
import socket
import queue
import struct
from time import sleep
from time import gmtime, strftime, struct_time
from Crypto.PublicKey import RSA
from backend import cpp


#########################
DEFAULT_IP = '127.0.0.1'
DEFAULT_PORT = 8000  # port defaults to this if not given by the user
#########################


class Client:
    """Chat client. Connects to a chat server on a specific port.
    Instance attributes:
    name - client's name, will be displayed when sending messages.
    srv_soc - the socket connecting the client and the server.
    msg_que - queue of received messages waiting to be displayed.
    """

    COMMANDS = {"/help": cpp.DataType.CMD_HELP.value,
                "/quit": cpp.DataType.CMD_QUIT.value,
                "/view-managers": cpp.DataType.CMD_VIEW.value,
                "/list": cpp.DataType.CMD_LIST.value,
                "/tell": cpp.DataType.CMD_TELL.value,
                "/kick": cpp.DataType.CMD_KICK.value,
                "/promote": cpp.DataType.CMD_PROMOTE.value,
                "/demote": cpp.DataType.CMD_DEMOTE.value,
                "/mute": cpp.DataType.CMD_MUTE.value,
                "/unmute": cpp.DataType.CMD_UNMUTE.value}
    BUFFER_SIZE = 1024  # how much data from a socket to read at a time.

    def __init__(self, name):
        """params:
        name - client's name, will be displayed when sending messages.
        """
        # Generate RSA private and public key:
        self.privkey = RSA.generate(1024)
        self.pubkey = self.privkey.public_key()
        self.aeskey = None  # used to encrypt session, will be sent by the server upon connection

        self.name = name
        self.srv_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.msg_que = queue.Queue()

    def connect(self, ip, port):
        self.srv_soc.connect((ip, port))
        self.send(self.name)
        self.send(self.pubkey.export_key().decode())

    def send(self, cpp_msg):
        """send a CPP message to the server.
        """
        cpp.send(self.srv_soc, cpp_msg)

    def ssend(self, cpp_msg):
        """send a CPPS message to the server.
        receives CPPS msg and encrpyts it
        """
        cpp.ssend(self.srv_soc, self.aeskey, cpp_msg)

    def recv(self):
        return cpp.recv(self.srv_soc)

    def srecv(self):
        return cpp.srecv(self.srv_soc, self.aeskey)



def main():
    # Get name:
    try:
        name = sys.argv[1]
    except IndexError:  # no commandline args received
        name = input("Choose a name: ")
    # Get port (if supplied):
    try:
        port = int(sys.argv[2])
    except Exception:
        port = DEFAULT_PORT
    print("Press T to start typing...")
    # Connect to server:
    client = Client(name)
    client.connect(DEFAULT_IP, port)
    while True:
        msg = input("> ")
        client.send(msg)
        response = client.recv()
        print(f"{strftime('%H:%M',gmtime(response.timestamp))} {response.name}: {response.msg}")
        # print(response.msg)


if __name__ == "__main__":
    main()
