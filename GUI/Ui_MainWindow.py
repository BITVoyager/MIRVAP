# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'E:\GitHub\MIRVAP\GUI\MainWindow.ui'
#
# Created: Wed Mar 05 23:24:57 2014
#      by: PyQt4 UI code generator 4.9.6
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(800, 571)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.mdiArea = QtGui.QMdiArea(self.centralwidget)
        self.mdiArea.setAutoFillBackground(False)
        self.mdiArea.setViewMode(QtGui.QMdiArea.TabbedView)
        self.mdiArea.setTabsClosable(True)
        self.mdiArea.setTabsMovable(True)
        self.mdiArea.setObjectName(_fromUtf8("mdiArea"))
        self.horizontalLayout.addWidget(self.mdiArea)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 23))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuFile = QtGui.QMenu(self.menubar)
        self.menuFile.setObjectName(_fromUtf8("menuFile"))
        self.menuLoad = QtGui.QMenu(self.menuFile)
        self.menuLoad.setObjectName(_fromUtf8("menuLoad"))
        self.menuSave = QtGui.QMenu(self.menuFile)
        self.menuSave.setObjectName(_fromUtf8("menuSave"))
        self.menuStart = QtGui.QMenu(self.menubar)
        self.menuStart.setObjectName(_fromUtf8("menuStart"))
        self.menuRegister = QtGui.QMenu(self.menuStart)
        self.menuRegister.setObjectName(_fromUtf8("menuRegister"))
        self.menuPlugin = QtGui.QMenu(self.menuStart)
        self.menuPlugin.setObjectName(_fromUtf8("menuPlugin"))
        self.menuAnalysis = QtGui.QMenu(self.menuStart)
        self.menuAnalysis.setObjectName(_fromUtf8("menuAnalysis"))
        self.menuWidget_View = QtGui.QMenu(self.menuStart)
        self.menuWidget_View.setObjectName(_fromUtf8("menuWidget_View"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setStyleSheet(_fromUtf8("QStatusBar::item{border: 0px}"))
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)
        self.actionExit = QtGui.QAction(MainWindow)
        self.actionExit.setObjectName(_fromUtf8("actionExit"))
        self.actionClear_all = QtGui.QAction(MainWindow)
        self.actionClear_all.setObjectName(_fromUtf8("actionClear_all"))
        self.menuFile.addAction(self.menuLoad.menuAction())
        self.menuFile.addAction(self.menuSave.menuAction())
        self.menuFile.addAction(self.actionClear_all)
        self.menuFile.addAction(self.actionExit)
        self.menuStart.addAction(self.menuPlugin.menuAction())
        self.menuStart.addAction(self.menuWidget_View.menuAction())
        self.menuStart.addSeparator()
        self.menuStart.addAction(self.menuRegister.menuAction())
        self.menuStart.addAction(self.menuAnalysis.menuAction())
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuStart.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QObject.connect(self.actionExit, QtCore.SIGNAL(_fromUtf8("triggered()")), MainWindow.close)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "Medical Image Registration Visualization and Analysis Platform", None))
        self.menuFile.setTitle(_translate("MainWindow", "File", None))
        self.menuLoad.setTitle(_translate("MainWindow", "Load", None))
        self.menuSave.setTitle(_translate("MainWindow", "Save", None))
        self.menuStart.setTitle(_translate("MainWindow", "Start", None))
        self.menuRegister.setTitle(_translate("MainWindow", "Register", None))
        self.menuPlugin.setTitle(_translate("MainWindow", "Plugin", None))
        self.menuAnalysis.setTitle(_translate("MainWindow", "Analysis", None))
        self.menuWidget_View.setTitle(_translate("MainWindow", "Widget View", None))
        self.actionExit.setText(_translate("MainWindow", "Exit", None))
        self.actionClear_all.setText(_translate("MainWindow", "Clear all", None))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

