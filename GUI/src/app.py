# Chat client app with a graphical user interface.
from PyQt5 import QtWidgets, QtCore
import sys
from chat.windows.login_window import LoginWindow
from chat.windows.chat_window import ChatWindow

# **********************
DEFAULT_IP = '127.0.0.1'
DEFAULT_PORT = 8000
# **********************


class Application():
    def __init__(self, args=dict()):
        self.args = args
        self.client = None

    def exec(self):
        login_window = LoginWindow(args=self.args)
        login_window.exec()  # Runs until user connects to the server
        if not login_window.data: return  # window closed by user
        self.client = login_window.data['client']

        chat_window = ChatWindow(args={'client': self.client})
        chat_window.exec()
        try: self.client.send('/quit')
        except BrokenPipeError: pass  # socket already closed


def main():
    # Get username (if provided):
    try: default_name = sys.argv[1]
    except IndexError: default_name = ""
    # Get port (if provided):
    try: default_port = int(sys.argv[2])
    except Exception: default_port = DEFAULT_PORT

    args = {'default_name': default_name, 'default_port': default_port, 'default_ip': DEFAULT_IP}
    app = Application(args)
    app.exec()


if __name__ == "__main__":
    main()
