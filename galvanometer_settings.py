# -*- coding: utf-8 -*-
"""
Created on Fri Feb 19 16:12:32 2021

@author: Badari
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
from galset_gui import Ui_galvanoForm

xscale = 1.0
yscale = 1.0
xvmax = 3.0
xvmin = -3.0
yvmax = 3.0
yvmin = -3.0
xmax = 3.0
xmin = -3.0
ymax = 3.0
ymin = -3.0

def item(name, value='', values=None, **kwargs):
    """Add an item to a parameter tree.

    Parameters
    ----------
    name : str
        Name of parameter
    value : object
        Default value for object.  If 'type' is not given,
        the type of this object is used to infer the 'type'
    values : list
        Allowable values.  If 'type' is not given, and 'values' are given,
        `type` will be assumed to be `list`.
    **kwargs
        Additional keyword arguments, such as

        type : str, The type of parameter (e.g. 'action' or 'text')
        step : int, The spinbox stepsize
        suffix : str, modifier suffix (e.g. 'Hz' or 'V')
        siPrefix : bool, whether to add an SI prefix ('e.g. mV or MHz')
    """
    if 'type' not in kwargs:
        if values:
            kwargs['type'] = 'list'
        elif isinstance(value, bool):
            kwargs['type'] = 'bool'
        elif isinstance(value, int):
            kwargs['type'] = 'int'
        elif isinstance(value, float):
            kwargs['type'] = 'float'
        else:
            kwargs['type'] = 'str'
    return dict(name=name, value=value, values=values, **kwargs)

class galsetting(QtWidgets.QDialog, Ui_galvanoForm):
    def __init__(self,*args, obj=None, **kwargs):
        super(galsetting,self).__init__(*args,**kwargs)
        with open('address.txt','r') as f:
            self.setting_address = f.readline()
            self.data_address = f.readline()
        self.filename = "SHG_default_Settings.txt"
        self.load_parameters_from_file()
        self.changed = False
        self.grp = [item('X-axis Scale     :', self.xscale, suffix='V = 1 μm',limits=(0.00000001,100000000), siPrefix=True),
           item('X-axis V max   :', self.xvmax, suffix= 'V',limits=(-10,10)),
           item('X-axis V min    :', self.xvmin, suffix = 'V',limits=(-10,10)),
           item('Set x-axis position:', self.xpos, suffix = 'V',siPrefix=True),#
           item('X-axis max       :', self.xmax, suffix= 'μm',readonly=True), #
           item('X-axis min       :', self.xmin, suffix = 'μm',readonly=True),#
           item('Y-axis Scale     :', self.yscale, suffix='V = 1 μm', limits=(0.00000001,100000000), siPrefix=True),
           item('Y-axis V max   :', self.yvmax, suffix= 'V',limits=(-10,10)),#
           item('Y-axis V min    :', self.yvmin, suffix = 'V',limits=(-10,10)),#
           item('Set y-axis position:', self.ypos, suffix = 'V',siPrefix=True),#
           item('Y-axis max       :', self.ymax, suffix= 'μm',readonly=True),
           item('Y-axis min        :', self.ymin, suffix = 'μm',readonly=True)]
        self.galset_setupUi(self,self.grp)
        #self.p.child('X-axis max       :').setStepType(QAbstractSpinBox.AdaptiveDecimalStepType) 
        self.setWindowTitle("Galvanometer Settings")
        self.cancelButton.clicked.connect(self.cancel_galsetting)
        self.okayButton.clicked.connect(self.okay_galsetting)
        self.treeWidget.paramSet.sigTreeStateChanged.connect(self.galsetchange)
        
        
    def load_parameters_from_file(self):
        if os.path.isdir(self.setting_address):
            os.chdir(self.setting_address)
        if os.path.isfile(self.filename):
            params = {}
            with open(self.filename,'r') as file:
                lines = file.readlines()
                glines = lines[1:9]
                for line in glines:
                    lp = line.split()
                    params[lp[0]] = float(lp[2])
                self.xscale = params['x_scale']
                self.yscale = params['y_scale']
                self.xvmax = params['x_vmax']
                self.xvmin = params['x_vmin']
                self.yvmax = params['y_vmax']
                self.yvmin = params['y_vmin']
                self.xmax = self.xvmax/self.xscale
                self.xmin = self.xvmin/self.xscale
                self.ymax = self.yvmax/self.xscale
                self.ymin = self.yvmin/self.xscale
                self.xpos = params['x_pos']
                self.ypos = params['y_pos']
        else:
            self.xscale = 1.0
            self.yscale = 1.0
            self.xvmax = 3.0
            self.xvmin = -3.0
            self.yvmax = 3.0
            self.yvmin = -3.0
            self.xmax = 3.0
            self.xmin = -3.0
            self.ymax = 3.0
            self.ymin = -3.0
            self.xpos = 0.0
            self.ypos = 0.0
        if os.path.isdir(self.data_address):
            os.chdir(self.data_address)
            
    def galsetchange(self,param,changes):
        for par, change, data in changes:
            if par.name() == 'X-axis V max   :':
                self.p.child('X-axis max       :').setValue(data/self.p.child('X-axis Scale     :').value())
            elif par.name() == 'X-axis V min    :':
                self.p.child('X-axis min       :').setValue(data/self.p.child('X-axis Scale     :').value())
            elif par.name() == 'Y-axis V max   :':
                self.p.child('Y-axis max       :').setValue(data/self.p.child('Y-axis Scale     :').value())
            elif par.name() == 'Y-axis V min    :':
                self.p.child('Y-axis min        :').setValue(data/self.p.child('Y-axis Scale     :').value())
            elif par.name() == 'X-axis Scale     :':
                self.p.child('X-axis max       :').setValue(self.p.child('X-axis V max   :').value()/data)
                self.p.child('X-axis min       :').setValue(self.p.child('X-axis V min    :').value()/data)
            elif par.name() == 'Y-axis Scale     :':
                self.p.child('Y-axis max       :').setValue(self.p.child('Y-axis V max   :').value()/data)
                self.p.child('Y-axis min        :').setValue(self.p.child('Y-axis V min    :').value()/data)
                
    def okay_galsetting(self):
        self.xscale = self.p.child('X-axis Scale     :').value()
        self.yscale = self.p.child('Y-axis Scale     :').value()
        self.xvmax = self.p.child('X-axis V max   :').value()
        self.xvmin = self.p.child('X-axis V min    :').value()
        self.yvmax = self.p.child('Y-axis V max   :').value()
        self.yvmin = self.p.child('Y-axis V min    :').value()
        self.xmax = self.p.child('X-axis max       :').value()
        self.xmin = self.p.child('X-axis min       :').value()
        self.ymax = self.p.child('Y-axis max       :').value()
        self.ymin = self.p.child('Y-axis min        :').value()
        self.xpos = self.p.child('Set x-axis position:').value()
        self.ypos = self.p.child('Set y-axis position:').value()
        self.changed = True
        self.accept()
        
    def cancel_galsetting(self):
        self.changed = False
        self.p.child('X-axis Scale     :').setValue(self.xscale)
        self.p.child('Y-axis Scale     :').setValue(self.yscale)
        self.p.child('X-axis V max   :').setValue(self.xvmax)
        self.p.child('X-axis V min    :').setValue(self.xvmin)
        self.p.child('Y-axis V max   :').setValue(self.yvmax)
        self.p.child('Y-axis V min    :').setValue(self.yvmin)
        self.p.child('X-axis max       :').setValue(self.xmax)
        self.p.child('X-axis min       :').setValue(self.xmin)
        self.p.child('Y-axis max       :').setValue(self.ymax)
        self.p.child('Y-axis min        :').setValue(self.ymin)
        self.p.child('Set x-axis position:').setValue(self.xpos) 
        self.p.child('Set y-axis position:').setValue(self.ypos)
        self.close()
    
def main():
    app = QtWidgets.QApplication(sys.argv)
    main = galsetting()
    main.show()
    #main.connect_instrument()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()