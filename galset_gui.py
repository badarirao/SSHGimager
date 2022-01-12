# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'galvanometer_settings.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtWidgets
from pyqtgraph.parametertree import Parameter, ParameterTree



class Ui_galvanoForm(object):
    def galset_setupUi(self, Form,grp):
        Form.setObjectName("Form")
        Form.resize(300, 310)
        Form.setMinimumSize(QtCore.QSize(300, 310))
        Form.setMaximumSize(QtCore.QSize(400, 410))
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.defaultButton = QtWidgets.QPushButton(Form)
        self.defaultButton.setObjectName("defaultButton")
        self.horizontalLayout.addWidget(self.defaultButton)
        self.setdefaultButton = QtWidgets.QPushButton(Form)
        self.setdefaultButton.setObjectName("setdefaultButton")
        self.horizontalLayout.addWidget(self.setdefaultButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.p = Parameter.create(name='Galvanometer Settings', type='group', children=grp)
        self.treeWidget = ParameterTree(Form)
        self.treeWidget.setObjectName("treeWidget")
        self.treeWidget.setParameters(self.p, showTop=False)
        self.treeWidget.paramSet = self.p
        self.verticalLayout.addWidget(self.treeWidget)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.okayButton = QtWidgets.QPushButton(Form)
        self.okayButton.setObjectName("okayButton")
        self.horizontalLayout_2.addWidget(self.okayButton)
        self.cancelButton = QtWidgets.QPushButton(Form)
        self.cancelButton.setObjectName("cancelButton")
        self.horizontalLayout_2.addWidget(self.cancelButton)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.galset_retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def galset_retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.defaultButton.setToolTip(_translate("Form", "Restores all values to their default values"))
        self.defaultButton.setText(_translate("Form", "Restore Defaults"))
        self.setdefaultButton.setToolTip(_translate("Form", "Sets these values as default. Use with caution!"))
        self.setdefaultButton.setText(_translate("Form", "Set as Default"))
        self.okayButton.setToolTip(_translate("Form", "Accept and save the modified values, and quit the menu"))
        self.okayButton.setText(_translate("Form", "Okay"))
        self.cancelButton.setToolTip(_translate("Form", "Cancel any changes made, and quit the menu"))
        self.cancelButton.setText(_translate("Form", "Cancel"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_galvanoForm()
    grp = [
    {'name': 'X-axis settings', 'type': 'group', 'children': [
        {'name': 'Scale', 'type': 'int', 'value': 1 },
        {'name': 'Max', 'type': 'float', 'value': 1, 'suffix':'μm'},
        {'name': 'Min', 'type': 'int', 'value': 1, 'suffix':'μm'},
        {'name': 'Driver division', 'type': 'int', 'value': 1},
        {'name': 'Max speed', 'type': 'int', 'value': 1, 'suffix':'pulses per second'},
        {'name': 'Current speed', 'type': 'int', 'value': 1, 'suffix':'pulses per second'},
        {'name': 'Home Position', 'type': 'int', 'value': 1}]},
    {'name': 'Y-axis settings', 'type': 'group', 'children': [
        {'name': 'Scale', 'type': 'int', 'value': 1 },
        {'name': 'Max', 'type': 'int', 'value': 1, 'suffix':'μm'},
        {'name': 'Min', 'type': 'int', 'value': 1, 'suffix':'μm'},
        {'name': 'Driver division', 'type': 'int', 'value': 1},
        {'name': 'Max speed', 'type': 'int', 'value': 1, 'suffix':'pulses per second'},
        {'name': 'Current speed', 'type': 'int', 'value': 1, 'suffix':'pulses per second'},
        {'name': 'Home Position', 'type': 'int', 'value': 1}]},
    {'name': 'Z-axis settings', 'type': 'group', 'children': [
        {'name': 'Scale', 'type': 'int', 'value': 1 },
        {'name': 'Max', 'type': 'int', 'value': 1, 'suffix':'μm'},
        {'name': 'Min', 'type': 'int', 'value': 1, 'suffix':'μm'},
        {'name': 'Driver division', 'type': 'int', 'value': 1},
        {'name': 'Max speed', 'type': 'int', 'value': 1, 'suffix':'pulses per second'},
        {'name': 'Current speed', 'type': 'int', 'value': 1, 'suffix':'pulses per second'},
        {'name': 'Home Position', 'type': 'int', 'value': 1}]},
    {'name': 'Other settings and device information', 'type': 'group', 'children': [
        {'name': 'Address', 'type': 'str', 'value': 1 },
        ]}]
    ui.galset_setupUi(Form,grp)
    Form.show()
    sys.exit(app.exec_())

