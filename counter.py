# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'counter_reading.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
from nidaqmx import Task
from nidaqmx.constants import Edge, CountDirection, TerminalConfiguration
import sys, os
from pymeasure.experiment import unique_filename
from numpy import array,savetxt,column_stack

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(533, 165)
        MainWindow.setMinimumSize(QtCore.QSize(533, 165))
        MainWindow.setMaximumSize(QtCore.QSize(533, 165))
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 1, 1, 1)
        self.label_4 = QtWidgets.QLabel(self.centralwidget)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 0, 2, 1, 1)
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 0, 3, 1, 1)
        self.tstep = QtWidgets.QDoubleSpinBox(self.centralwidget)
        self.tstep.setMinimum(0.01)
        self.tstep.setMaximum(100.0)
        self.tstep.setSingleStep(0.01)
        self.tstep.setProperty("value", 0.1)
        self.tstep.setObjectName("tstep")
        self.gridLayout.addWidget(self.tstep, 1, 0, 1, 1)
        self.intensity = QtWidgets.QLabel(self.centralwidget)
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(170, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(170, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(170, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(170, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Window, brush)
        self.intensity.setPalette(palette)
        self.intensity.setAutoFillBackground(True)
        self.intensity.setObjectName("intensity")
        self.gridLayout.addWidget(self.intensity, 1, 1, 1, 1)
        self.intensity_cps = QtWidgets.QLabel(self.centralwidget)
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(189, 218, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(189, 218, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(189, 218, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(189, 218, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Window, brush)
        self.intensity_cps.setPalette(palette)
        self.intensity_cps.setAutoFillBackground(True)
        self.intensity_cps.setObjectName("intensity_cps")
        self.gridLayout.addWidget(self.intensity_cps, 1, 2, 1, 1)
        self.intensity_2 = QtWidgets.QLabel(self.centralwidget)
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 170, 127))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 170, 127))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 170, 127))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 170, 127))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Window, brush)
        self.intensity_2.setPalette(palette)
        self.intensity_2.setAutoFillBackground(True)
        self.intensity_2.setObjectName("intensity_2")
        self.gridLayout.addWidget(self.intensity_2, 1, 3, 1, 1)
        self.startbtn = QtWidgets.QPushButton(self.centralwidget)
        self.startbtn.setObjectName("startbtn")
        self.gridLayout.addWidget(self.startbtn, 2, 0, 1, 1)
        self.stopbtn = QtWidgets.QPushButton(self.centralwidget)
        self.stopbtn.setObjectName("stopbtn")
        self.gridLayout.addWidget(self.stopbtn, 2, 1, 1, 1)
        self.exitbtn = QtWidgets.QPushButton(self.centralwidget)
        self.exitbtn.setObjectName("exitbtn")
        self.gridLayout.addWidget(self.exitbtn, 2, 2, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 533, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.label.setText(_translate("MainWindow", "<html><head/><body><p><span style=\" font-size:12pt; font-weight:600;\">Time Step (s)</span></p></body></html>"))
        self.label_2.setText(_translate("MainWindow", "<html><head/><body><p align=\"center\"><span style=\" font-size:12pt; font-weight:600;\">Intensity </span></p><p align=\"center\"><span style=\" font-size:8pt;\">(counts per time step)</span></p></body></html>"))
        self.label_4.setText(_translate("MainWindow", "<html><head/><body><p align=\"center\"><span style=\" font-size:12pt; font-weight:600;\">Intensity (cps)</span></p></body></html>"))
        self.label_3.setText(_translate("MainWindow", "<html><head/><body><p align=\"center\"><span style=\" font-size:12pt; font-weight:600;\">Ref. Intensity (μV)</span></p></body></html>"))
        self.intensity.setText(_translate("MainWindow", "<html><head/><body><p align=\"center\">N/A</p></body></html>"))
        self.intensity_cps.setText(_translate("MainWindow", "<html><head/><body><p align=\"center\">N/A</p></body></html>"))
        self.intensity_2.setText(_translate("MainWindow", "<html><head/><body><p align=\"center\">N/A</p></body></html>"))
        self.startbtn.setText(_translate("MainWindow", "Start"))
        self.stopbtn.setText(_translate("MainWindow", "Stop"))
        self.exitbtn.setText(_translate("MainWindow", "Exit"))

class ctrview(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self,*args, obj=None, **kwargs):
        super().__init__(*args,**kwargs)
        self.setupUi(self)
        self.update_tstep()
        self.tstep.setKeyboardTracking(False)
        self.tstep.valueChanged.connect(self.update_tstep)
        self.startbtn.clicked.connect(self.show_data)
        self.stopbtn.clicked.connect(self.stop_ctr)
        self.exitbtn.clicked.connect(self.exitprog)
        self.exitbtn.setShortcut('Ctrl+Q')
        self.exitbtn.setStatusTip('Exit application')
        self.cdata = [0]
        self.tdata = [0]
        self.rdata = [0]
        self.counter = Task()
        self.counter.ci_channels.add_ci_count_edges_chan('Dev1/ctr0',initial_count=0,edge=Edge.RISING,count_direction=CountDirection.COUNT_UP)
        self.counter.channels.ci_count_edges_term = '/Dev1/PFI0'
        self.reference = Task()
        self.reference.ai_channels.add_ai_voltage_chan('Dev1/ai0',terminal_config = TerminalConfiguration.RSE, min_val = 0, max_val = 2)
        self.reference.channels.ai_rng_high = 0.2
        self.reference.channels.ai_rng_low = -0.2
            
    def update_tstep(self):
        self.ts = self.tstep.value()
    
    def show_data(self):
        self.tstep.setEnabled(False)
        self.ctr = 0
        self.cps = 0
        self.ref = 0
        self.intensity.setText(str(self.ctr))
        self.intensity_cps.setText(str(self.cps))
        self.timer = QtCore.QTimer()
        self.timecount = QtCore.QElapsedTimer()
        self.timer.setInterval(int(self.ts*1000))
        self.timer.timeout.connect(self.update_ctr_data)
        self.timer.start()
        self.timecount.start()
        self.counter.start()
        self.reference.start()
        
    def update_ctr_data(self):
        self.ctr = self.counter.read()
        self.ref = self.reference.read()
        self.counter.stop()
        self.reference.stop()
        self.cps = self.ctr/self.ts
        self.intensity.setText(str(self.ctr))
        self.intensity_cps.setText(str(self.cps))
        self.intensity_2.setText("{:.4f}".format(self.ref*1000000))
        self.cdata.append(self.ctr)
        self.tdata.append(self.tdata[-1]+self.ts)
        self.rdata.append(self.ref)
        self.counter.start()
        self.reference.start()
        
    def stop_ctr(self):
        self.timer.stop()
        self.counter.stop()
        self.reference.stop()
        self.tstep.setEnabled(True)
        filename = 'counterdata.txt'
        self.cdata = array(self.cdata)
        self.tdata = array(self.tdata)
        self.rdata = array(self.rdata)
        whole_data = column_stack((self.tdata,self.cdata,self.rdata))
        self.cdata = [0]
        self.tdata = [0]
        self.rdata = [0]
        savetxt(filename,whole_data,delimiter='\t')
    
    def exitprog(self):
        self.counter.close()
        self.reference.close()
        QtWidgets.qApp.quit()
    
    def closeEvent(self, event):
        self.counter.close()
        self.reference.close()
        QtWidgets.qApp.quit()
        
def main():
    app = QtWidgets.QApplication(sys.argv)
    os.chdir(os.path.join(os.path.expandvars("%userprofile%"),"Desktop"))
    gui = ctrview()
    gui.show()
    #main.connect_instrument()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

