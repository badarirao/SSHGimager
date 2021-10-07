# -*- coding: utf-8 -*-
"""
Created on Fri Feb 19 16:12:32 2021

@author: Badari

TO DO:
    
    Make sure the current speed and home position settings are within the given max, min limits
"""
from galvanometer import Galvano
from nidaqmx import Task, stream_readers, stream_writers
from nidaqmx.constants import AcquisitionType, Edge, CountDirection, Level
from nidaqmx.constants import WAIT_INFINITELY, READ_ALL_AVAILABLE
from nidaqmx.errors import DaqError
from nidaqmx.error_codes import DAQmxErrors
from numpy import linspace, ones, zeros, shape, random, uint32, diff, append
from time import sleep
import os, sys
from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
from ds102_gui import Ui_ds102Form

class ds102setting(QtWidgets.QDialog, Ui_ds102Form):
    def __init__(self,*args, obj=None, **kwargs):
        super().__init__(*args,**kwargs)
        with open('address.txt','r') as f:
            self.setting_address = f.readline()
            self.data_address = f.readline()
        self.filename = "SHG_default_Settings.txt"
        self.load_parameters_from_file()
        self.changed = False
        self.grp = [
    {'name': 'X-axis settings', 'type': 'group', 'children': [
        {'name': 'Scale', 'type': 'int', 'value': self.xscale, 'default': 1 },
        {'name': 'Max (μm)', 'type': 'int', 'value': self.xmax, 'limits':(-24325,27349)},
        {'name': 'Min (μm)', 'type': 'int', 'value': self.xmin, 'limits':(-24326,27348)},
        #{'name': 'Driver division', 'type': 'int', 'value': self.xdd},
        {'name': 'Current speed (pps)', 'type': 'int', 'value': self.xspeed, 'limits':(1,999999), 'default':1000},
        {'name': 'Scanning speed (pps)', 'type': 'int', 'value': self.xscanspeed, 'limits':(1,999999), 'default':100},
        {'name': 'Home Position', 'type': 'int', 'value': self.xhome}]},
    {'name': 'Y-axis settings', 'type': 'group', 'children': [
        {'name': 'Scale', 'type': 'int', 'value': self.yscale, 'default': 1 },
        {'name': 'Max (μm)', 'type': 'int', 'value': self.ymax, 'limits':(-24517,27511)},
        {'name': 'Min (μm)', 'type': 'int', 'value': self.ymin, 'limits':(-24518,27510)},
        #{'name': 'Driver division', 'type': 'int', 'value': self.ydd},
        {'name': 'Current speed (pps)', 'type': 'int', 'value': self.yspeed, 'limits':(1,999999), 'default':1000},
        {'name': 'Scanning speed (pps)', 'type': 'int', 'value': self.yscanspeed, 'limits':(1,999999), 'default':100},
        {'name': 'Home Position', 'type': 'int', 'value': self.yhome}]},
    {'name': 'Z-axis settings', 'type': 'group', 'children': [
        {'name': 'Scale', 'type': 'int', 'value': self.zscale, 'default': 1 },
        {'name': 'Max (μm)', 'type': 'int', 'value': self.zmax, 'limits':(-7304,10786)},
        {'name': 'Min (μm)', 'type': 'int', 'value': self.zmin, 'limits':(-7305,10785)},
        #{'name': 'Driver division', 'type': 'int', 'value': self.zdd},
        {'name': 'Current speed (pps)', 'type': 'int', 'value': self.zspeed, 'limits':(1,999999), 'default':1000},
        {'name': 'Scanning speed (pps)', 'type': 'int', 'value': self.zscanspeed, 'limits':(1,999999), 'default':100},
        {'name': 'Home Position', 'type': 'int', 'value': self.zhome}]},
    {'name': 'Other settings and device information', 'type': 'group', 'children': [
        {'name': 'Address', 'type': 'str', 'value': self.com },
        ]}]
        self.ds102_setupUi(self,self.grp)
        self.setWindowTitle("Sample Stage Settings")
        self.cancelButton.clicked.connect(self.cancel_ds102setting)
        self.okayButton.clicked.connect(self.okay_ds102setting)
        
    def load_parameters_from_file(self):
        if os.path.isdir(self.setting_address):
            os.chdir(self.setting_address)
        if os.path.isfile(self.filename):
            params = {}
            with open(self.filename,'r') as file:
                lines = file.readlines()
                slines = lines[11:30]
                for line in slines:
                    lp = line.split()
                    if lp[0] == 'address':
                        params[lp[0]] = lp[2]
                    else:
                        params[lp[0]] = int(lp[2])
                self.xscale = params['xscale']
                self.yscale = params['yscale']
                self.zscale = params['zscale']
                self.xmax = params['xmax']
                self.xmin = params['xmin']
                self.ymax = params['ymax']
                self.ymin = params['ymin']
                self.zmax = params['zmax']
                self.zmin = params['zmin']
                self.xspeed = params['xspeed']
                self.xscanspeed = params['xscanspeed']
                self.yspeed = params['yspeed']
                self.yscanspeed = params['yscanspeed']
                self.zspeed = params['zspeed']
                self.zscanspeed = params['zscanspeed']
                self.xhome = params['xhome']
                self.yhome = params['yhome']
                self.zhome = params['zhome']
                self.com = params['address']
        else:
            self.xscale = 1
            self.yscale = 1
            self.zscale = 1
            self.xmax = 27349  #mechanical limit
            self.xmin = -24326  #mechanical limit
            self.ymax = 27511   #mechanical limit
            self.ymin = -24518
            self.zmax = 10786
            self.zmin = -7305
            self.xspeed = 1000
            self.xscanspeed = 100
            self.yspeed = 1000
            self.yscanspeed = 100
            self.zspeed = 1000
            self.zscanspeed = 100
            self.xhome = 0
            self.yhome = 0
            self.zhome = 0
            self.com = 'com8'
        if os.path.isdir(self.data_address):
            os.chdir(self.data_address)
            
    def okay_ds102setting(self):
        self.xscale = self.p.child('X-axis settings').child('Scale').value()
        self.yscale = self.p.child('Y-axis settings').child('Scale').value()
        self.zscale = self.p.child('Z-axis settings').child('Scale').value()
        self.xmax = self.p.child('X-axis settings').child('Max (μm)').value()
        self.xmin = self.p.child('X-axis settings').child('Min (μm)').value()
        self.ymax = self.p.child('Y-axis settings').child('Max (μm)').value()
        self.ymin = self.p.child('Y-axis settings').child('Min (μm)').value()
        self.zmax = self.p.child('Z-axis settings').child('Max (μm)').value()
        self.zmin = self.p.child('Z-axis settings').child('Min (μm)').value()
        #self.xdd = self.p.child('X-axis settings').child('Driver division').value()
        #self.ydd = self.p.child('Y-axis settings').child('Driver division').value()
        #self.zdd = self.p.child('Z-axis settings').child('Driver division').value()
        self.xspeed = self.p.child('X-axis settings').child('Current speed (pps)').value()
        self.xscanspeed = self.p.child('X-axis settings').child('Scanning speed (pps)').value()
        self.yspeed = self.p.child('Y-axis settings').child('Current speed (pps)').value()
        self.yscanspeed = self.p.child('Y-axis settings').child('Scanning speed (pps)').value()
        self.zspeed = self.p.child('Z-axis settings').child('Current speed (pps)').value()
        self.zscanspeed = self.p.child('Z-axis settings').child('Scanning speed (pps)').value()
        self.xhome = self.p.child('X-axis settings').child('Home Position').value()
        self.yhome = self.p.child('Y-axis settings').child('Home Position').value()
        self.zhome = self.p.child('Z-axis settings').child('Home Position').value()
        self.com = self.p.child('Other settings and device information').child('Address').value()
        self.changed = True
        self.accept()
    
    def cancel_ds102setting(self):
        self.changed = False
        self.p.child('X-axis settings').child('Scale').setValue(self.xscale)
        self.p.child('Y-axis settings').child('Scale').setValue(self.yscale)
        self.p.child('Z-axis settings').child('Scale').setValue(self.zscale)
        self.p.child('X-axis settings').child('Max (μm)').setValue(self.xmax)
        self.p.child('X-axis settings').child('Min (μm)').setValue(self.xmin)
        self.p.child('Y-axis settings').child('Max (μm)').setValue(self.ymax)
        self.p.child('Y-axis settings').child('Min (μm)').setValue(self.ymin)
        self.p.child('Z-axis settings').child('Max (μm)').setValue(self.zmax)
        self.p.child('Z-axis settings').child('Min (μm)').setValue(self.zmin)
        #self.xdd = self.p.child('X-axis settings').child('Driver division').value()
        #self.ydd = self.p.child('Y-axis settings').child('Driver division').value()
        #self.zdd = self.p.child('Z-axis settings').child('Driver division').value()
        self.p.child('X-axis settings').child('Current speed (pps)').setValue(self.xspeed)
        self.p.child('X-axis settings').child('Scanning speed (pps)').setValue(self.xscanspeed)
        self.p.child('Y-axis settings').child('Current speed (pps)').setValue(self.yspeed)
        self.p.child('Y-axis settings').child('Scanning speed (pps)').setValue( self.yscanspeed)
        self.p.child('Z-axis settings').child('Current speed (pps)').setValue(self.zspeed)
        self.p.child('Z-axis settings').child('Scanning speed (pps)').setValue(self.zscanspeed)
        self.p.child('X-axis settings').child('Home Position').setValue(self.xhome)
        self.p.child('Y-axis settings').child('Home Position').setValue(self.yhome)
        self.p.child('Z-axis settings').child('Home Position').setValue(self.zhome)
        self.p.child('Other settings and device information').child('Address').setValue(self.com)
        self.close()
    
def main():
    app = QtWidgets.QApplication(sys.argv)
    st = ds102setting()
    st.show()
    #main.connect_instrument()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
        