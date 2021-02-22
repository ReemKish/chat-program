#!/usr/bin/env python

import sys
import socket
import threading
import time
import queue
import struct
from random import choice
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
    MANAGER_NAMES = ["Alice", "Menny", "Reem"]  # these automatically become managers
    COMMANDS = ["/help", "/quit", "/view-managers", "/tell", "/kick", "/promote", "/demote", "/mute", "/unmute"]
    COLORS = ["#aa0000", "#005500", "#00007f", "#aa007f", "#00557f", "#550000", "#b07500", "#00aa00"]

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
            if name in self.group:
                msg = "Connection Refused: Name is already taken."
                conn.send(struct.pack('>I', len(msg)) + msg.encode())
                conn.close()
            else:
                color = choice(Server.COLORS)
                self.group.add(name, conn, color, name in self.MANAGER_NAMES)
                self.broadcast(self.servermsg_to_html(f"{self.group[name]} joined the chat.", time.strftime('%H:%M')))
                self.unicast(self.group[name], self.servermsg_to_html("Tip: Type /help to display available commands.", time.strftime('%H:%M')))
                if len(self.group) == 1:  # make first member to join the chat a manager
                    self.group[name].is_manager = True
                print("#DEBUG# added member " + name + " #members = " + str(len(self.group)))

    def accept_connections(self):
        while True:
            conn, _ = self.accept_soc.accept()
            conn.setblocking(0)
            self.pending_que.put(conn)
            print(
                "#DEBUG# accepted connection. #pending_connections = " + str(self.pending_que.qsize()))
            time.sleep(0.05)

    def unicast(self, member, msg):
        """send a message to a specific member.
        prefixes the msg with a 4-byte length.
        """
        try:
            member.conn.send(struct.pack('>I', len(msg)) + msg.encode())
        except socket.error:  # connection has likely been closed
            self.group.kick(member)
            self.broadcast(self.servermsg_to_html(f"{member.name} left the chat.", time.strftime('%H:%M')))

    def broadcast(self, msg, exclude=[]):
        """send a message to all members, possibly excluding some.
        """
        for member in self.group:
            if member not in exclude:
                self.unicast(member, msg)

    def recv(self, origin):
        if type(origin) is Member:
            origin = origin.conn
        try:
            return self.recv_raw(origin).decode()
        except socket.error:  # connection has likey been closed
            return None

    def recv_raw(self, origin):
        raw_msglen = self.recvn(origin, 4)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        return self.recvn(origin, msglen)

    def recvn(self, origin, n):
        """Returns n bytes of the server socket data.
        """
        data = bytearray()
        while len(data) < n:
            packet = origin.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data

    def handle(self, member, msg):
        if msg[0] == "/":
            self.execute_command(member, msg[1:].strip())
        elif not member.is_muted:
            self.broadcast(self.usermsg_to_html(member.name, msg, time.strftime('%H:%M'), member.color), exclude=[member])
            self.unicast(member, self.selfmsg_to_html(msg, time.strftime('%H:%M')))
        else:
            self.unicast(member, self.servermsg_to_html("Error - You are muted, message was not sent.", time.strftime('%H:%M')))

    def execute_command(self, executer, commandline):
        args = commandline.split(" ")
        command, args = args[0].lower(), args[1:]
        if not executer.is_manager and command in ["kick", "promote", "demote", "mute", "unmute"]:
            # executer is not a manager but tries to use manager-only commands
            self.unicast(executer, self.servermsg_to_html("Error - Permission denied.", time.strftime('%H:%M')))
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
            self.unicast(executer, self.servermsg_to_html("Error - Invalid input, try /help.", time.strftime('%H:%M')))

    def execute_help(self, executer):
        self.unicast(executer, self.help_html(time.strftime('%H:%M')))

    def execute_quit(self, executer):
        self.broadcast(self.servermsg_to_html(f"{executer.name} left the chat.", time.strftime('%H:%M')))
        self.group.kick(executer)

    def execute_view_managers(self, executer):
        self.unicast(executer, self.servermsg_to_html("Managers: " + ", ".join(map(lambda m: str(m), filter(lambda m: m.is_manager, self.group))), time.strftime('%H:%M')))

    def execute_tell(self, executer, name, msg):
        if executer.is_muted:
            self.unicast(executer, self.servermsg_to_html("Error - You are muted, message was not sent.", time.strftime('%H:%M')))
        elif name in self.group:
            self.unicast(executer, self.servermsg_to_html(f"{executer.name} -> {self.group[name].name}: {msg}", time.strftime('%H:%M')))
            self.unicast(self.group[name], self.servermsg_to_html(f"{executer.name} -> {self.group[name].name}: {msg}", time.strftime('%H:%M')))

    def execute_kick(self, names):
        for name in filter(lambda name: name in self.group, names):
            self.broadcast(self.servermsg_to_html(f"{self.group[name].name} has been kicked from the group.", time.strftime('%H:%M')), exclude=[self.group[name]])
            self.unicast(self.group[name], self.servermsg_to_html("You have been kicked from the group.", time.strftime('%H:%M')))
            self.group.kick(name)

    def execute_promote(self, names):
        for name in filter(lambda name: name in self.group and not self.group[name].is_manager, names):
            self.unicast(self.group[name], self.servermsg_to_html("You are now a manager.", time.strftime('%H:%M')))
            self.group[name].is_manager = True

    def execute_demote(self, names):
        for name in filter(lambda name: name in self.group and self.group[name].is_manager, names):
            self.unicast(self.group[name], self.servermsg_to_html("You are no longer a manager.", time.strftime('%H:%M')))
            self.group[name].is_manager = False

    def execute_mute(self, names):
        for name in filter(lambda name: name in self.group and not self.group[name].is_muted, names):
            self.unicast(self.group[name], self.servermsg_to_html("You have been muted by a manager.", time.strftime('%H:%M')))
            self.group[name].is_muted = True

    def execute_unmute(self, names):
        for name in filter(lambda name: name in self.group and self.group[name].is_muted, names):
            self.unicast(self.group[name], self.servermsg_to_html("You are no longer muted.", time.strftime('%H:%M')))
            self.group[name].is_muted = False

    def do(self):
        for member in self.group:
            msg = self.recv(member)
            if msg:
                self.handle(member, msg)

    def usermsg_to_html(self, name, msg, time, color="#000000"):
        msg = msg.replace('font-size:', '')
        return \
            f'''MESG</head>
<body style=" font-family:\'Sans Serif\'; font-size:9pt; font-weight:400; font-style:normal;">\n<p
style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">
<span style=" color:{color};">{name}</span></p>\n{msg}\n<p align="right"
style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">
<span style=" font-size:7pt; color:#353535;">{time}</span></p>
</body>
</html>'''

    def selfmsg_to_html(self, msg, time):
        msg = msg.replace('font-size:', '')
        return \
            f'''SELF</head>
<body style=" font-family:\'Sans Serif\'; font-size:9pt; font-weight:400; font-style:normal;">
</p>{msg}<p align="right"
style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">
<span style=" font-size:7pt; color:#353535;">{time}</span></p>
</body>
</html>'''

    def servermsg_to_html(self, msg, time):
        return \
            f'''SERV</head>
<body style=" font-family:\'Sans Serif\'; font-size:9pt; font-weight:400; font-style:normal;">
</p>{msg}<p align="right"
style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">
<span style=" font-size:7pt; color:#353535;">{time}</span></p>
</body>
</html>'''

    def help_html(self, time):
        return \
            f'''SERV<html><head /><body>
        <p>List of commands:</p>
        <p><span style=" font-weight:600;">/help</span> - display this text.</p>
        <p><span style=" font-weight:600;">/quit</span> - quit the chat group.</p>
        <p><span style=" font-weight:600;">/view-managers</span> - view all members with manager permissions.</p>
        <p><span style=" font-weight:600;">/tell</span><span style=" font-style:italic;"> [name] [msg]</span> - send a
                private message to a member.</p>
        <p><span style=" font-weight:600; text-decoration: underline;">/kick</span><span
                        style=" font-style:italic;"> [name]</span> - remove a member from the chat group.</p>
        <p><span style=" font-weight:600; text-decoration: underline;">/promote</span><span
                        style=" font-style:italic;"> [name]</span> - give a member manager permissions.</p>
        <p><span style=" font-weight:600; text-decoration: underline;">/demote</span><span
                        style=" font-style:italic;"> [name]</span> - take a member's manager permissions.</p>
        <p><span style=" font-weight:600; text-decoration: underline;">/mute</span><span
                        style=" font-style:italic;"> [name]</span> - make a member unable to send messages.</p>
        <p><span style=" font-weight:600; text-decoration: underline;">/unmute</span><span
                        style=" font-style:italic;"> [name]</span> - make a member able to send messages.</p>
        <p>* Underlined commands require manager permissions.</p>
        <p align="right"><span style=" font-size:7pt; color:#000000;">{time}</span></p>
        </body></html>'''


def main():
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = DEFAULT_PORT
    print(f"Running chat server on port {port}")
    server = Server()
    server.start(port, ip=LISTEN_IP)


if __name__ == "__main__":
    main()
