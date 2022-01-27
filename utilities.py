# -*- coding: utf-8 -*-
"""
Created on Thu Oct  7 15:50:23 2021

@author: Badari
"""
from datetime import datetime
from numpy import append, flip, shape, ones, zeros, random
from PyQt5.QtCore import QThread, QEventLoop, QTimer
from os.path import abspath, join, exists
from os import makedirs
from copy import copy
from re import sub
from serial import SerialException, SerialTimeoutException
from nidaqmx.errors import DaqError
from galvanometer import Scan
from ds102 import DS102
from time import sleep
from glob import glob

# Need to optimize BUF so that image edges are not scarred
BUF = 5


class Select:
    X_Scan_Continuous_Galvano = 1
    X_Scan_Step_Galvano = 2  # not used
    X_Scan_Continuous_Stage = 3  # not used
    X_Scan_Step_Stage = 4

    Y_Scan_Continuous_Galvano = 5
    Y_Scan_Step_Galvano = 6  # not used
    Y_Scan_Continuous_Stage = 7  # not used
    Y_Scan_Step_Stage = 8

    # Z_Scan_Continuous_Galvano = 9 # not available
    # Z_Scan_Step_Galvano = 10 # not available
    Z_Scan_Continuous_Stage = 11  # not used
    Z_Scan_Step_Stage = 12

    YZ_Scan_Continuous_Galvano = 13
    YZ_Scan_Step_Galvano = 14  # not used
    YZ_Scan_Continuous_Stage = 15  # not used
    YZ_Scan_Step_Stage = 16

    ZY_Scan_Continuous_Galvano = 17
    ZY_Scan_Step_Galvano = 18  # not used
    ZY_Scan_Continuous_Stage = 19  # not used
    ZY_Scan_Step_Stage = 20

    XZ_Scan_Continuous_Galvano = 21
    XZ_Scan_Step_Galvano = 22  # not used
    XZ_Scan_Continuous_Stage = 23  # not used
    XZ_Scan_Step_Stage = 24

    ZX_Scan_Continuous_Galvano = 25
    ZX_Scan_Step_Galvano = 26  # not used
    ZX_Scan_Continuous_Stage = 27  # not used
    ZX_Scan_Step_Stage = 28

    XY_Scan_Continuous_Galvano = 29
    XY_Scan_Step_Galvano = 30  # not used
    XY_Scan_Continuous_Stage = 31  # not used
    XY_Scan_Step_Stage = 32

    YX_Scan_Continuous_Galvano = 33
    YX_Scan_Step_Galvano = 34  # not used
    YX_Scan_Continuous_Stage = 35  # not used
    YX_Scan_Step_Stage = 36

    # Z is always the last axis order
    XYZ_Scan_Continuous_Galvano = 37  # Z is stage scan
    XYZ_Scan_Step_Galvano = 38  # not used
    XYZ_Scan_Continuous_Stage = 39  # not used
    XYZ_Scan_Step_Stage = 40

    YXZ_Scan_Continuous_Galvano = 41  # Z is stage scan
    YXZ_Scan_Step_Galvano = 42  # not used
    YXZ_Scan_Continuous_Stage = 43  # not used
    YXZ_Scan_Step_Stage = 44

    # Special scan for reflection mode
    ZXY_Scan_Step_Stage = 45
    ZYX_Scan_Step_Stage = 46

    def scanName(ID):
        if ID == 1:
            return 'X_Scan_Continuous_Galvano'
        elif ID == 2:
            return 'X_Scan_Step_Galvano'
        elif ID == 3:
            return 'X_Scan_Continuous_Stage'
        elif ID == 4:
            return 'X_Scan_Step_Stage'
        elif ID == 5:
            return 'Y_Scan_Continuous_Galvano'
        elif ID == 6:
            return 'Y_Scan_Step_Galvano'
        elif ID == 7:
            return 'Y_Scan_Continuous_Stage'
        elif ID == 8:
            return 'Y_Scan_Step_Stage'
        elif ID == 9:
            return 'Z_Scan_Continuous_Galvano'
        elif ID == 10:
            return 'Z_Scan_Step_Galvano = 10'
        elif ID == 11:
            return 'Z_Scan_Continuous_Stage'
        elif ID == 12:
            return 'Z_Scan_Step_Stage'
        elif ID == 13:
            return 'YZ_Scan_Continuous_Galvano'
        elif ID == 14:
            return 'YZ_Scan_Step_Galvano'
        elif ID == 15:
            return 'YZ_Scan_Continuous_Stage'
        elif ID == 16:
            return 'YZ_Scan_Step_Stage'
        elif ID == 17:
            return 'ZY_Scan_Continuous_Galvano'
        elif ID == 18:
            return 'ZY_Scan_Step_Galvano'
        elif ID == 19:
            return 'ZY_Scan_Continuous_Stage'
        elif ID == 20:
            return 'ZY_Scan_Step_Stage'
        elif ID == 21:
            return 'XZ_Scan_Continuous_Galvano'
        elif ID == 22:
            return 'XZ_Scan_Step_Galvano'
        elif ID == 23:
            return 'XZ_Scan_Continuous_Stage'
        elif ID == 24:
            return 'XZ_Scan_Step_Stage'
        elif ID == 25:
            return 'ZX_Scan_Continuous_Galvano'
        elif ID == 26:
            return 'ZX_Scan_Step_Galvano'
        elif ID == 27:
            return 'ZX_Scan_Continuous_Stage'
        elif ID == 28:
            return 'ZX_Scan_Step_Stage'
        elif ID == 29:
            return 'XY_Scan_Continuous_Galvano'
        elif ID == 30:
            return 'XY_Scan_Step_Galvano'
        elif ID == 31:
            return 'XY_Scan_Continuous_Stage'
        elif ID == 32:
            return 'XY_Scan_Step_Stage'
        elif ID == 33:
            return 'YX_Scan_Continuous_Galvano'
        elif ID == 34:
            return 'YX_Scan_Step_Galvano'
        elif ID == 35:
            return 'YX_Scan_Continuous_Stage'
        elif ID == 36:
            return 'YX_Scan_Step_Stage'
        elif ID == 37:
            return 'XYZ_Scan_Continuous_Galvano'
        elif ID == 38:
            return 'XYZ_Scan_Step_Galvano'
        elif ID == 39:
            return 'XYZ_Scan_Continuous_Stage'
        elif ID == 40:
            return 'XYZ_Scan_Step_Stage'
        elif ID == 41:
            return 'YXZ_Scan_Continuous_Galvano'
        elif ID == 42:
            return 'YXZ_Scan_Step_Galvano'
        elif ID == 43:
            return 'YXZ_Scan_Continuous_Stage'
        elif ID == 44:
            return 'YXZ_Scan_Step_Stage'
        elif ID == 45:
            return 'ZXY_Scan_Step_Stage'
        elif ID == 46:
            return 'ZYX_Scan_Step_Stage'


class MonitorStage(QThread):
    def __init__(self, Stage, parent=None):
        QThread.__init__(self, parent)
        self.Stage = Stage

    def run(self):
        loop = QEventLoop()
        if self.Stage.ID == 'Fake':
            QTimer.singleShot(1000, loop.quit)
            loop.exec_()
        else:
            while self.Stage.is_xmoving() or self.Stage.is_ymoving() or self.Stage.is_zmoving():
                QTimer.singleShot(100, loop.quit)
                loop.exec_()


class Dummy():
    def __init__(self):
        pass

    def __getattr__(self, name):
        """If any undefined method is called, do nothing."""
        def method(*args):
            pass
        return method

    def read(self):
        return 1

    def moving(self):
        return 0


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
        self._xscale = 1
        self._yscale = 1
        self._srate = 100
        self._fast_dir = 'x'
        self._x = 0
        self._y = 0
        self.t = 6.78
        self.set_xscan_param()
        self.set_yscan_param()
        self.create_taskxy()
        self.repeatxy = False
        self.repeatx = False
        self.repeaty = False
        self.retrace = 2
        self.sam_pc = 450
        self.xhome = 0
        self.yhome = 0
        self.counter = Dummy()
        self.reference = Dummy()

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

    def __getattr__(self, name):
        """If any undefined method is called, do nothing."""
        def method(*args):
            pass
        return method

    def readCounts(self):
        sleep(0.01)
        refV = random.uniform(0.015, 0.02)*1000000
        if refV < 1000:
            refV = 1
        counts = random.randint(90000, 100000)
        return counts, refV

    def start_scanxy(self, xarr, yarr, retrace=2):
        self.startscan = True
        self.xarr = xarr
        self.yarr = yarr
        self.retrace = retrace
        self.i = 0
        sample = self.getxyarray(self.xarr, self.yarr, retrace)
        self.sampleIndex = self.getxyarray(
            range(len(self.xarr)), range(len(self.yarr)), retrace)
        self.sampleIndex = self.sampleIndex[:, 1:].astype(int)
        self.sam_pc = shape(sample)[1]
        if retrace != 0:
            self.shgData = zeros(self.sam_pc)
            self.refData = -ones(self.sam_pc)
        else:
            self.shgData = zeros(self.sam_pc)
            self.refData = -ones(self.sam_pc)
            self.shgData2 = zeros(self.sam_pc)
            self.refData2 = -ones(self.sam_pc)

    def update_scanxy(self):
        if self.startscan == False:
            return False
        buf = random.randint(5, 10)
        buffer_shg = random.randint(90000, 100000, buf)
        number_of_SHG_samples = len(buffer_shg)
        buffer_ref = 1000000*random.uniform(0.015, 0.02, buf)
        buffer_ref[buffer_ref < 1000] = 1  # to avoid divide by zero error
        if self.i + number_of_SHG_samples > self.sam_pc:
            number_of_SHG_samples = self.sam_pc - self.i
            buffer_shg = buffer_shg[:number_of_SHG_samples]
            buffer_ref = buffer_ref[:number_of_SHG_samples]
        self.shgData[self.i:self.i+number_of_SHG_samples] = buffer_shg
        self.refData[self.i:self.i+number_of_SHG_samples] = buffer_ref
        self.diff_data_shg = self.shgData[1:]
        self.img_dataSHG = zeros((len(self.xarr), len(self.yarr)))
        self.img_dataRef = -ones((len(self.xarr), len(self.yarr)))
        if self.retrace == 0:
            self.img_dataSHG2 = zeros((len(self.xarr), len(self.yarr)))
            self.img_dataRef2 = -ones((len(self.xarr), len(self.yarr)))
        for pos in range(self.sam_pc-1):
            i = self.sampleIndex[0, pos]
            j = self.sampleIndex[1, pos]
            if self.retrace != 0:
                self.img_dataSHG[i, j] = self.diff_data_shg[pos]
                self.img_dataRef[i, j] = self.refData[pos+1]
            else:
                if self.img_dataSHG[i, j] == 0:
                    self.img_dataSHG[i, j] = self.diff_data_shg[pos]
                    self.img_dataRef[i, j] = self.refData[pos+1]
                else:
                    self.img_dataSHG2[i, j] = self.diff_data_shg[pos]
                    self.img_dataRef2[i, j] = self.refData[pos+1]
        self.img_Processed = self.img_dataSHG/self.img_dataRef
        if self.retrace == 0:
            self.img_Processed2 = self.img_dataSHG2/self.img_dataRef2
        self.i += number_of_SHG_samples
        if self.i >= self.sam_pc:
            return False
        return True

    def getxyarray(self, xarr, yarr, retrace=2):
        if self.fast_dir == 'x':
            a1 = xarr
            a2 = yarr
        elif self.fast_dir == 'y':
            a1 = yarr
            a2 = xarr
        if retrace == 1:  # scan each line only in one direction (only trace)
            a1_arr = a1
            a2_arr = a2[0]*ones(len(a1))
            for i in range(len(a2)-1):
                a1_arr = append(a1_arr, a1)
                a2_arr = append(a2_arr, a2[i+1]*ones(len(a1)))
        # scan each line only in opposite direction (only retrace)
        elif retrace == -1:
            a1_arr = flip(a1)
            a2_arr = a2[0]*ones(len(a1))
            for i in range(len(a2)-1):
                a1_arr = append(a1_arr, flip(a1))
                a2_arr = append(a2_arr, a2[i+1]*ones(len(a1)))
        elif retrace == 0:  # scan trace and retrace a line, then go to next line
            a1 = append(a1, flip(a1))
            a1_arr = a1
            a2_arr = a2[0]*ones(len(a1_arr))
            for i in range(len(a2)-1):
                a1_arr = append(a1_arr, a1)
                a2_arr = append(a2_arr, a2[i+1]*ones(len(a1)))
        elif retrace == 2:  # scan trace one line, retrace next line , and so on..
            a1_arr = a1
            a2_arr = a2[0]*ones(len(a1))
            flp = 1
            for i in range(len(a2)-1):
                flp = flp * -1
                if flp == -1:
                    a1_arr = append(a1_arr, flip(a1))
                else:
                    a1_arr = append(a1_arr, a1)
                a2_arr = append(a2_arr, a2[i+1]*ones(len(a1)))
        if self.fast_dir == 'x':
            a1_arr = append(a1_arr[0], a1_arr)
            a2_arr = append(a2_arr[0], a2_arr)
        else:
            temp = copy(a2_arr)
            a2_arr = append(a1_arr[0], a1_arr)
            a1_arr = append(temp[0], temp)
        return append(a1_arr, a2_arr).reshape(2, len(a1_arr))


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
        sleep(0.05)
        return result

    def write(self, command):
        """Write the command to a buffer, so that it can be read back."""
        self._buffer += command
        sleep(0.1)

    def __repr__(self):
        """Return the class name as a string."""
        return "<FakeAdapter>"

    def __getattr__(self, name):
        """If any undefined method is called, do nothing."""
        def method(*args):
            pass
        return method

    def is_xmoving(self):
        return 0

    def is_ymoving(self):
        return 0

    def is_zmoving(self):
        return 0

    def set_xspeed(self, F=1):
        pass

    def set_yspeed(self, F=1):
        pass

    def set_zspeed(self, F=1):
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
        for file in glob(basepath+"*.*"):
            try:
                ind = int(file.split(".")[-2].split("_")[-1])
                if ind > i:
                    i = ind
            except:
                break
        basefilename = "%s_%d%s" % (basepath, i, suffix)
        filename = "%s_%d%s.%s" % (basepath, i, suffix, ext)
        while glob(basefilename+".*"):
            i += 1
            basefilename = "%s_%d%s" % (basepath, i, suffix)
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


def checkInstrument(ds102Port=None, Fake=False):
    if Fake:
        gal = FakeDAQ()
        stage = FakeDS102()
        return gal, stage
    try:
        gal = Scan()
    except (DaqError, FileNotFoundError, AttributeError) as e:
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
            except (ValueError, SerialTimeoutException, SerialException):
                pass
        if stageConnected == False:
            stage = FakeDS102()

    return gal, stage
