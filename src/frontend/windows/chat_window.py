from time import localtime, strftime
from backend.client import Client
from backend import cpp
from PyQt5 import QtWidgets, QtCore
from .window import Window
from frontend.ui.chat_ui import ChatUi
from frontend.ui.widgets import QGrowingTextBrowser
from enum import Enum
from colorsys import hls_to_rgb


class MsgType(Enum):
    SELF = 0  # msg typed by the user.
    OTHER = 1  # msg typed by another user in the group.
    SERVER = 2  # msg sent to the user by the server.


class ChatWindow(Window):
    def __init__(self, args=dict()):
        super().__init__(ui=ChatUi(), Qtype=QtWidgets.QMainWindow, args=args)
        self.client = self.args['client']
        self.recv_thread = RecvThread(self.client)
        self.recv_thread.received.connect(self.received_string)
        self.recv_thread.daemon  = True
        self.recv_thread.start()

    def extend_ui(self):
        self.ui.msgs = []
        self.ui.sendButton.clicked.connect(self.send_msg)
        self.ui.window.resizeEvent = self.resize_event
        self.ui.msgInput.send = self.send_msg
        self.ui.msgInput.cmds = Client.COMMANDS

    def resize_event(self, event):
        self.ui.resize_event(event)
        for msgBrowser in self.ui.msgs:
            msgBrowser.setMaximumWidth(self.ui.msgArea.size().width() - 30)
            msgBrowser.adjustSize()

    def display_msg(self, msgtype, html):
        msgBrowser = QGrowingTextBrowser(self.ui.msgScrollAreaWidgetContents)
        if msgtype == MsgType.SELF:
            style = self.ui.selfmsg_style
            self.ui.msgVLayout.addWidget(msgBrowser, 0, QtCore.Qt.AlignRight)
        elif msgtype == MsgType.SERVER:
            style = self.ui.servermsg_style
            self.ui.msgVLayout.addWidget(msgBrowser, 0, QtCore.Qt.AlignCenter)
        elif msgtype == MsgType.OTHER:
            style = self.ui.othermsg_style
            self.ui.msgVLayout.addWidget(msgBrowser)
        msgBrowser.setStyleSheet(style)
        move_scrollbar = False
        scrollbar = self.ui.msgArea.verticalScrollBar()
        if scrollbar.value() == scrollbar.maximum():
            move_scrollbar = True
        msgBrowser.setMaximumHeight(150)
        msgBrowser.setHtml(html)
        self.ui.msgs.append(msgBrowser)
        self.resize_event(self.ui.window)
        if move_scrollbar:
            scrollbar.setValue(scrollbar.maximum())

    def handle_msg(self, cpp_msg):
        if not cpp_msg.name:
            msgtype = MsgType.SERVER
        elif cpp_msg.name == self.client.name:
            msgtype = MsgType.SELF
        else:
            msgtype = MsgType.OTHER
        self.display_msg(msgtype, self.html_format(msgtype, cpp_msg))

    def name_to_color(self, name):
        """Calculates and returns a member's name color
        """
        k = hash(name)*6 % 360
        r,g,b = tuple(round(y*256) for y in hls_to_rgb(k/360,.3,.9))
        return f"#{r:02x}{g:02x}{b:02x}"

    def html_format(self, msgtype, cpp_msg):
        time = strftime("%H:%M", localtime(cpp_msg.timestamp))
        msg = cpp_msg.msg
        name = cpp_msg.name
        color = self.name_to_color(name)
        if msgtype == MsgType.SELF:
            return \
                f'''</head>
<body style=" font-family:\'Sans Serif\'; font-size:9pt; font-weight:400; font-style:normal;">{msg}<p align="right"
style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">
<span style=" font-size:7pt; color:#353535;">{time}</span></p>
</body>
</html>'''
        elif msgtype == MsgType.OTHER:
            return \
                f'''</head>
<body style=" font-family:\'Sans Serif\'; font-size:9pt; font-weight:400; font-style:normal;">\n<p
style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">
<span style=" color:{color};">{name}</span></p>\n{msg}\n<p align="right"
style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">
<span style=" font-size:7pt; color:#353535;">{time}</span></p>
</body>
</html>'''
        elif msgtype == MsgType.SERVER:
            return f'''</head>
    <body style=" font-family:\'Sans Serif\'; font-size:9pt; font-weight:400; font-style:normal;">
    </p>{msg}<p align="right"
    style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">
    <span style=" font-size:7pt; color:#353535;">{time}</span></p>
    </body>
    </html>'''

    def send_msg(self):
        """Sends the message typed by the user & clears the input.
        """
        msg_plain = self.ui.msgInput.toPlainText()
        msg_html = self.ui.msgInput.toHtml()
        if msg_plain:
            if msg_plain.strip().split(' ')[0] in Client.COMMANDS:
                self.send_cmd(msg_plain)
            else:
                # self.client.send(msg_plain)
                self.client.ssend(msg_html)
        self.ui.msgInput.clear()
        self.ui.msgInput.setFocus()

    def send_cmd(self, cmdline):
        args = cmdline.split(" ")
        cmdname, args = args[0].lower(), args[1:]
        print(f"CMDLINE: {cmdline}\n CMDNAME:{cmdname}\n args:{args}")

        try:
            cmdtype = Client.COMMANDS[cmdname]
        except KeyError:
            return
        if len(args) == 0:
            cmd = cpp.Cmd(cmdtype)
        elif len(args) == 1:
            cmd = cpp.Cmd(cmdtype, args[0])
        elif len(args) >= 2:
            cmd = cpp.Cmd(cmdtype, args[0], " ".join(args[1:]))
        self.client.ssend(cmd)
        if cmdtype == cpp.DataType.CMD_QUIT.value:
            self.close()

    def received_string(self, cpp_msg):
        print(f"RECEIVED CPP_MSG: {cpp_msg}")
        if not cpp_msg:  # kicked by server
            self.close()
        else:
            self.handle_msg(cpp_msg)

    def close(self):
        """Closes the program.
        """
        self.recv_thread.stop()
        self.ui.window.close()

    def closeEvent(self, event):
        print("WHATTHEFUCJ")
        self.close()
        event.accept()


class RecvThread(QtCore.QThread):
    """Thread responsible for receiving data from the server.
    """

    # stored string details the cause of rejection.
    received = QtCore.pyqtSignal(object)

    def __init__(self, client):
        super().__init__()
        super().__init__(parent=self)
        self.client = client
        self.listen = True

    def run(self):
        while self.listen:
            cpp_msg = self.client.srecv()
            self.received.emit(cpp_msg)
    
    def stop(self):
        self.listen = False


if __name__ == "__main__":
    app = ChatWindow()
    app.exec()
