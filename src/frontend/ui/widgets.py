# widgets.py
# Custom widgets designed for specific usage in the program.

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt
from time import sleep
import ntpath
import random
from . import util

class QFileButton(QtWidgets.QPushButton):
    def __init__(self, parent = None):
        super(QFileButton, self).__init__(parent)
        self.installEventFilter(self)
        self.filepath = None
        self.hideButton = None

    def eventFilter(self, object, event):
        if event.type()== QtCore.QEvent.FocusOut:
            self.setText("Attach file")
            self.filepath = None
            if self.hideButton is not None:
                self.hideButton.show()
        return False

    def setFilepath(self, filepath):
        self.filepath = filepath

class QGrowingTextEdit(QtWidgets.QTextEdit):
    """A TextEdit widgets that dynamically adjusts its size to fit its contents.
    """

    def __init__(self, *args, send=None, **kwargs):
        super(QGrowingTextEdit, self).__init__(*args, **kwargs)

        self.height_min = 0
        self.height_max = 65000

        self.document().contentsChanged.connect(self.adjustHeight)
        self.setFocus()
        self.send = send
        self.cmds = []

    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        k = e.key()
        # ENTER: Send message.
        if k == Qt.Key_Return and not e.modifiers():
            if self.send: self.send()
        # TAB: Complete command or insert 4 spaces.
        elif k == Qt.Key_Tab:
            tc = self.textCursor()
            text = self.toPlainText()
            if text.startswith('/'):
                for cmd in self.cmds:
                    if cmd.startswith(text):
                        tc.insertText(cmd[len(text):])
                        return
            tc.insertText('    ')
        else:
            return super().keyPressEvent(e)

    def adjustHeight(self):
        docHeight = self.document().size().height()
        docHeight = int(docHeight)
        if self.height_min <= docHeight <= self.height_max:
            self.setFixedHeight(docHeight + 2)
        elif docHeight < self.height_min:
            self.setFixedHeight(self.height_min)
        else:
            self.setFixedHeight(self.height_max)

    def setMaximumHeight(self, maxh): self.height_max = maxh
    def setMinimumHeight(self, minh): self.height_min = minh
    def setStyle(self, style_type): pass

class QFileAttachment(QtWidgets.QFrame):
    """A TextBrowser widgets that dynamically adjusts its size to fit its contents.
    """

    def __init__(self, uuid, filepath, *args, **kwargs):
        super(QFileAttachment, self).__init__(*args, **kwargs)
        self.uuid = uuid
        self.filepath = filepath
        self.filename = ntpath.basename(filepath)

        # Get icon from file extension
        fileInfo = QtCore.QFileInfo(filepath)
        iconProvider = QtWidgets.QFileIconProvider()
        icon = iconProvider.icon(fileInfo)

        # layouts
        innerFrame = QtWidgets.QFrame(self, objectName="innerFrame")
        outerLayout = QtWidgets.QVBoxLayout(self)
        innerLayout = QtWidgets.QVBoxLayout(innerFrame)
        # file button
        fileButton = QtWidgets.QPushButton(innerFrame)
        fileButton.setCursor(QtCore.Qt.PointingHandCursor)
        fileButton.setText(f" {self.filename}")
        fileButton.setIcon(icon)
        fileButton.setIconSize(QtCore.QSize(30,30))

        # progress bar
        bar = QtWidgets.QProgressBar(innerFrame, minimum=0, maximum=100, objectName="bar")
        bar.setValue(random.randint(20,80))
        bar.setValue(100)
        bar.setMaximumHeight(10)
        bar.setAlignment(QtCore.Qt.AlignCenter)
        bar.setTextVisible(False)

        innerLayout.addWidget(fileButton)
        innerLayout.addWidget(bar)


        # innerFrame.setStyleSheet("border: 0px; font-size: 14px; background-color:#84df8f; padding: 0px; margin: 0px;")
        outerLayout.addWidget(innerFrame)
        fileButton.setFont(QtGui.QFont("Arial", round(14*0.75)))
        fileButton.setStyleSheet("font-size: 14px; font-family: Arial")
        print(fileButton.font().family())
        width = QtGui.QFontMetrics(fileButton.font()).size(0, fileButton.text()).width() + 80  # +30 to show hour
        width = int(width)
        self.innerFrame = innerFrame
        self.bar = bar
        self.fileButton = fileButton
        self.setFixedWidth(width)
        
    def setStyle(self, style_type):
        frame_color = bar_color = None
        inner_darken = .95 
        bar_darken = .9
        if style_type == 0:
            bar_color   = "#7ae487"
            inner_color = "#b3ffbc"
            base_color = "#93ffa0"
        else:
            base_color = "#ffffff"
        inner_color = util.adjust_lightness(base_color, inner_darken)
        bar_color = util.adjust_lightness(base_color, bar_darken)
        self.setStyleSheet(f"border-radius:8px; background-color:{base_color}")
        self.innerFrame.setStyleSheet(f"border: 0px; font-size: 14px; font-family:Arial; background-color:{inner_color}; padding: 0px; margin: 0px;")
        self.bar.setStyleSheet(f"#bar::chunk {{ margin: 0.5px; background-color:{bar_color}; border-radius: 3px; }} ")


class QGrowingTextBrowser(QtWidgets.QTextBrowser):
    """A TextBrowser widgets that dynamically adjusts its size to fit its contents.
    """

    def __init__(self, *args, **kwargs):
        super(QGrowingTextBrowser, self).__init__(*args, **kwargs)
        super(QGrowingTextBrowser, self).setMinimumHeight(200)

        self.height_min = 0
        self.height_max = 100
        self.width_min = 0
        self.width_max = 65000

        self.document().contentsChanged.connect(self.adjustSize)

    def adjustSize(self):
        QtWidgets.QApplication.processEvents()
        self.adjustWidth()
        self.adjustHeight()

    def adjustHeight(self):
        height = self.document().size().height()
        height = int(height)
        if self.height_min <= height <= self.height_max:
            self.setFixedHeight(height + 6)
        elif height < self.height_min:
            self.setFixedHeight(self.height_min)
        else:
            self.setFixedHeight(self.height_max)

    def adjustWidth(self):
        width = QtGui.QFontMetrics(self.document().defaultFont()).size(0, self.toPlainText()).width() + 30  # +30 to show hour
        width = int(width)
        if self.width_min <= width <= self.width_max:
            self.setFixedWidth(width)
        elif width < self.width_min:
            self.setFixedWidth(self.width_min)
        else:
            self.setFixedWidth(self.width_max)

    def setMaximumHeight(self, maxh): self.height_max = maxh; self.adjustHeight()
    def setMinimumHeight(self, minh): self.height_min = minh; self.adjustHeight()
    def setMaximumWidth(self, maxw): self.width_max = maxw; self.adjustWidth()
    def setMinimumWidth(self, minw): self.width_min = minw; self.adjustWidth()
    def setStyle(self, style_type): pass
