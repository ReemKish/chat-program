# CPP - Chat Program Protocol
# Methods for receiving and sending message in CPP protocol
# CPP specifications are at chat_program_protocol.txt

import enum
import socket
import struct
from time import time


class DataType(enum.Enum):
    MSG = 0
    SERVERMSG = 1
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


def send(sock, cpp_msg):
    """encodes a string or a Cmd object cpp_msg into raw data and sends it through sock
    """
    data = cpp_msg.encode()
    datasize = len(data)
    if type(cpp_msg) is str: datatype = DataType.MSG.value
    elif type(cpp_msg) is ServerMsg: datatype = DataType.SERVERMSG.value
    elif type(cpp_msg) is Cmd: datatype = cpp_msg.cmd
    elif cpp_msg is None: datatype = cpp_msg = Cmd(DataType.CMD_QUIT)  # Quit
    print(f"SEND: type:{datatype}, size:{datasize}, data:{data}")
    sock.send(struct.pack('>BI', datatype, datasize) + data)


def recv(sock):
    """Returns a string or ServerMsg or CPPCmd object decoded from the raw data in sock
    """
    try:
        datatype, data = _recv_raw(sock)
        if datatype is None: return None
        print(f"RECV: datatype:{datatype}, data:{data}")
        if datatype == DataType.MSG.value:
            return data.decode()
        elif datatype == DataType.SERVERMSG.value:
            return ServerMsg.decode(data)
        elif datatype & DataType.MASK_CMD.value == DataType.MASK_CMD.value:  # data is a command
            return Cmd.decode(datatype, data)
        else:
            return None  # invalid datatype
    except socket.error:  # connection has likely been closed
        return None


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
        """Decodes the data into a ServerMsg object.
        - cmd is a value of DataType,
        - data is the bytearray to parse.
        """
        name = msg = ""
        if cmd == DataType.CMD_TELL.value:
            namesize = struct.unpack_from("H", data)[0]
            shortsize = struct.calcsize("H")
            name = data[shortsize:shortsize + namesize].decode()
            msg = data[shortsize + namesize:].decode()
        elif cmd & DataType.MASK_CMD_ONEARG.value == DataType.MASK_CMD_ONEARG.value:
            name = data.decode()
       # other commands have no args
        return Cmd(cmd, name, msg)

    def encode(self):
        """Encodes the msg into a byte-array that is the [data] part of a CPP msg of type CMD_X.
        """
        datatype = self.cmd
        namesize = len(self.name)
        datasize = namesize + len(self.msg)
        data = self.name.encode() + self.msg.encode()

        if datatype == DataType.CMD_TELL:
            datasize += namesize
            data = struct.pack('>H', namesize) + data

        return data


class ServerMsg:
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
        print(f"DE: {timestamp}, {name}, {msg}")
        return ServerMsg(msg, timestamp, name)

    def encode(self):
        """Encodes the msg into a byte-array that is the [data] part of a CPP msg of type SERVERMSG.
        """
        namesize = len(self.name)
        data = struct.pack('>fH', self.timestamp, namesize) + self.name.encode() + self.msg.encode()
        return data
