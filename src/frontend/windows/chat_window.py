from time import gmtime, strftime
from backend import client
from backend.client import Client
from backend import cpp
from PyQt5 import QtWidgets, QtCore
from .window import Window
from frontend.ui.chat_ui import ChatUi
from frontend.ui.widgets import QGrowingTextBrowser
from enum import Enum


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
        self.recv_thread.start()

    def extend_ui(self):
        self.ui.msgs = []
        self.ui.sendButton.clicked.connect(self.send_msg)
        self.ui.window.resizeEvent = self.resize_event

    def resize_event(self, event):
        self.ui.resize_event(event)
        for msgBrowser in self.ui.msgs:
            msgBrowser.setMaximumWidth(self.ui.msgArea.size().width() - 30)
            msgBrowser.adjustSize()

    # def display_msg(self, html):
    #     print("HTML:\n" + html)
    #     msgtype = html[:4]
    #     html = html[4:]
    #     move_scrollbar = False
    #     scrollbar = self.ui.msgArea.verticalScrollBar()
    #     if scrollbar.value() == scrollbar.maximum():
    #         move_scrollbar = True
    #     msgBrowser = QGrowingTextBrowser(self.ui.msgScrollAreaWidgetContents)
    #     msgBrowser.setStyleSheet("border: 3px solid white; border-radius: 8px")
    #     if msgtype == "SELF":
    #         msgBrowser.setStyleSheet("background-color:#93ffa0; border: 3px solid #93ffa0; border-radius: 8px")
    #         self.ui.msgVLayout.addWidget(msgBrowser, 0, QtCore.Qt.AlignRight)
    #     elif msgtype == "SERV":
    #         msgBrowser.setStyleSheet("background-color:#dddddd; border: 3px solid #dddddd; border-radius: 8px")
    #         self.ui.msgVLayout.addWidget(msgBrowser, 0, QtCore.Qt.AlignCenter)
    #     else:  # msgtype == "MESG"
    #         self.ui.msgVLayout.addWidget(msgBrowser)
    #     msgBrowser.setMaximumHeight(150)
    #     msgBrowser.setHtml(html)
    #     self.ui.msgs.append(msgBrowser)
    #     self.resize_event(self.ui.window)
    #     if move_scrollbar:
    #         scrollbar.setValue(scrollbar.maximum())

    def display_msg(self, msgtype, html):
        #     html = f'''</head>
        # <body style=" font-family:\'Sans Serif\'; font-size:9pt; font-weight:400; font-style:normal;">
        # </p>HEY<p align="right"
        # style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">
        # <span style=" font-size:7pt; color:#353535;">HH:MM</span></p>
        # </body>
        # </html>'''
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
        if not cpp_msg.name: msgtype = MsgType.SERVER
        elif cpp_msg.name == self.client.name: msgtype = MsgType.SELF
        else: msgtype = MsgType.OTHER
        self.display_msg(msgtype, self.html_format(msgtype, cpp_msg))

    def html_format(self, msgtype, cpp_msg):
        time = strftime("%H:%M", gmtime(cpp_msg.timestamp))
        msg = cpp_msg.msg
        name = cpp_msg.name
        color = "#00557f"
        if msgtype == MsgType.SELF:
            return \
                f'''</head>
<body style=" font-family:\'Sans Serif\'; font-size:9pt; font-weight:400; font-style:normal;">{msg}<p align="right"
style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">
<span style=" font-size:7pt; color:#353535;">{time}</span></p>
</body>
</html>'''
            return \
                f'''</head>
    <body style=" font-family:\'Sans Serif\'; font-size:9pt; font-weight:400; font-style:normal;">
    </p>{msg}<p align="right"
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
                self.client.send(msg_html)
        self.ui.msgInput.clear()
        self.ui.msgInput.setFocus()

    def send_cmd(self, cmdline):
        args = cmdline.split(" ")
        cmdname, args = args[0].lower(), args[1:]
        try:
            cmdtype = Client.COMMANDS[cmdname]
        except KeyError:
            return
        if len(args) == 0: cmd = cpp.Cmd(cmdtype)
        elif len(args) == 1: cmd = cpp.Cmd(cmdtype, args[0])
        elif len(args) >= 2: cmd = cpp.Cmd(cmdtype, args[0], args[1])
        self.client.send(cmd)

    def received_string(self, cpp_msg):
        if not cpp_msg:  # kicked by server
            self.close()
        else:
            self.handle_msg(cpp_msg)

    def close(self):
        """Closes the program.
        """
        self.ui.window.close()


class RecvThread(QtCore.QThread):
    """Thread responsible for receiving data from the server.
    """

    received = QtCore.pyqtSignal(object)  # stored string details the cause of rejection.

    def __init__(self, client):
        super().__init__()
        super().__init__(parent=self)
        self.client = client

    def run(self):
        while True:
            cpp_msg = self.client.recv()
            self.received.emit(cpp_msg)


if __name__ == "__main__":
    app = ChatWindow()
    app.exec()
