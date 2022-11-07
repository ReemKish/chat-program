# CPP - Chat Program Protocol
# Methods for receiving and sending message in CPP protocol
# CPP specifications are at chat_program_protocol.txt

import enum
import socket
import struct
from time import time
from Crypto.Cipher import AES
from uuid import uuid4, UUID  # random uuid


class DataType(enum.Enum):
    MSG = 0
    SERVERMSG = 1
    BYTES = 2
    FILE_PART = 3
    FILE_ATTACH_SEND = 4
    FILE_ATTACH_RECV = 5
    MASK_CMD = 128  # mask to filter command data types

    CMD_TELL = 128

    MASK_CMD_ONEARG = 160  # mask to filter commands with one argument
    CMD_KICK = 160
    CMD_PROMOTE = 161
    CMD_DEMOTE = 162
    CMD_MUTE = 163
    CMD_UNMUTE = 164

    MASK_CMD_NOARGS = 192  # mask to filter commands without arguments
    CMD_HELP = 192
    CMD_QUIT = 193
    CMD_VIEW = 194  # view managers
    CMD_LIST = 195  # list users


def encode(cpp_msg):
    if type(cpp_msg) is bytes: data = cpp_msg
    elif type(cpp_msg) is str: data = cpp_msg.encode()
    else: data = cpp_msg.get_data()
    datasize = len(data)
    if type(cpp_msg) is str: datatype = DataType.MSG.value
    elif type(cpp_msg) is bytes: datatype = DataType.BYTES.value
    elif type(cpp_msg) is ServerMsg: datatype = DataType.SERVERMSG.value
    elif type(cpp_msg) is Cmd: datatype = cpp_msg.cmd
    elif type(cpp_msg) is FileAttachSend: datatype = DataType.FILE_ATTACH_SEND.value
    elif type(cpp_msg) is FileAttachRecv: datatype = DataType.FILE_ATTACH_RECV.value
    elif cpp_msg is None: datatype = cpp_msg = Cmd(DataType.CMD_QUIT)  # Quit
    return struct.pack('>BI', datatype, datasize) + data

def send(sock, cpp_msg):
    """encodes a string or a Cmd object cpp_msg into raw data and sends it through sock"""
    sock.send(encode(cpp_msg))


def recv(sock):
    """Returns a string or ServerMsg or CPPCmd object decoded from the raw data in sock
    """
    try:
        datatype, data = _recv_raw(sock)
        return construct_cpp_msg(datatype, data)
    except socket.error:  # connection has likely been closed
        return None

def construct_cpp_msg(datatype, data):
    """Constructs and returns a string or ServerMsg or CPPCmd object decoded from the datatype and data
    """
    if datatype is None: return None
    if datatype == DataType.MSG.value:
        return data.decode()
    elif datatype == DataType.BYTES.value:
        return data
    elif datatype == DataType.SERVERMSG.value:
        return ServerMsg.decode(data)
    elif datatype & DataType.MASK_CMD.value == DataType.MASK_CMD.value:  # data is a command
        return Cmd.decode(datatype, data)
    elif datatype == DataType.FILE_ATTACH_SEND.value:
        return FileAttachSend.decode(data)
    elif datatype == DataType.FILE_ATTACH_RECV.value:
        return FileAttachRecv.decode(data)
    else:
        return None  # invalid datatype


def _recv_raw(sock):
    raw_datasize_and_datatype = _recvn(sock, 5)
    if not raw_datasize_and_datatype:
        return None, None
    datatype, datasize = struct.unpack('>BI', raw_datasize_and_datatype)
    data = _recvn(sock, datasize)
    return datatype, data


def _recvn(sock, n):
    """Returns n bytes of the socket data.
    """
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data


class Cmd:
    def __init__(self, cmd, name="", msg=""):
        self.cmd = cmd
        self.name = name
        self.msg = msg

    @staticmethod
    def decode(cmd, data):
        """Decodes the data into a Cmd object.
        - cmd is a value of DataType,
        - data is the bytearray to parse.
        """
        name = msg = ""
        if cmd == DataType.CMD_TELL.value:
            namesize = struct.unpack_from(">H", data)[0]
            shortsize = struct.calcsize("H")
            name = data[shortsize:shortsize + namesize].decode()
            msg = data[shortsize + namesize:].decode()
        elif cmd & DataType.MASK_CMD_ONEARG.value == DataType.MASK_CMD_ONEARG.value:
            name = data.decode()
       # other commands have no args
        return Cmd(cmd, name, msg)

    def get_data(self):
        """Encodes the msg into a byte-array that is the [data] part of a CPP msg of type CMD_X.
        """
        datatype = self.cmd
        namesize = len(self.name.encode())
        data = self.name.encode() + self.msg.encode()


        if datatype == DataType.CMD_TELL.value:
            data = struct.pack('>H', namesize) + data

        return data


class ServerMsg:
    def __init__(self, msg, timestamp=None, name=""):
        self.msg = msg
        self.timestamp = timestamp if timestamp else time()
        self.name = name

    @staticmethod
    def decode(data):
        """Decodes the [data] part of a CPP msg of type SERVERMSG into a ServerMsg object.
        """
        floatshort_size = struct.calcsize("fH")
        timestamp, namesize = struct.unpack_from(">fH", data)
        name = data[floatshort_size:floatshort_size + namesize].decode()
        msg = data[floatshort_size + namesize:].decode()
        return ServerMsg(msg, timestamp, name)

    def get_data(self):
        """Encodes the msg into a byte-array that is the [data] part of a CPP msg of type SERVERMSG.
        """
        namesize = len(self.name)
        data = struct.pack('>fH', self.timestamp, namesize) + self.name.encode() + self.msg.encode()
        return data

class FileAttachSend:
    def __init__(self, filename):
        self.filename = filename

    @staticmethod
    def decode(data):
        return FileAttachSend(data.decode())

    def get_data(self):
        return self.filename.encode()

class FileAttachRecv:
    def __init__(self, filename, name, uuid):
        self.filename = filename
        self.name = name
        self.uuid = uuid

    @staticmethod
    def decode(data):
        print(f"decode: data={data}")

        short_size = struct.calcsize("H")
        namesize, = struct.unpack_from(">H", data)
        print(namesize)
        name = data[short_size : short_size+namesize].decode()
        uuid = UUID(bytes=data[short_size+namesize : short_size+namesize+16])
        filename = data[short_size+namesize+16:].decode()
        return FileAttachRecv(filename, name, uuid)

    def get_data(self):
        namesize = len(self.name)
        data = struct.pack('>H', namesize) + self.name.encode() + self.uuid.bytes + self.filename.encode()
        print(f"data={data}")
        return data

class FilePart:
    def __init__(self, msg, timestamp=None, name=""):
        """data is the byte array to be parse.
        """
        self.msg = msg
        self.timestamp = timestamp if timestamp else time()
        self.name = name

    @staticmethod
    def decode(data):
        """Decodes the [data] part of a CPP msg of type SERVERMSG into a ServerMsg object.
        """
        floatshort_size = struct.calcsize("fH")
        timestamp, namesize = struct.unpack_from(">fH", data)
        name = data[floatshort_size:floatshort_size + namesize].decode()
        msg = data[floatshort_size + namesize:].decode()
        return ServerMsg(msg, timestamp, name)

    def get_data(self):
        """Encodes the msg into a byte-array that is the [data] part of a CPP msg of type SERVERMSG.
        """
        namesize = len(self.name)
        data = struct.pack('>fH', self.timestamp, namesize) + self.name.encode() + self.msg.encode()
        return data


# CPPS - Chat Program Protocol Secure
# Methods for receiving and sending message in CPPS protocol
# CPPS specifications are at chat_program_protocol.txt

def ssend(sock, aeskey, cpp_msg):
    """encodes a string or a Cmd object cpp_msg into raw data, encrypts it and sends it through sock
    """
    plaintext = encode(cpp_msg)
    # print(f"1st BYTE: {plaintext[0]}")
    # print(f"type: {type(cpp_msg)}")
    cipher = AES.new(aeskey, AES.MODE_EAX, mac_len=16)
    nonce = cipher.nonce
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    # print(f"SENT: message: \"{plaintext}\"\n      nonce: {nonce}\n      tag:{tag}\n      ciphertext:{ciphertext}\n")
    # both 'nonce' and 'tag' are bytearrays of length 16
    datasize = len(nonce) + len(tag) + len(ciphertext)
    # print(f"DATASIZE: {datasize}")
    raw_datasize = struct.pack(">I", datasize)
    sock.send(raw_datasize + nonce + tag + ciphertext)


def srecv(sock, aeskey):
    """Returns a string or ServerMsg or CPPCmd object decoded from the encrypted data in sock
    """
    try:
        nonce, tag, ciphertext = s_recv_raw(sock)
        if not (nonce and tag and ciphertext):
            return None
        cipher_aes = AES.new(aeskey, AES.MODE_EAX, nonce)
        cpp_data = cipher_aes.decrypt_and_verify(ciphertext, tag)
        data = cpp_data[5:]
        datatype, _ = struct.unpack('>BI', cpp_data[:5])
        return construct_cpp_msg(datatype, data)
    except BlockingIOError:
        return None

def s_recv_raw(sock):
    raw_datasize = s_recvn(sock, 4)
    nonce = s_recvn(sock, 16)
    tag = s_recvn(sock, 16)
    if not (raw_datasize and nonce and tag):
        return None, None, None
    datasize = struct.unpack('>I', raw_datasize)[0]
    # print(f"DATASIZE: {datasize}")
    data = bytes(s_recvn(sock, datasize-32))
    return nonce, tag, data

def s_recvn(sock, n):
    """Returns n bytes of the socket data.
    """
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data
