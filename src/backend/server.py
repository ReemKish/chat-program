#!/usr/bin/env python

import sys
import socket
import threading
import time
import queue
from uuid import uuid4, UUID
from random import choice
import cpp
from group import Group, Member  # implemented in group.py
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Random import get_random_bytes
from pathlib import Path
import os

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

    BUFFER_SIZE = 1024
    MANAGER_NAMES = ["Alice", "Menny", "Reem"]  # these names automatically become managers
    COMMANDS = ["/help", "/quit", "/view-managers", "/tell", "/kick", "/promote", "/demote", "/mute", "/unmute"]
    COLORS = ["#aa0000", "#005500", "#00007f", "#aa007f", "#00557f", "#550000", "#b07500", "#00aa00"]

    def __init__(self):
        # Generate AES key to encrypt all communication with clients:
        self.aeskey = get_random_bytes(16)
        self.curr_file_desc = 0
        self.group = Group()
        self.accept_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.pending_que = queue.Queue()

    def start(self, port, ip='0.0.0.0'):
        self.accept_soc.bind((ip, port))
        self.accept_soc.listen(1)
        threading.Thread(target=self.accept_connections).start()
        while True:
            try:
                self.add_pending_member()
                self.do()
                time.sleep(0.05)
            except KeyboardInterrupt:
                pid = os.getpid()
                os.kill(pid, 9)

    def add_pending_member(self):
        try:
            conn = self.pending_que.get_nowait()
        except queue.Empty:  # no pending members to add
            return
        name = self.recv(conn, secure=False)
        time.sleep(0.5)
        pubkey = RSA.import_key(self.recv(conn, secure=False))
        if type(name) == str and name:
            name = name.strip()
            if name in self.group:
                cpp.send(conn, cpp.ServerMsg("Connection Refused: Name is already taken."))
                conn.close()
            else:
                enc_aeskey = PKCS1_OAEP.new(pubkey).encrypt(self.aeskey)
                cpp.send(conn, enc_aeskey)
                color = choice(Server.COLORS)
                self.group.add(name, pubkey, conn, color, name in self.MANAGER_NAMES)
                self.broadcast(cpp.ServerMsg(f"{self.group[name]} joined the chat."))
                self.unicast(self.group[name], cpp.ServerMsg("Tip: Type /help to display available commands."))
                if len(self.group) == 1:  # make first member to join the chat a manager
                    self.group[name].is_manager = True

    def accept_connections(self):
        while True:
            conn, _ = self.accept_soc.accept()
            conn.setblocking(0)
            self.pending_que.put(conn)
            time.sleep(0.1)

    def unicast(self, member, cpp_msg):
        """send a CPP message to a specific member.
        """
        try:
            cpp.ssend(member.conn, self.aeskey, cpp_msg)
        except socket.error:  # connection has likely been closed
            self.group.kick(member)
            self.broadcast(cpp.ServerMsg(f"{member.name} left the chat."))

    def broadcast(self, cpp_msg, exclude=[]):
        """send a message to all members, possibly excluding some.
        """
        for member in self.group:
            if member not in exclude:
                self.unicast(member, cpp_msg)

    def recv(self, origin, secure=True):
        if type(origin) is Member:
            origin = origin.conn
        if secure:
            return cpp.srecv(origin, self.aeskey)
        else:
            return cpp.recv(origin)

    def handle(self, member, cpp_msg):
        if type(cpp_msg) is cpp.Cmd:
            self.execute_command(member, cpp_msg)
        elif type(cpp_msg) is str and not member.is_muted:
            if cpp_msg.startswith("DOWNLOAD:"):
                file_descriptor = int(cpp_msg.split(':', 1)[1])
                self.send_file(member, file_descriptor)
                return
            if cpp_msg.startswith("FILE:"):
                filepath = cpp_msg.split(':', 1)[1]
                self.curr_file_desc += 1
                cpp_msg = f"FILE:{self.curr_file_desc}:{filepath}"
            self.broadcast(cpp.ServerMsg(cpp_msg, name=member.name), exclude=[member])
            self.unicast(member, cpp.ServerMsg(cpp_msg, name=member.name))
        elif type(cpp_msg) is cpp.FileAttachSend:
            uuid = uuid4()
            attachment = cpp.FileAttachRecv(cpp_msg.filename, member.name, uuid)
            self.broadcast(attachment, exclude=[member])
            self.unicast(member, attachment)
        elif type(cpp_msg) is cpp.FileAttachRecv:
            print("recv")
        elif type(cpp_msg) is bytes:
            self.download_file(cpp_msg)
        elif member.is_muted:
            self.unicast(member, cpp.ServerMsg("Error - You are muted, message was not sent."))

    def send_file(self, member, file_descriptor):
        filepath = f"./data/{file_descriptor}"
        with open(filepath, 'rb') as file:
            data = file.read()
            file.close()
        self.unicast(member, data)

    def download_file(self, data):
        Path(f"./data").mkdir(parents=True, exist_ok=True)
        file = open(f"./data/{self.curr_file_desc}", 'wb')
        file.write(data)
        file.close()

    def execute_command(self, executer, cmd):

        if not executer.is_manager and cmd.cmd in [cpp.DataType.CMD_KICK.value, cpp.DataType.CMD_PROMOTE.value, cpp.DataType.CMD_DEMOTE.value,
                                                   cpp.DataType.CMD_MUTE.value, cpp.DataType.CMD_UNMUTE.value]:
            # executer is not a manager but tries to use manager-only commands
            self.unicast(executer, cpp.ServerMsg("Error - Permission denied."))
        elif cmd.cmd == cpp.DataType.CMD_HELP.value:
            self.execute_help(executer)
        elif cmd.cmd == cpp.DataType.CMD_QUIT.value:
            self.execute_quit(executer)
        elif cmd.cmd == cpp.DataType.CMD_VIEW.value:
            self.execute_view_managers(executer)
        elif cmd.cmd == cpp.DataType.CMD_LIST.value:
            self.execute_list(executer)
        elif cmd.name not in self.group:
            self.unicast(executer, cpp.ServerMsg(f"Error - '{cmd.name}' is not in the group."))
        elif cmd.cmd == cpp.DataType.CMD_TELL.value:
            self.execute_tell(executer, cmd.name, cmd.msg)
        elif cmd.cmd == cpp.DataType.CMD_KICK.value:
            self.execute_kick(cmd.name)
        elif cmd.cmd == cpp.DataType.CMD_PROMOTE.value:
            self.execute_promote(cmd.name)
        elif cmd.cmd == cpp.DataType.CMD_DEMOTE.value:
            self.execute_demote(cmd.name)
        elif cmd.cmd == cpp.DataType.CMD_MUTE.value:
            self.execute_mute(cmd.name)
        elif cmd.cmd == cpp.DataType.CMD_UNMUTE.value:
            self.execute_unmute(cmd.name)
        else:
            self.unicast(executer, cpp.ServerMsg("Error - Invalid input, try /help."))

    def execute_help(self, executer):
        self.unicast(executer, cpp.ServerMsg(self.help_html()))

    def execute_quit(self, executer):
        self.broadcast(cpp.ServerMsg(f"{executer.name} left the chat."))
        self.group.kick(executer)

    def execute_view_managers(self, executer):
        manager_list = map(lambda memb: str(memb), filter(lambda memb: memb.is_manager, self.group))
        self.unicast(executer, cpp.ServerMsg(f'''
            <p style='text-align:center'>
                <u>Managers</u>
                <p>{'<br />'.join(manager_list)}</p>
            </p> 
            '''))
    
    def execute_list(self, executer):
        user_list = map(lambda memb: str(memb), self.group)
        self.unicast(executer, cpp.ServerMsg(f'''
            <p style='text-align:center'>
                <u>Online Users</u>
                <p>{'<br />'.join(user_list)}</p>
            </p> 
            '''))

    def execute_tell(self, executer, name, msg):
        if executer.is_muted:
            self.unicast(executer, cpp.ServerMsg("Error - You are muted, message was not sent."))
        elif name in self.group:
            self.unicast(executer, cpp.ServerMsg(f"{executer.name} -> {self.group[name].name}: {msg}"))
            self.unicast(self.group[name], cpp.ServerMsg(f"{executer.name} -> {self.group[name].name}: {msg}"))

    def execute_kick(self, name):
        if name in self.group:
            self.broadcast(cpp.ServerMsg(f"{self.group[name].name} has been kicked from the group."), exclude=[self.group[name]])
            self.unicast(self.group[name], cpp.ServerMsg("You have been kicked from the group."))
            self.group.kick(name)

    def execute_promote(self, name):
        if name in self.group and not self.group[name].is_manager:
            self.unicast(self.group[name], cpp.ServerMsg("You are now a manager."))
            self.group[name].is_manager = True

    def execute_demote(self, name):
        if name in self.group and self.group[name].is_manager:
            self.unicast(self.group[name], cpp.ServerMsg("You are no longer a manager."))
            self.group[name].is_manager = False

    def execute_mute(self, name):
        if name in self.group and not self.group[name].is_muted:
            self.unicast(self.group[name], cpp.ServerMsg("You have been muted by a manager."))
            self.group[name].is_muted = True

    def execute_unmute(self, name):
        if name in self.group and self.group[name].is_muted:
            self.unicast(self.group[name], cpp.ServerMsg("You are no longer muted."))
            self.group[name].is_muted = False

    def do(self):
        for member in self.group:
            if member.conn.fileno() == -1:
                self.group.kick(member)
            else:
                try:
                    cpp_msg = self.recv(member)
                    if cpp_msg is not None:
                        self.handle(member, cpp_msg)
                except ConnectionError:
                    self.group.kick(member)
                

    def help_html(self):
        return \
            f'''<html><head /><body>
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
