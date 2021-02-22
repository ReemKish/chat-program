from chat.backend.client import Client
from PyQt5 import QtWidgets, QtCore
from .window import Window
from ..frontend.chat_ui import ChatUi
from ..frontend.widgets import QGrowingTextBrowser


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

    def display_msg(self, html):
        msgtype = html[:4]
        html = html[4:]
        move_scrollbar = False
        scrollbar = self.ui.msgArea.verticalScrollBar()
        if scrollbar.value() == scrollbar.maximum():
            move_scrollbar = True
        msgBrowser = QGrowingTextBrowser(self.ui.msgScrollAreaWidgetContents)
        msgBrowser.setStyleSheet("border: 3px solid white; border-radius: 8px")
        if msgtype == "SELF":
            msgBrowser.setStyleSheet("background-color:#93ffa0; border: 3px solid #93ffa0; border-radius: 8px")
            self.ui.msgVLayout.addWidget(msgBrowser, 0, QtCore.Qt.AlignRight)
        elif msgtype == "SERV":
            msgBrowser.setStyleSheet("background-color:#dddddd; border: 3px solid #dddddd; border-radius: 8px")
            self.ui.msgVLayout.addWidget(msgBrowser, 0, QtCore.Qt.AlignCenter)
        else:  # msgtype == "MESG"
            self.ui.msgVLayout.addWidget(msgBrowser)
        msgBrowser.setMaximumHeight(150)
        msgBrowser.setHtml(html)
        self.ui.msgs.append(msgBrowser)
        self.resize_event(self.ui.window)
        if move_scrollbar:
            scrollbar.setValue(scrollbar.maximum())

    def send_msg(self):
        """Sends the message typed by the user & clears the input.
        """
        msg_plain = self.ui.msgInput.toPlainText()
        msg_html = self.ui.msgInput.toHtml()
        if msg_plain:
            if msg_plain.strip().split(' ')[0] in Client.COMMANDS:
                self.client.send(msg_plain)
            else:
                self.client.send(msg_html)
        self.ui.msgInput.clear()
        self.ui.msgInput.setFocus()

    def received_string(self, st):
        if not st:
            self.close()
        else:
            self.display_msg(st)

    def close(self):
        """Closes the program.
        """
        self.ui.window.close()


class RecvThread(QtCore.QThread):
    """Thread responsible for receiving data from the server.
    """

    received = QtCore.pyqtSignal(str)  # stored string details the cause of rejection.

    def __init__(self, client):
        super().__init__()
        super().__init__(parent=self)
        self.client = client

    def run(self):
        while True:
            data = self.client.recv()
            self.received.emit(data)


if __name__ == "__main__":
    app = ChatWindow()
    app.exec()
