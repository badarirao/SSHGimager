# -*- coding: utf-8 -*-
"""
Created on Thu Oct  7 15:50:23 2021

@author: Badari
"""
from datetime import datetime
from PyQt5.QtCore import QThread, QEventLoop, QTimer
from os.path import abspath, join, exists
from pyvisa import ResourceManager, VisaIOError
from os import makedirs
from copy import copy
from re import sub
from sys import exit as exitprogram
from serial import SerialException
from nidaqmx.errors import DaqError
from galvanometer import Scan
from ds102 import DS102

class Select:
    X_Scan_Continuous_Galvano = 1
    X_Scan_Step_Galvano = 2 #not used
    X_Scan_Continuous_Stage = 3 #not used
    X_Scan_Step_Stage = 4
    
    Y_Scan_Continuous_Galvano = 5
    Y_Scan_Step_Galvano = 6 #not used
    Y_Scan_Continuous_Stage = 7 #not used
    Y_Scan_Step_Stage = 8
    
    #Z_Scan_Continuous_Galvano = 9 # not available
    #Z_Scan_Step_Galvano = 10 # not available
    Z_Scan_Continuous_Stage = 11 #not used
    Z_Scan_Step_Stage = 12 
    
    YZ_Scan_Continuous_Galvano = 13
    YZ_Scan_Step_Galvano = 14 #not used
    YZ_Scan_Continuous_Stage = 15 #not used
    YZ_Scan_Step_Stage = 16
    
    ZY_Scan_Continuous_Galvano = 17
    ZY_Scan_Step_Galvano = 18 #not used
    ZY_Scan_Continuous_Stage = 19 #not used
    ZY_Scan_Step_Stage = 20
    
    XZ_Scan_Continuous_Galvano = 21
    XZ_Scan_Step_Galvano = 22 #not used
    XZ_Scan_Continuous_Stage = 23 #not used
    XZ_Scan_Step_Stage = 24
    
    ZX_Scan_Continuous_Galvano = 25
    ZX_Scan_Step_Galvano = 26 #not used
    ZX_Scan_Continuous_Stage = 27 #not used
    ZX_Scan_Step_Stage = 28
    
    XY_Scan_Continuous_Galvano = 29
    XY_Scan_Step_Galvano = 30 #not used
    XY_Scan_Continuous_Stage = 31 #not used
    XY_Scan_Step_Stage = 32
    
    YX_Scan_Continuous_Galvano = 33
    YX_Scan_Step_Galvano = 34 #not used
    YX_Scan_Continuous_Stage = 35 #not used
    YX_Scan_Step_Stage = 36
    
    # Z is always the last axis order
    XYZ_Scan_Continuous_Galvano = 37  # Z is stage scan
    XYZ_Scan_Step_Galvano = 38 #not used
    XYZ_Scan_Continuous_Stage = 39 #not used
    XYZ_Scan_Step_Stage = 40
    
    YXZ_Scan_Continuous_Galvano = 41  # Z is stage scan
    YXZ_Scan_Step_Galvano = 42 #not used
    YXZ_Scan_Continuous_Stage = 43 #not used
    YXZ_Scan_Step_Stage = 44
    
    
class MonitorStage(QThread):
    def __init__(self, Stage, parent=None):
        QThread.__init__(self,parent)
        self.Stage = Stage
        
    def run(self):
        loop = QEventLoop()
        if self.Stage.ID == 'Fake':
            QTimer.singleShot(5000, loop.quit)
            loop.exec_()
        else:
            while self.Stage.is_xmoving() or self.Stage.is_ymoving() or self.Stage.is_zmoving():
                QTimer.singleShot(100, loop.quit)
                loop.exec_()

class FakeDAQ():
    """Provides a fake adapter for debugging purposes.

    Bounces back the command so that arbitrary values testing is possible.

    Note: Adopted from Pymeasure package

    .. code-block:: python

        a = FakeAdapter()
        assert a.read() == ""
        a.write("5")
        assert a.read() == "5"
        assert a.read() == ""
        assert a.ask("10") == "10"
        assert a.values("10") == [10]

    """

    _buffer = ""

    def __init__(self):
        self.address = ''
        self.x = 0
        self.y = 0
        self.z = 0
        self.ID = 'Fake'

    def read(self):
        """Return last commands given after the last read call."""
        result = copy(self._buffer)
        # Reset the buffer
        self._buffer = ""
        return result

    def write(self, command):
        """Write the command to a buffer, so that it can be read back."""
        self._buffer += command

    def __repr__(self):
        """Return the class name as a string."""
        return "<FakeAdapter>"

    def __getattr__(self,name):  
        """If any undefined method is called, do nothing."""
        def method(*args):
            pass
        return method
    
    def set_xspeed(self,F=1):
        pass
    
    def set_yspeed(self,F=1):
        pass
    
    def set_zspeed(self,F=1):
        pass

class FakeDS102():
    """Provides a fake adapter for debugging purposes.

    Bounces back the command so that arbitrary values testing is possible.

    Note: Adopted from Pymeasure package

    .. code-block:: python

        a = FakeAdapter()
        assert a.read() == ""
        a.write("5")
        assert a.read() == "5"
        assert a.read() == ""
        assert a.ask("10") == "10"
        assert a.values("10") == [10]

    """

    _buffer = ""

    def __init__(self):
        self.address = ''
        self.x = 0
        self.y = 0
        self.z = 0
        self.ID = 'Fake'

    def read(self):
        """Return last commands given after the last read call."""
        result = copy(self._buffer)
        # Reset the buffer
        self._buffer = ""
        return result

    def write(self, command):
        """Write the command to a buffer, so that it can be read back."""
        self._buffer += command

    def __repr__(self):
        """Return the class name as a string."""
        return "<FakeAdapter>"

    def __getattr__(self,name):  
        """If any undefined method is called, do nothing."""
        def method(*args):
            pass
        return method
    
    def set_xspeed(self,F=1):
        pass
    
    def set_yspeed(self,F=1):
        pass
    
    def set_zspeed(self,F=1):
        pass

def unique_filename(directory, prefix='DATA', suffix='', ext='csv',
                    dated_folder=False, index=True, datetimeformat="%Y-%m-%d"):
    """
    Return a unique filename based on the directory and prefix.

    Note: adopted from Pymeasure Package.
    """
    now = datetime.now()
    directory = abspath(directory)
    if dated_folder:
        directory = join(directory, now.strftime('%Y-%m-%d'))
    if not exists(directory):
        makedirs(directory)
    if index:
        i = 1
        basename = "%s%s" % (prefix, now.strftime(datetimeformat))
        basepath = join(directory, basename)
        filename = "%s_%d%s.%s" % (basepath, i, suffix, ext)
        while exists(filename):
            i += 1
            filename = "%s_%d%s.%s" % (basepath, i, suffix, ext)
    else:
        basename = "%s%s%s.%s" % (
            prefix, now.strftime(datetimeformat), suffix, ext)
        filename = join(directory, basename)
    return filename


def get_valid_filename(s):
    """
    Check if given filename is valid, and correct it if its not.

    Parameters
    ----------
    s : string
        file-name

    Returns
    -------
    string
        Valid file-name

    """
    s = str(s).strip().replace(' ', '_')
    return sub(r'(?u)[^-\w.]', '', s)


def connectDevice(inst,addr,test = False):
    """
    try:
        return inst(addr), 1
    except VisaIOError:
        if test == True:
            return FakeAdapter(), 0
        else:
            # TODO: prompt a gui message instead
            print("Instrument not connected! Check connections!")
            exitprogram()
    """
    pass
        
def checkInstrument(ds102Port = None, test = False):
    try:
        gal = Scan()
    except DaqError:
        gal = FakeDAQ()
    try:
        stage = DS102(ds102Port)
    except (SerialException, ValueError):
        import serial.tools.list_ports as portlist
        stageConnected = False
        availablePorts = [comport.device for comport in portlist.comports()]
        for port in availablePorts:
            try:
                stage = DS102(port)
                stageConnected = True
            except ValueError:
                pass
        if stageConnected == False:
            stage = FakeDS102()
        
    return gal,stage
    """
    Obtain instrument address of K2450, K2700 and function generator.

    Returns: list of instrument objects
    -------
    Instrument objects pointing to K2450, K2700 and AFG1022
    if test is True,
        return FakeAdapter if any instrument is not found
    else exit program
    
    deviceAddr = [k2450Addr,k2700Addr,AFG1022Addr]
    rm = ResourceManager()
    k2450Status = k2700Status = afgStatus = 0
    if k2450Addr:
        k2450, k2450Status = connectDevice(Keithley2450,k2450Addr,test=True)
    if k2700Addr:
        k2700, k2700Status = connectDevice(Keithley2700,k2700Addr,test=True)
    if AFG1022Addr:
        afg, afgStatus = connectDevice(AFG1022,AFG1022Addr,test=True)
    status = [k2450Status,k2700Status,afgStatus]
    deviceInfo = [['KEITHLEY','2450'],['KEITHLEY','2700'],['TEKTRONIX','AFG1022']]
    notConnected = [x for x,y in enumerate(status) if y == 0]
    if notConnected:
        instList = rm.list_resources()
        for inst in instList:
            for deviceNo in notConnected:
                try:
                    myInst = rm.open_resource(inst)
                    instID = myInst.query('*IDN?').split(',')
                    if deviceInfo[deviceNo][0] in instID[0] and deviceInfo[deviceNo][1] in instID[1]:
                        deviceAddr[deviceNo] = inst
                        notConnected.remove(deviceNo)
                        break
                except VisaIOError:
                    pass
        k2450Addr = deviceAddr[0]
        k2700Addr = deviceAddr[1]
        AFG1022Addr = deviceAddr[2]
        if k2450Status == 0:
                k2450,_ = connectDevice(Keithley2450,k2450Addr,test)
        if k2700Status == 0:
            k2700,_ = connectDevice(Keithley2700,k2700Addr,test)
        if afgStatus == 0:
            afg,_ = connectDevice(AFG1022,AFG1022Addr,test)
    return k2450, k2700, afg
    """

"""
def connect_instrument(self):
    try:
        self.create_taskxy()
        self.create_ctr()
        self.create_ref()
    except:
        quit_msg = "Problem Connecting with Instrument. Please check instrument connection and retry"
        reply = QtGui.QMessageBox.question(self, 'Connection Error', 
                 quit_msg, QtGui.QMessageBox.Retry, QtGui.QMessageBox.Close)
        if reply == QtGui.QMessageBox.Close:
            try:
                self.close_channels()
            except AttributeError:
                pass
            sys.exit()
        else:
            self.connect_instrument()
"""