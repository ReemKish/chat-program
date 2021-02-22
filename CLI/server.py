#!/usr/bin/env python

import sys
import socket
import threading
import time
import queue
from group import Group, Member  # implemented in group.py

#########################
DEFAULT_PORT = 8000  # port defaults to this if not given by the user
LISTEN_IP = '0.0.0.0'  # IP to listen from ('0.0.0.0' for any ip)
#########################


class Server:
    """Chat server. Listens to requests from any IP on a specific port.
    Instance attributes:
    group - (instance of Group) group of the current chat members.
    accept_soc - the socket used to accept new connections.
    pending_que - queue of newly accepted connections.

    """

    BUFFER_SIZE = 1024  # how much data from a socket to read at a time.
    # Any member that connects with one of the following usernames is automatically granted manager permissions:
    MANAGER_NAMES = ["Alice", "Menny", "Reem"]

    def __init__(self):
        self.group = Group()
        self.accept_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.pending_que = queue.Queue()

    def start(self, port, ip='0.0.0.0'):
        self.accept_soc.bind((ip, port))
        self.accept_soc.listen(1)
        threading.Thread(target=self.accept_connections).start()
        while True:
            # print("Got: ")
            self.add_pending_member()
            self.do()
            time.sleep(0.05)

    def add_pending_member(self):
        try:
            conn = self.pending_que.get_nowait()
        except queue.Empty:  # no pending members to add
            return
        name = self.recv(conn)
        if name:
            name = name.strip()
            if name[0] == '@':
                conn.send(
                    "Connection Refused: Username must not begin with '@'.".encode())
                conn.close()
            if name in self.group:
                conn.send(
                    "Connection Refused: Username is already taken.".encode())
                conn.close()
            else:
                self.group.add(name, conn, name in self.MANAGER_NAMES)
                self.broadcast(
                    f"{time.strftime('%H:%M')} {self.group[name]} joined the chat.")
                self.unicast(
                    self.group[name], f"\n{time.strftime('%H:%M')} [Server] Tip: Type /help to display available commands.")
                print("#DEBUG# added member " + name +
                      " #members = " + str(len(self.group)))

    def accept_connections(self):
        while True:
            conn, _ = self.accept_soc.accept()
            conn.setblocking(0)
            self.pending_que.put(conn)
            print(
                "#DEBUG# accepted connection. #pending_connections = " + str(self.pending_que.qsize()))
            time.sleep(0.05)

    def encode(self, msg):
        """Returns an encoded message that fits the protocol's format.
        """
        data = msg
        return data.encode()

    def unicast(self, member, msg):
        """send a message to a specific member.
        """
        try:
            member.conn.send(msg.encode())
        except socket.error:  # connection has likey been closed
            self.group.kick(member)
            self.broadcast(
                f"\n{time.strftime('%H:%M')} {member.dname} left the chat.")

    def broadcast(self, msg, exclude=[]):
        """send a message to all members, possibly excluding some.
        """
        for member in self.group:
            if member not in exclude:
                self.unicast(member, msg)

    def recv(self, origin):
        """Returns received data from either a connection or a member.
        """
        if type(origin) is Member:
            origin = origin.conn
        try:
            return origin.recv(Server.BUFFER_SIZE).decode()
        except socket.error:  # connection has likey been closed
            return None

    def handle(self, member, msg):
        if msg[0] == "/":
            self.execute_command(member, msg[1:].strip())
        elif not member.is_muted:
            self.broadcast(
                f"{time.strftime('%H:%M')} {member.dname}: {msg}")
        else:
            self.unicast(
                member, "Error - You are muted, message was not sent.")

    def execute_command(self, executer, commandline):
        args = commandline.split(" ")
        command, args = args[0].lower(), args[1:]
        if not executer.is_manager and command in ["kick", "promote", "demote", "mute", "unmute"]:
            # executer is not a manager but tries to use manager-only commands
            self.unicast(executer, "Error - Permission denied.")
        elif command == "help":
            self.execute_help(executer)
        elif command == "quit":
            self.execute_quit(executer)
        elif command == "view-managers":
            self.execute_view_managers(executer)
        elif command == "tell" and len(args) >= 2:
            self.execute_tell(executer, args[0], ' '.join(args[1:]))
        elif command == "kick" and len(args) >= 1:
            self.execute_kick(args)
        elif command == "promote" and len(args) == 1:
            self.execute_promote(args)
        elif command == "demote" and len(args) == 1:
            self.execute_demote(args)
        elif command == "mute" and len(args) == 1:
            self.execute_mute(args)
        elif command == "unmute" and len(args) == 1:
            self.execute_unmute(args)
        else:
            self.unicast(executer, "Error - Invalid input, try /help.")

    def execute_help(self, executer):
        self.unicast(
            executer, "List of commands:\n  /help - display this text.\n  /quit - quit the chat group.\n  /view-managers - view all members with manager permissions.\n  /tell [name] [msg] - send a private message to a member.\n* /kick [name] - remove a member from the chat group.\n* /promote [name] - give a member manager permissions.\n* /demote [name] - take a member's manager permissions.\n* /mute [name] - make a member unable to send messages.\n* /unmute  [name] - make a member able to send messages.\n- commands marked with * require manager permissions.")

    def execute_quit(self, executer):
        self.broadcast(
            f"{time.strftime('%H:%M')} {executer.dname} left the chat.")
        self.group.kick(executer)

    def execute_view_managers(self, executer):
        self.unicast(executer, "Managers: " +
                     ", ".join(map(lambda m: str(m), filter(lambda m: m.is_manager, self.group))))

    def execute_tell(self, executer, name, msg):
        if executer.is_muted:
            self.unicast(
                executer, "Error - You are muted, message was not sent.")
        elif name in self.group:
            self.unicast(
                executer, f"{time.strftime('%H:%M')} ! {executer.dname} -> {self.group[name].dname}: {msg}")
            self.unicast(
                self.group[name], f"{time.strftime('%H:%M')} ! {executer.dname} -> {self.group[name].dname}: {msg}")

    def execute_kick(self, names):
        for name in filter(lambda name: name in self.group, names):
            self.broadcast(
                f"{time.strftime('%H:%M')} {self.group[name].dname} has been kicked from the group.", exclude=[self.group[name]])
            self.unicast(
                self.group[name], f"{time.strftime('%H:%M')} You have been kicked from the group.")
            self.group.kick(name)

    def execute_promote(self, names):
        for name in filter(lambda name: name in self.group and not self.group[name].is_manager, names):
            self.unicast(
                self.group[name], f"{time.strftime('%H:%M')} [Server] You are now a manager.")
            self.group[name].is_manager = True

    def execute_demote(self, names):
        for name in filter(lambda name: name in self.group and self.group[name].is_manager, names):
            self.unicast(
                self.group[name], f"{time.strftime('%H:%M')} [Server] You are no longer a manager.")
            self.group[name].is_manager = False

    def execute_mute(self, names):
        for name in filter(lambda name: name in self.group and not self.group[name].is_muted, names):
            self.unicast(
                self.group[name], f"{time.strftime('%H:%M')} [Server] You have been muted by a manager.")
            self.group[name].is_muted = True

    def execute_unmute(self, names):
        for name in filter(lambda name: name in self.group and self.group[name].is_muted, names):
            self.unicast(
                self.group[name], f"{time.strftime('%H:%M')} [Server] You are no longer muted.")
            self.group[name].is_muted = False

    def do(self):
        for member in self.group:
            msg = self.recv(member)
            if msg:
                self.handle(member, msg)


def main():
    if len(sys.argv) > 1:
        port = 8000
    else:
        port = DEFAULT_PORT
    print(f"Running chat server on port {port}")
    server = Server()
    server.start(port, ip=LISTEN_IP)


if __name__ == "__main__":
    main()
