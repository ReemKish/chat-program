from PyQt5 import QtCore, QtGui, QtWidgets
from .widgets import QGrowingTextEdit, QFileButton


class ChatUi(object):
    selfmsg_style = "background-color:#93ffa0; border: 3px solid #93ffa0; border-radius: 8px; "
    othermsg_style = "border: 3px solid white; border-radius: 8px"
    servermsg_style = "background-color:#dddddd; border: 3px solid #dddddd; border-radius: 8px"

    def setup_ui(self, window):
        self.window = window
        self.window.setObjectName("Window")
        self.window.resize(700, 500)
        self.centralwidget = QtWidgets.QWidget(self.window)
        self.centralwidget.setObjectName("centralwidget")
        # main vertical layout:
        self.mainVLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.mainVLayout.setObjectName("verticalLayout")
        # scroll area where messages are shown:
        self.msgArea = QtWidgets.QScrollArea(self.centralwidget)
        self.msgArea.setWidgetResizable(True)
        self.msgArea.setObjectName("msgArea")
        self.msgScrollAreaWidgetContents = QtWidgets.QWidget()
        self.msgScrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.msgScrollAreaWidgetContents.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum))
        self.msgArea.setWidget(self.msgScrollAreaWidgetContents)
        self.mainVLayout.addWidget(self.msgArea)
        # vertical layout for the msg area:
        self.msgVLayout = QtWidgets.QVBoxLayout(self.msgScrollAreaWidgetContents)
        # horizontal layout for input widgets:
        self.inputHLayout = QtWidgets.QHBoxLayout()
        self.inputHLayout.setObjectName("inputHLayout")
        # text msg input:
        self.msgInput = QGrowingTextEdit(self.centralwidget)
        self.msgInput.setObjectName("msgInput")
        self.msgInput.setMaximumHeight(self.window.size().height() // 2)
        self.inputHLayout.addWidget(self.msgInput)
        # send-message button:
        self.sendButton = QtWidgets.QPushButton(self.centralwidget)
        self.sendButton.setObjectName("sendButton")
        self.sendButton.setCursor(QtCore.Qt.PointingHandCursor)
        self.inputHLayout.addWidget(self.sendButton, 0, QtCore.Qt.AlignBottom)
        # file-attachment button:
        self.fileButton = QFileButton(self.centralwidget)
        self.fileButton.setObjectName("fileButton")
        self.fileButton.setCursor(QtCore.Qt.PointingHandCursor)
        self.inputHLayout.addWidget(self.fileButton, 0, QtCore.Qt.AlignBottom)
        # window layout;
        self.mainVLayout.addLayout(self.inputHLayout)
        self.window.setCentralWidget(self.centralwidget)
        self.window.resizeEvent = self.resize_event

        self.style()
        self.retranslateUi(self.window)
        QtCore.QMetaObject.connectSlotsByName(self.window)

    def resize_event(self, event):
        self.msgInput.setMaximumHeight(event.size().height() // 2)
        self.msgInput.adjustHeight()

    def retranslateUi(self, Window):
        _translate = QtCore.QCoreApplication.translate
        Window.setWindowTitle(_translate("Window", "Chat"))
        self.msgInput.setPlaceholderText(_translate("Window", "Type a message"))
        self.sendButton.setText(_translate("Window", "Send"))
        self.fileButton.setText(_translate("Window", "Attach file"))

    def style(self):
        scrollbar_style = '''
            QScrollBar:vertical{
                border:0px solid;
                border-color: rgb(197,197,199);
                width: 1px;
                margin: 0px 0px 0px 0px;
                background: rgb(234,234,234);
            }

            QScrollBar::handle:vertical  {
                background: rgb(14,65,148);
            }

            QScrollBar::add-line:vertical{
                height: 0px;
            }

            QScrollBar::sub-line:vertical{
                height: 0px;
            }'''
        self.centralwidget.setStyleSheet(scrollbar_style)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = QtWidgets.QMainWindow()
    ui = ChatUi()
    ui.setup_ui(window)
    window.show()
    sys.exit(app.exec_())
