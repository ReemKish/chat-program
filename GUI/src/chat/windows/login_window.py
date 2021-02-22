from PyQt5 import QtWidgets, QtCore
from .window import Window
from ..frontend.login_ui import LoginUi
from ..backend.client import Client


class LoginWindow(Window):
    def __init__(self, args=dict()):
        super().__init__(ui=LoginUi(), Qtype=QtWidgets.QDialog, args=args)

    def extend_ui(self):
        self.ui.spinPort.setValue(self.args['default_port'])
        self.ui.lineIP.setPlaceholderText(self.args['default_ip'])
        self.ui.lineName.setText(self.args['default_name'])
        self.ui.buttonBox.accepted.connect(lambda: self.login() if self.validate_login() else None)
        self.ui.lineName.textEdited.connect(self.ui.labelError.clear)

        # self.ui.buttonBox.accepted.emit()

    def login(self):
        name = self.ui.lineName.text()
        ip = self.ui.lineIP.text() if self.ui.lineIP.text() else self.args['default_ip']
        port = self.ui.spinPort.value()
        self.ui.ok()
        connect_thread = ConnectThread(name, ip, port)
        connect_thread.rejected.connect(self.rejected)
        connect_thread.accepted.connect(self.accepted)
        connect_thread.start()

    def validate_login(self):
        name = self.ui.lineName.text()
        if not name:
            self.ui.labelError.setText("Error: Invalid Name.")
            return False
        return True

    def rejected(self, err):
        self.ui.retry()
        self.show_error(err)

    def accepted(self, client):
        self.data['client'] = client
        QtWidgets.QApplication.restoreOverrideCursor()
        self.window.close()

    def show_error(self, err):
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle("Error")
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setText(err)
        msg.exec()


class ConnectThread(QtCore.QThread):

    rejected = QtCore.pyqtSignal(str)  # stored string details the cause of rejection.
    accepted = QtCore.pyqtSignal(Client)  # stored Client-type is the client object for communication with the server.

    def __init__(self, name, ip, port):
        super().__init__()
        super().__init__(parent=self)
        self.name = name
        self.ip = ip
        self.port = port

    def run(self):
        self.msleep(250)
        client = Client(self.name)
        client.connect(self.ip, self.port)
        response = client.recv()
        if response.startswith("Connection Refused"):
            self.rejected.emit(response)
        else:
            self.accepted.emit(client)


if __name__ == "__main__":
    app = LoginWindow(args={'default_ip': '127.0.0.1', 'default_port': 8000})
    app.exec()
