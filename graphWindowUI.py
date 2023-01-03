# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'graphWindow.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_GraphWindow(object):
    def setupUi(self, GraphWindow):
        GraphWindow.setObjectName("GraphWindow")
        GraphWindow.resize(420, 160)
        GraphWindow.setMinimumSize(QtCore.QSize(420, 160))
        GraphWindow.setMaximumSize(QtCore.QSize(420, 160))
        GraphWindow.setStyleSheet("background: rgb(255, 255, 255)")
        self.graph_placeholder = QtWidgets.QWidget(GraphWindow)
        self.graph_placeholder.setGeometry(QtCore.QRect(140, 0, 280, 160))
        self.graph_placeholder.setStyleSheet("background: white")
        self.graph_placeholder.setObjectName("graph_placeholder")
        self.temperature = QtWidgets.QLabel(GraphWindow)
        self.temperature.setGeometry(QtCore.QRect(19, 20, 121, 120))
        font = QtGui.QFont()
        font.setFamily("Lobster 1.4")
        font.setPointSize(41)
        self.temperature.setFont(font)
        self.temperature.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.temperature.setTextFormat(QtCore.Qt.PlainText)
        self.temperature.setAlignment(QtCore.Qt.AlignCenter)
        self.temperature.setObjectName("temperature")

        self.retranslateUi(GraphWindow)
        QtCore.QMetaObject.connectSlotsByName(GraphWindow)

    def retranslateUi(self, GraphWindow):
        _translate = QtCore.QCoreApplication.translate
        GraphWindow.setWindowTitle(_translate("GraphWindow", "Dialog"))
        self.temperature.setText(_translate("GraphWindow", "58°"))
