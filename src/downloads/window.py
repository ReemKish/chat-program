from PyQt5 import QtWidgets, QtCore
import sys


class Window():
    def __init__(self, ui=None, Qtype=QtWidgets.QMainWindow, args=dict()):
        """
        args - program arguments.
        type - specifies window type, callable. (QtWidgets.*)
        ui - ui object, represents the window's ui.
        data - optional data to be returned from the window when it is closed.
        """
        self.ui = ui
        self.Qtype = Qtype
        self.args = args
        self.data = dict()

    def extend_ui(self):
        """Extend the ui with functionality that requires specific program parameters. 
        """
        pass

    def exec(self):
        """Execute and show the window.
        """
        Qapp = QtWidgets.QApplication(sys.argv)
        self.window = self.Qtype()
        self.ui.setup_ui(self.window)
        self.extend_ui()
        self.window.show()
        Qapp.exec_()
        return self.data
