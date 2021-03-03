# widgets.py
# Custom widgets designed for specific usage in the program.

from PyQt5 import QtWidgets, QtGui
from time import sleep
import PyQt5


class QGrowingTextEdit(QtWidgets.QTextEdit):
    """A TextEdit widgets that dynamically adjusts its size to fit its contents.
    """

    def __init__(self, *args, **kwargs):
        super(QGrowingTextEdit, self).__init__(*args, **kwargs)

        self.height_min = 0
        self.height_max = 65000

        self.document().contentsChanged.connect(self.adjustHeight)
        self.setFocus()

    def adjustHeight(self):
        docHeight = self.document().size().height()
        if self.height_min <= docHeight <= self.height_max:
            self.setFixedHeight(docHeight + 2)
        elif docHeight < self.height_min:
            self.setFixedHeight(self.height_min)
        else:
            self.setFixedHeight(self.height_max)

    def setMaximumHeight(self, maxh): self.height_max = maxh
    def setMinimumHeight(self, minh): self.height_min = minh


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
        if self.height_min <= height <= self.height_max:
            self.setFixedHeight(height + 6)
        elif height < self.height_min:
            self.setFixedHeight(self.height_min)
        else:
            self.setFixedHeight(self.height_max)

    def adjustWidth(self):
        width = QtGui.QFontMetrics(self.document().defaultFont()).size(0, self.toPlainText()).width() + 30  # +30 to show hour
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
