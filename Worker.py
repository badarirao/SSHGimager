# -*- coding: utf-8 -*-
"""
Created on Tue Dec  7 16:23:49 2021

@author: Badari
"""
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal
from utilities import Select
from time import sleep
from numpy import linspace, array, ones, ones_like, zeros, savetxt, flip, append
import h5py
import sidpy
import pyNSID
from pymeasure.experiment import unique_filename
from datetime import datetime
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# TODO: galvano - trace, retrace options are yet to be sorted out
# TODO: saving of various kinds of trace, retrace images, especially when retrace = 0

class ScanImage(QObject):
    finished = pyqtSignal()
    initialData = pyqtSignal(list)
    imageData = pyqtSignal(list)
    imageData3D = pyqtSignal(list)
    lineData = pyqtSignal(list)
    stopcall = pyqtSignal()
    go_ahead = pyqtSignal(bool)
    checkRef = pyqtSignal(bool)
    
    def __init__(self, scanParams, Gal, Stage, filename="sample"):
        super(ScanImage,self).__init__()
        self.stopCall = False
        self.go = 0
        self.scanParams = scanParams
        self.Gal = Gal
        self.Stage = Stage
        self.filename = filename
        self.stopcall.connect(self.stopCalled)
        self.go_ahead.connect(self.goAhead)
        self.stopFlag = False
        self.nd = scanParams[0]
        self.scanNum = scanParams[1]
        self.xpos = scanParams[2]
        self.ypos = scanParams[3]
        self.zpos = scanParams[4]
        self.xsize = scanParams[5]
        self.ysize = scanParams[6]
        self.zsize = scanParams[7]
        self.xpoints = scanParams[8]
        self.ypoints = scanParams[9]
        self.zpoints = scanParams[10]
        self.xspeed = scanParams[11]
        self.yspeed = scanParams[12]
        self.zspeed = scanParams[13]
        self.srate = scanParams[14]
        self.xhighspeed = scanParams[15]
        self.yhighspeed = scanParams[16]
        self.zhighspeed = scanParams[17]
        self.scanKind = scanParams[18]
        self.Gal.srate = self.srate
        self.xarr = list(linspace(self.xpos,self.xpos+self.xsize,self.xpoints,dtype=int))
        self.yarr = list(linspace(self.ypos,self.ypos+self.ysize,self.ypoints,dtype=int))
        self.zarr = list(linspace(self.zpos,self.zpos+self.zsize,self.zpoints,dtype=int))
        self.xscale = self.xsize/self.xpoints
        self.yscale = self.ysize/self.ypoints
        self.zscale = self.zsize/self.zpoints
       
    def getScanKind(self,num):
        if num == -1:
            return 'Retrace'
        elif num == 0:
            return 'Trace and Retrace'
        elif num == 1:
            return 'Trace'
        elif num == 2:
            return 'Alternate Trace and Retrace'
        
    def goAhead(self,state):
        if state == True:
            self.go = 1
        else:
            self.go = -1
            
    def stopCalled(self):
        self.stopCall = True
    
    def saveData(self):
        self.xarr = array(self.xarr)
        self.yarr = array(self.yarr)
        self.zarr = array(self.zarr)
        xarr = self.xarr - self.xarr[0]
        yarr = self.yarr - self.yarr[0]
        zarr = self.zarr - self.zarr[0]
        shgData = sidpy.Dataset.from_array(self.shgData.round(6))  # RAW shg signals
        refData = sidpy.Dataset.from_array(self.refData.round(6))  # Reference intensity in μV
        imgData = sidpy.Dataset.from_array(self.imgData.round(6)) # shg/ref signal
        if self.scanKind == 0:
            shgData2 = sidpy.Dataset.from_array(self.shgData2.round(6))  # RAW shg signals
            refData2 = sidpy.Dataset.from_array(self.refData2.round(6))  # Reference intensity in μV
            imgData2 = sidpy.Dataset.from_array(self.imgData2.round(6)) # shg/ref signal
        # Add information about scanning parameters as metadata
        shgData.metadata = {'Scan Type':Select.scanName(self.scanNum),
                            'Scan Kind':self.getScanKind(self.scanKind),
                            'Scan Speed': self.srate,
                            'Date & Time': datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
        if self.nd == 1: # 1D scan data
            shgData.data_type = 'LINE_PLOT'
            refData.data_type = 'LINE_PLOT'
            imgData.data_type = 'LINE_PLOT'
            if self.scanNum in (1,2,3,4): # x-scan
                shgData.set_dimension(0, sidpy.Dimension(xarr, 'aAxis'))
                refData.set_dimension(0, sidpy.Dimension(xarr, 'aAxis'))
                imgData.set_dimension(0, sidpy.Dimension(xarr, 'aAxis'))
                refData.aAxis.quantity = 'x'
                shgData.aAxis.quantity = 'x'
                imgData.aAxis.quantity = 'x'
                shgData.metadata['x-position'] = self.xpos
                shgData.metadata['x-size'] = self.xsize
                shgData.metadata['x-points'] = self.xpoints
            elif self.scanNum in (5,6,7,8): # y-scan
                shgData.set_dimension(0, sidpy.Dimension(yarr, 'aAxis'))
                refData.set_dimension(0, sidpy.Dimension(yarr, 'aAxis'))
                imgData.set_dimension(0, sidpy.Dimension(yarr, 'aAxis'))
                refData.aAxis.quantity = 'y'
                shgData.aAxis.quantity = 'y'
                imgData.aAxis.quantity = 'y'
                shgData.metadata['y-position'] = self.ypos
                shgData.metadata['y-size'] = self.ysize
                shgData.metadata['y-points'] = self.ypoints
            elif self.scanNum in (9,10,11,12): # z-scan
                shgData.set_dimension(0, sidpy.Dimension(zarr, 'aAxis'))
                refData.set_dimension(0, sidpy.Dimension(zarr, 'aAxis'))
                imgData.set_dimension(0, sidpy.Dimension(zarr, 'aAxis'))
                refData.aAxis.quantity = 'z'
                shgData.aAxis.quantity = 'z'
                imgData.aAxis.quantity = 'z'
                shgData.metadata['z-position'] = self.zpos
                shgData.metadata['z-size'] = self.zsize
                shgData.metadata['z-points'] = self.zpoints
        elif self.nd == 2: # 2D scan data
            shgData.data_type = 'IMAGE'
            refData.data_type = 'IMAGE'
            imgData.data_type = 'IMAGE'
            if self.scanNum in range(13,21): 
                shgData.set_dimension(0, sidpy.Dimension(yarr, 'aAxis'))
                shgData.set_dimension(1, sidpy.Dimension(zarr, 'bAxis'))
                refData.set_dimension(0, sidpy.Dimension(yarr, 'aAxis'))
                refData.set_dimension(1, sidpy.Dimension(zarr, 'bAxis'))
                imgData.set_dimension(0, sidpy.Dimension(yarr, 'aAxis'))
                imgData.set_dimension(1, sidpy.Dimension(zarr, 'bAxis'))
                shgData.aAxis.quantity = 'y'
                shgData.bAxis.quantity = 'z'
                refData.aAxis.quantity = 'y'
                refData.bAxis.quantity = 'z'
                imgData.aAxis.quantity = 'y'
                imgData.bAxis.quantity = 'z'
                shgData.metadata['y-position'] = self.ypos
                shgData.metadata['y-size'] = self.ysize
                shgData.metadata['y-points'] = self.ypoints
                shgData.metadata['z-position'] = self.zpos
                shgData.metadata['z-size'] = self.zsize
                shgData.metadata['z-points'] = self.zpoints
            elif self.scanNum in range(21,29): 
                shgData.set_dimension(0, sidpy.Dimension(xarr, 'aAxis'))
                shgData.set_dimension(1, sidpy.Dimension(zarr, 'bAxis'))
                refData.set_dimension(0, sidpy.Dimension(xarr, 'aAxis'))
                refData.set_dimension(1, sidpy.Dimension(zarr, 'bAxis'))
                imgData.set_dimension(0, sidpy.Dimension(xarr, 'aAxis'))
                imgData.set_dimension(1, sidpy.Dimension(zarr, 'bAxis'))
                shgData.aAxis.quantity = 'x'
                shgData.bAxis.quantity = 'z'
                refData.aAxis.quantity = 'x'
                refData.bAxis.quantity = 'z'
                imgData.aAxis.quantity = 'x'
                imgData.bAxis.quantity = 'z'
                shgData.metadata['x-position'] = self.xpos
                shgData.metadata['x-size'] = self.xsize
                shgData.metadata['x-points'] = self.xpoints
                shgData.metadata['z-position'] = self.zpos
                shgData.metadata['z-size'] = self.zsize
                shgData.metadata['z-points'] = self.zpoints
            elif self.scanNum in range(29,37): 
                shgData.set_dimension(0, sidpy.Dimension(xarr, 'aAxis'))
                shgData.set_dimension(1, sidpy.Dimension(yarr, 'bAxis'))
                refData.set_dimension(0, sidpy.Dimension(xarr, 'aAxis'))
                refData.set_dimension(1, sidpy.Dimension(yarr, 'bAxis'))
                imgData.set_dimension(0, sidpy.Dimension(xarr, 'aAxis'))
                imgData.set_dimension(1, sidpy.Dimension(yarr, 'bAxis'))
                shgData.aAxis.quantity = 'x'
                shgData.bAxis.quantity = 'y'
                refData.aAxis.quantity = 'x'
                refData.bAxis.quantity = 'y'
                imgData.aAxis.quantity = 'x'
                imgData.bAxis.quantity = 'y'
                shgData.metadata['x-position'] = self.xpos
                shgData.metadata['x-size'] = self.xsize
                shgData.metadata['x-points'] = self.xpoints
                shgData.metadata['y-position'] = self.ypos
                shgData.metadata['y-size'] = self.ysize
                shgData.metadata['y-points'] = self.ypoints
        elif self.nd == 3: # 3D scan data
            shgData.data_type = 'image_stack'
            refData.data_type = 'image_stack'
            imgData.data_type = 'image_stack'
            if self.scanNum in range(37,45): # xyz-scan
                shgData.set_dimension(0, sidpy.Dimension(zarr, 'cAxis'))
                shgData.set_dimension(1, sidpy.Dimension(xarr, 'aAxis'))
                shgData.set_dimension(2, sidpy.Dimension(yarr, 'bAxis'))
                refData.set_dimension(0, sidpy.Dimension(zarr, 'cAxis'))
                refData.set_dimension(1, sidpy.Dimension(xarr, 'aAxis'))
                refData.set_dimension(2, sidpy.Dimension(yarr, 'bAxis'))
                imgData.set_dimension(0, sidpy.Dimension(zarr, 'cAxis'))
                imgData.set_dimension(1, sidpy.Dimension(xarr, 'aAxis'))
                imgData.set_dimension(2, sidpy.Dimension(yarr, 'bAxis'))
            shgData.aAxis.quantity = 'x'
            refData.aAxis.quantity = 'x'
            imgData.aAxis.quantity = 'x'
            shgData.bAxis.quantity = 'y'
            refData.bAxis.quantity = 'y'
            refData.bAxis.quantity = 'y'
            shgData.cAxis.quantity = 'z'
            refData.cAxis.quantity = 'z'
            refData.cAxis.quantity = 'z'
            shgData.metadata['x-position'] = self.xpos
            shgData.metadata['x-size'] = self.xsize
            shgData.metadata['x-points'] = self.xpoints
            shgData.metadata['y-position'] = self.ypos
            shgData.metadata['y-size'] = self.ysize
            shgData.metadata['y-points'] = self.ypoints
            shgData.metadata['z-position'] = self.zpos
            shgData.metadata['z-size'] = self.zsize
            shgData.metadata['z-points'] = self.zpoints
        try:    
            shgData.aAxis.dimension_type = 'spatial'
            refData.aAxis.dimension_type = 'spatial'
            imgData.aAxis.dimension_type = 'spatial'
            shgData.aAxis.units = 'μm'
            refData.aAxis.units = 'μm'
            imgData.aAxis.units = 'μm'
            shgData.bAxis.dimension_type = 'spatial'
            refData.bAxis.dimension_type = 'spatial'
            imgData.bAxis.dimension_type = 'spatial'
            shgData.bAxis.units = 'μm'
            refData.bAxis.units = 'μm'
            imgData.bAxis.units = 'μm'
            shgData.cAxis.dimension_type = 'spatial'
            refData.cAxis.dimension_type = 'spatial'
            imgData.cAxis.dimension_type = 'spatial'
            shgData.cAxis.units = 'μm'
            refData.cAxis.units = 'μm'
            imgData.cAxis.units = 'μm'
        except Exception:
            pass
        shgData.modality = 'SHG micorscopy Raw Image'
        shgData.title = self.filename+'_shg_RAW'
        shgData.quantity = 'intensity'
        shgData.units = 'counts'
        
        refData.modality = 'SHG micorscopy Reference Intensity data'
        refData.title = self.filename+'_reference'
        refData.quantity = 'intensity'
        refData.units = 'μV'
        imgData.modality = 'SHG micorscopy Processed Image'
        imgData.title = self.filename+'_processed'
        imgData.quantity = 'intensity'
        imgData.units = 'arb.units'
        self.fullfilename = unique_filename(directory='.',prefix=self.filename,datetimeformat="",ext='h5')
        # save all data as HDF5 file
        hf = h5py.File(self.fullfilename,'w')
        hf.create_group('Raw_Data')
        pyNSID.hdf_io.write_nsid_dataset(shgData, hf['Raw_Data'], main_data_name="RAW_SHG")
        hf.create_group('Processed_Data')
        pyNSID.hdf_io.write_nsid_dataset(imgData, hf['Processed_Data'], main_data_name="PROCESSED")
        hf.create_group('Reference_Data')
        pyNSID.hdf_io.write_nsid_dataset(shgData, hf['Reference_Data'], main_data_name="REFERENCE")
        hf.close()
    
    def check_ref_ON(self):
        self.Gal.reference.start()
        ref = self.Gal.reference.read() * 1000000
        self.Gal.reference.stop()
        if  ref < 1000:
            return False
        return True
        
    def startScan(self):
        self.checkRef.emit(self.check_ref_ON())
        while self.go != 1: # wait to get go_ahead signal
            if self.go == -1:
                self.stop_program()
                return
        if self.scanNum == Select.X_Scan_Continuous_Galvano:
            pass
        elif self.scanNum == Select.X_Scan_Step_Galvano:
            pass
        elif self.scanNum == Select.X_Scan_Continuous_Stage:
            pass
        elif self.scanNum == Select.X_Scan_Step_Stage:
            self.initialData.emit(['1D x-scan using Stage', 'x (μm)',self.xpos])
            #self.spinBox_xmove.setValue(int(self.xpos.value()))
            #self.display_stagemove_msg()
            
            self.X_Scan_Step_Stage()
        elif self.scanNum == Select.Y_Scan_Continuous_Galvano:
            pass
        elif self.scanNum == Select.Y_Scan_Step_Galvano:
            pass
        elif self.scanNum == Select.Y_Scan_Continuous_Stage:
            pass
        elif self.scanNum == Select.Y_Scan_Step_Stage:
            #self.spinBox_ymove.setValue(int(self.ypos.value()))
            self.initialData.emit(['1D y-scan using Stage', 'y (μm)',self.ypos])
            self.Stage.set_yspeed(F=int(self.yspeed))                
            #self.display_stagemove_msg()
            
            self.Y_Scan_Step_Stage()
        elif self.scanNum == Select.Z_Scan_Continuous_Stage:
            pass
        elif self.scanNum == Select.Z_Scan_Step_Stage:
            #self.spinBox_zmove.setValue(int(self.zpos))
            self.initialData.emit(['1D z-scan using Stage', 'z (μm)',self.zpos])
            self.Stage.set_zspeed(F=int(self.zspeed))                
            #self.display_stagemove_msg()
            
            self.Z_Scan_Step_Stage()
        elif self.scanNum == Select.YZ_Scan_Continuous_Galvano:
            pass
        elif self.scanNum == Select.YZ_Scan_Step_Galvano:
            pass
        elif self.scanNum == Select.YZ_Scan_Continuous_Stage:
            pass
        elif self.scanNum == Select.YZ_Scan_Step_Stage:
            #self.spinBox_ymove.setValue(int(self.ypos.value()))
            #self.spinBox_zmove.setValue(int(self.zpos.value()))
            #self.display_stagemove_msg()
            self.initialData.emit(['2D YZ-scan using Stage','y (μm)','z (μm)',self.yscale,self.zscale])
            self.YZ_Scan_Step_Stage()
        elif self.scanNum == Select.ZY_Scan_Continuous_Galvano:
            pass
        elif self.scanNum == Select.ZY_Scan_Step_Galvano:
            pass
        elif self.scanNum == Select.ZY_Scan_Continuous_Stage:
            pass
        elif self.scanNum == Select.ZY_Scan_Step_Stage:
            #self.spinBox_ymove.setValue(int(self.ypos.value()))
            #self.spinBox_zmove.setValue(int(self.zpos.value()))
            #self.display_stagemove_msg()
            self.initialData.emit(['2D ZY-scan using Stage', 'y (μm)','z (μm)',self.yscale,self.zscale])
            self.ZY_Scan_Step_Stage()
        elif self.scanNum == Select.XZ_Scan_Continuous_Galvano:
            pass
        elif self.scanNum == Select.XZ_Scan_Step_Galvano:
            pass
        elif self.scanNum == Select.XZ_Scan_Continuous_Stage:
            pass
        elif self.scanNum == Select.XZ_Scan_Step_Stage:
            #self.spinBox_xmove.setValue(int(self.xpos.value()))
            #self.spinBox_zmove.setValue(int(self.zpos.value()))
            #self.display_stagemove_msg()
            self.initialData.emit(['2D XZ-scan using Stage', 'x (μm)','z (μm)',self.xscale,self.zscale])
            self.XZ_Scan_Step_Stage()
        elif self.scanNum == Select.ZX_Scan_Continuous_Galvano:
            pass
        elif self.scanNum == Select.ZX_Scan_Step_Galvano:
            pass
        elif self.scanNum == Select.ZX_Scan_Continuous_Stage:
            pass
        elif self.scanNum == Select.ZX_Scan_Step_Stage:
            #self.spinBox_ymove.setValue(int(self.ypos.value()))
            #self.spinBox_zmove.setValue(int(self.zpos.value()))
            #self.display_stagemove_msg()
            self.initialData.emit(['2D ZX-scan using Stage', 'x (μm)','z (μm)',self.xscale,self.zscale])
            self.ZX_Scan_Step_Stage()
        elif self.scanNum == Select.XY_Scan_Continuous_Galvano:
            self.initialData.emit(['2D XY-scan using Laser', 'x (μm)','y (μm)',self.xscale,self.yscale])
            self.xarr = linspace(-self.xsize/2,self.xsize/2,self.xpoints)
            self.yarr = linspace(-self.ysize/2,self.ysize/2,self.ypoints)
            self.Gal.x = self.xarr[0]+self.Gal.xhome
            self.Gal.y = self.yarr[0]+self.Gal.yhome
            self.Gal.srate = self.srate
            self.XY_Scan_Continuous_Galvano()
            self.Gal.x = self.Gal.xhome
            self.Gal.y = self.Gal.yhome
        elif self.scanNum == Select.XY_Scan_Step_Galvano:
            pass
        elif self.scanNum == Select.XY_Scan_Continuous_Stage:
            pass
        elif self.scanNum == Select.XY_Scan_Step_Stage:
            #self.spinBox_xmove.setValue(int(self.xpos.value()))
            #self.spinBox_ymove.setValue(int(self.ypos.value()))
            #self.display_stagemove_msg()
            self.initialData.emit(['2D XY-scan using Stage', 'x (μm)','y (μm)',self.xscale,self.yscale])
            self.XY_Scan_Step_Stage()
        elif self.scanNum == Select.YX_Scan_Continuous_Galvano:
            self.initialData.emit(['2D YX-scan using Laser', 'x (μm)','y (μm)',self.xscale,self.yscale])
            self.xarr = linspace(-self.xsize/2,self.xsize/2,self.xpoints)
            self.yarr = linspace(-self.ysize/2,self.ysize/2,self.ypoints)
            self.Gal.x = self.xarr[0]+self.Gal.xhome
            self.Gal.y = self.yarr[0]+self.Gal.yhome
            self.Gal.srate = self.srate
            self.YX_Scan_Continuous_Galvano()
            self.Gal.x = self.Gal.xhome
            self.Gal.y = self.Gal.yhome
        elif self.scanNum == Select.YX_Scan_Step_Galvano:
            pass
        elif self.scanNum == Select.YX_Scan_Continuous_Stage:
            pass
        elif self.scanNum == Select.YX_Scan_Step_Stage:
            self.initialData.emit(['2D YX-scan using Stage', 'x (μm)','y (μm)',self.xscale,self.yscale])
            self.YX_Scan_Step_Stage()
        elif self.scanNum == Select.XYZ_Scan_Continuous_Galvano:
            #self.spinBox_zmove.setValue(int(self.zpos.value()))
            self.initialData.emit(['3D XYZ-scan using Laser', 'x (μm)','y (μm)','z (μm)',self.xscale,self.yscale,self.zarr])
            self.Stage.set_zspeed(F=int(self.zspeed))
            #self.display_stagemove_msg()
            self.xarr = linspace(-self.xsize/2,self.xsize/2,self.xpoints,dtype=float)
            self.yarr = linspace(-self.ysize/2,self.ysize/2,self.ypoints,dtype=float)
            self.XYZ_Scan_Continuous_Galvano()
            self.Gal.x = self.Gal.xhome
            self.Gal.y = self.Gal.yhome
        elif self.scanNum == Select.XYZ_Scan_Step_Galvano:
            pass
        elif self.scanNum == Select.XYZ_Scan_Continuous_Stage:
            pass
        elif self.scanNum == Select.XYZ_Scan_Step_Stage:
            #self.spinBox_xmove.setValue(int(self.xpos.value()))
            #self.spinBox_ymove.setValue(int(self.ypos.value()))
            #self.spinBox_zmove.setValue(int(self.zpos.value()))
            #self.display_stagemove_msg()
            self.initialData.emit(['3D XYZ-scan using Stage', 'x (μm)','y (μm)','z (μm)',self.xscale,self.yscale,self.zarr])
            self.XYZ_Scan_Step_Stage()
        elif self.scanNum == Select.YXZ_Scan_Continuous_Galvano:
            #self.spinBox_zmove.setValue(int(self.zpos.value()))
            self.initialData.emit(['3D YXZ-scan using Laser', 'x (μm)','y (μm)','z (μm)',self.xscale,self.yscale,self.zarr])
            self.Stage.set_zspeed(F=int(self.zspeed))
            #self.display_stagemove_msg()
            self.xarr = linspace(-self.xsize/2,self.xsize/2,self.xpoints,dtype=float)
            self.yarr = linspace(-self.ysize/2,self.ysize/2,self.ypoints,dtype=float)
            self.YXZ_Scan_Continuous_Galvano()
        elif self.scanNum == Select.YXZ_Scan_Step_Galvano:
            pass
        elif self.scanNum == Select.YXZ_Scan_Continuous_Stage:
            pass
        elif self.scanNum == Select.YXZ_Scan_Step_Stage:
            self.initialData.emit(['3D YXZ-scan using Stage', 'x (μm)','y (μm)','z (μm)',self.xscale,self.yscale,self.zarr])
            self.YXZ_Scan_Step_Stage()
    
    def scan1D_Stage(self,goto,setSpeed,arr,speed,highSpeed):
        lData = []
        self.shgData = []
        self.refData = []
        self.imgData = []
        if self.scanKind == -1:
            arr.reverse()
        elif self.scanKind in (0,2):
            temp = arr.copy()
            temp.reverse()
            arr.extend(temp)
        goto(arr[0])
        setSpeed(F=int(speed))
        self.Gal.start_single_point_counter()
        for i,q in enumerate(arr):
            goto(q)
            c,r = self.Gal.readCounts()
            img = c/r
            lData.append(q)
            self.shgData.append(c)
            self.refData.append(r)
            self.imgData.append(img)
            self.lineData.emit([lData,self.shgData,self.refData,self.imgData])
            if self.stopCall:
                break
        self.Gal.stop_single_point_counter()
        setSpeed(F=int(highSpeed))
        self.lineData.emit([lData,self.shgData,self.refData,self.imgData])
        self.shgData = array(self.shgData)
        self.refData = array(self.refData)
        self.imgData = array(self.imgData)
        self.saveData()
        self.stop_program()
        
    def X_Scan_Step_Stage(self):
        self.scan1D_Stage(self.Stage.goto_x,self.Stage.set_xspeed,self.xarr,self.xspeed,self.xhighspeed)
        
    def Y_Scan_Step_Stage(self):
        self.scan1D_Stage(self.Stage.goto_y,self.Stage.set_yspeed,self.yarr,self.yspeed,self.yhighspeed)
    
    def Z_Scan_Step_Stage(self):
        self.scan1D_Stage(self.Stage.goto_z,self.Stage.set_zspeed,self.zarr,self.zspeed,self.zhighspeed)
        
    def collect_2DSHG_Signal(self,goto,p,q,i,j):
        goto(p,q)
        c,r = self.Gal.readCounts()
        img = c/r
        self.shgData[i,j] = c
        self.refData[i,j] = r
        self.imgData[i,j] = img
        self.imageData.emit([self.shgData,self.refData,self.imgData])
    
    def collect_2DSHG_secondSignal(self,goto,p,q,i,j):
        goto(p,q)
        c,r = self.Gal.readCounts()
        img = c/r
        self.shgData2[i,j] = c
        self.refData2[i,j] = r
        self.imgData2[i,j] = img
        #self.imageData.emit([self.shgData,self.refData,self.imgData])
        
    def scan2D_Stage(self,goto,arr1,arr2,set1speed,set2speed,speed1,speed2,highspeed1,highspeed2,scanKind,gotoP):
        self.shgData = zeros((len(arr1),len(arr2)))
        self.refData = -ones_like(self.shgData)
        self.imgData = ones_like(self.shgData)
        j = 0
        if scanKind in (0,1,2):
            i = 0
        elif scanKind == -1:
            i = len(arr1)-1
        if scanKind == 0:
            self.shgData2 = zeros((len(arr1),len(arr2)))
            self.refData2 = -ones_like(self.shgData2)
            self.imgData2 = ones_like(self.shgData2)
        p = arr1[i]
        q = arr2[j]
        goto(p,q)
        set2speed(F=int(speed2))
        set1speed(F=int(speed1))
        self.Gal.start_single_point_counter()
        iStart = 0
        iEnd = len(arr1)-1
        if scanKind == 1:
            while True:
                self.collect_2DSHG_Signal(goto,p,q,i,j)
                i += 1
                if i >= len(arr1):
                    j += 1
                    if j >= len(arr2):
                        break
                    set1speed(F=int(highspeed1))
                    gotoP(arr1[0])
                    set1speed(F=int(speed1))
                    i = iStart
                if self.stopCall:
                    break
        elif scanKind == -1:
            while True:
                self.collect_2DSHG_Signal(goto,p,q,i,j)
                i -= 1
                if i < 0:
                    j += 1
                    if j >= len(arr2):
                        break
                    set1speed(F=int(highspeed1))
                    gotoP(arr1[-1])
                    set1speed(F=int(speed1))
                    i = iEnd
                if self.stopCall:
                    break
        elif scanKind == 2:
            while True:
                self.collect_2DSHG_Signal(goto,p,q,i,j)
                if j%2 == 0:
                    i += 1
                    if i >= len(arr1):
                        j += 1
                        if j >= len(arr2):
                            break
                        i = iEnd
                else:
                    i -= 1
                    if i < 0:
                        j += 1
                        if j >= len(arr2):
                            break
                        i = iStart
                if self.stopCall:
                        break
        elif scanKind == 0:
            while True:
                self.collect_2DSHG_Signal(goto,p,q,i,j)
                i += 1
                if i >= len(arr1):
                    i = iEnd
                    while True:
                        self.collect_2DSHG_secondSignal(goto,p,q,i,j)
                        i -= 1
                        if i < 0:
                            j += 1
                            i = iStart
                            break
                        if self.stopCall:
                            break
                    if j >= len(arr2):
                        break
                if self.stopCall:
                    break
        self.Gal.stop_single_point_counter()
        set1speed(F=int(highspeed1))
        set2speed(F=int(highspeed2))
        self.imageData.emit([self.shgData,self.refData,self.imgData])
        self.saveData()
        self.stop_program()
    
    def altScan2D_Stage(self,goto,arr1,arr2,set1speed,set2speed,speed1,speed2,highspeed1,highspeed2,scanKind,gotoQ):
        self.shgData = zeros((len(arr1),len(arr2)))
        self.refData = -ones_like(self.shgData)
        self.imgData = ones_like(self.shgData)
        i = 0
        if scanKind in (0,1,2):
            j = 0
        elif scanKind == -1:
            j = len(arr1)-1
        if scanKind == 0:
            self.shgData2 = zeros((len(arr1),len(arr2)))
            self.refData2 = -ones_like(self.shgData2)
            self.imgData2 = ones_like(self.shgData2)
        p = arr1[i]
        q = arr2[j]
        goto(p,q)
        set1speed(F=int(speed1))
        set2speed(F=int(speed2))
        self.Gal.start_single_point_counter()
        jStart = 0
        jEnd = len(arr2)-1
        if scanKind == 1:
            while True:
                self.collect_2DSHG_Signal(goto,p,q,i,j)
                j += 1
                if j >= len(arr2):
                    i += 1
                    if i >= len(arr1):
                        break
                    set2speed(F=int(highspeed2))
                    gotoQ(arr2[0])
                    set2speed(F=int(speed2))
                    j = jStart
                if self.stopCall:
                    break
        elif scanKind == -1:
            while True:
                self.collect_2DSHG_Signal(goto,p,q,i,j)
                j -= 1
                if j < 0:
                    i += 1
                    if i >= len(arr1):
                        break
                    set2speed(F=int(highspeed2))
                    gotoQ(arr2[-1])
                    set2speed(F=int(speed2))
                    j = jEnd
                if self.stopCall:
                    break
        elif scanKind == 2:
            while True:
                self.collect_2DSHG_Signal(goto,p,q,i,j)
                if i%2 == 0:
                    j += 1
                    if j >= len(arr2):
                        i += 1
                        if i >= len(arr1):
                            break
                        j = jEnd
                else:
                    j -= 1
                    if j < 0:
                        i += 1
                        if i >= len(arr1):
                            break
                        j = jStart
                if self.stopCall:
                        break
        elif scanKind == 0:
            while True:
                self.collect_2DSHG_Signal(goto,p,q,i,j)
                j += 1
                if j >= len(arr2):
                    j = jEnd
                    while True:
                        self.collect_2DSHG_secondSignal(goto,p,q,i,j)
                        j -= 1
                        if j < 0:
                            i += 1
                            j = jStart
                            break
                        if self.stopCall:
                            break
                    if i >= len(arr1):
                        break
                if self.stopCall:
                    break
        self.Gal.stop_single_point_counter()
        set1speed(F=int(highspeed1))
        set2speed(F=int(highspeed2))
        self.imageData.emit([self.shgData,self.refData,self.imgData])
        self.saveData()
        self.stop_program()
    
    def YZ_Scan_Step_Stage(self):
        self.scan2D_Stage(self.Stage.goto_yz,
                          self.yarr,self.zarr,
                          self.Stage.set_yspeed,self.Stage.set_zspeed,
                          self.yspeed,self.zspeed,
                          self.yhighspeed,self.zhighspeed,
                          self.scanKind,self.Stage.goto_y)
    
    def ZY_Scan_Step_Stage(self):
        self.altScan2D_Stage(self.Stage.goto_yz,
                          self.yarr,self.zarr,
                          self.Stage.set_yspeed,self.Stage.set_zspeed,
                          self.yspeed,self.zspeed,
                          self.yhighspeed,self.zhighspeed,
                          self.scanKind,self.Stage.goto_z)
        
    def XZ_Scan_Step_Stage(self):
        self.scan2D_Stage(self.Stage.goto_xz,
                          self.xarr,self.zarr,
                          self.Stage.set_xspeed,self.Stage.set_zspeed,
                          self.xspeed,self.zspeed,
                          self.xhighspeed,self.zhighspeed,
                          self.scanKind,self.Stage.goto_x)
    
    def ZX_Scan_Step_Stage(self):
        self.altScan2D_Stage(self.Stage.goto_xz,
                          self.xarr,self.zarr,
                          self.Stage.set_xspeed,self.Stage.set_zspeed,
                          self.xspeed,self.zspeed,
                          self.xhighspeed,self.zhighspeed,
                          self.scanKind,self.Stage.goto_x)
    
    def XY_Scan_Step_Stage(self):
        self.scan2D_Stage(self.Stage.goto_xy,
                          self.xarr,self.yarr,
                          self.Stage.set_xspeed,self.Stage.set_yspeed,
                          self.xspeed,self.yspeed,
                          self.xhighspeed,self.yhighspeed,
                          self.scanKind,self.Stage.goto_y)
    
    def YX_Scan_Step_Stage(self):
        self.altScan2D_Stage(self.Stage.goto_xy,
                          self.xarr,self.yarr,
                          self.Stage.set_xspeed,self.Stage.set_yspeed,
                          self.xspeed,self.yspeed,
                          self.xhighspeed,self.yhighspeed,
                          self.scanKind,self.Stage.goto_z)
    
    def scan2D_Continuous_Galvano(self):
        self.Gal.start_scanxy(self.xarr,self.yarr,retrace = self.scanKind)
        while True:
            sleep(1)
            if self.stopCall:
                self.Gal.startscan = False
            if self.Gal.update_scanxy():
                self.imageData.emit([self.Gal.img_dataSHG,self.Gal.img_dataRef,self.Gal.img_Processed])
            else:
                self.Gal.stop_scanxy()
                break
        self.imageData.emit([self.Gal.img_dataSHG,self.Gal.img_dataRef,self.Gal.img_Processed])
        self.shgData = self.Gal.img_dataSHG
        self.refData = self.Gal.img_dataRef
        self.imgData = self.Gal.img_Processed
        self.saveData()
        self.stop_program()
        
    def XY_Scan_Continuous_Galvano(self):
        self.Gal.fast_dir = 'x'
        self.scan2D_Continuous_Galvano()
    
    def YX_Scan_Continuous_Galvano(self):
        self.Gal.fast_dir = 'y'
        self.scan2D_Continuous_Galvano()
    
    def Scan3D_Continuous_Galvano(self):
        shgData = zeros((len(self.zarr),len(self.xarr),len(self.yarr)))
        refData = -ones_like(shgData)
        imgData = ones_like(shgData)
        self.Stage.goto_xyz(self.xpos,self.ypos,self.zpos)
        self.Stage.set_zspeed(F=int(self.zspeed))
        for k,z in enumerate(self.zarr):
            self.Stage.goto_z(z)
            self.Gal.start_scanxy(self.xarr,self.yarr,retrace = 1)
            while True:
                sleep(1)
                if self.stopCall:
                    self.Gal.startscan = False
                if self.Gal.update_scanxy():
                    self.imageData.emit([self.Gal.img_dataSHG,self.Gal.img_dataRef,self.Gal.img_Processed])
                else:
                    self.imageData.emit([self.Gal.img_dataSHG,self.Gal.img_dataRef,self.Gal.img_Processed])
                    shgData[k,:,:] = self.Gal.img_dataSHG
                    refData[k,:,:] = self.Gal.img_dataRef
                    imgData[k,:,:] = self.Gal.img_Processed
                    self.Gal.stop_scanxy()
                    break
            if self.stopCall:
                self.Gal.startscan = False
                break
        self.imageData3D.emit([shgData,refData,imgData])
        self.saveData(shgData,refData,imgData)
        self.stop_program()
        
    def XYZ_Scan_Continuous_Galvano(self):
        self.Gal.fast_dir = 'x'
        self.Scan3D_Continuous_Galvano()
    
    def YXZ_Scan_Continuous_Galvano(self):
        self.Gal.fast_dir = 'y'
        self.Scan3D_Continuous_Galvano()
        
    def XYZ_Scan_Step_Stage(self):
        shgData = zeros((len(self.zarr),len(self.xarr),len(self.yarr)))
        refData = -ones_like(shgData)
        imgData = ones_like(shgData)
        self.Stage.goto_xyz(self.xpos,self.ypos,self.zpos)
        self.Stage.set_zspeed(F=int(self.zspeed))
        self.Gal.start_single_point_counter()
        for k,z in enumerate(self.zarr):
            self.Stage.set_yspeed(F=int(self.yspeed))
            self.Stage.goto_z(z)
            for j,y in enumerate(self.yarr):
                self.Stage.goto_y(y)
                self.Stage.set_xspeed(F=int(self.xhighspeed))
                self.Stage.goto_x(self.xarr[0])
                self.Stage.set_xspeed(F=int(self.xspeed))
                for i,x in enumerate(self.xarr):
                    self.Stage.goto_x(x)
                    c,r = self.Gal.readCounts()
                    img = c/r
                    shgData[k,i,j] = c
                    refData[k,i,j] = r
                    imgData[k,i,j] = img
                    self.imageData.emit([shgData[k,:,:],refData[k,:,:],imgData[k,:,:]])
                    if self.stopCall:
                        break
                if self.stopCall:
                    break
            self.Stage.set_xspeed(F=int(self.xhighspeed))
            self.Stage.set_yspeed(F=int(self.yhighspeed))
            self.Stage.goto_xy(self.xarr[0],self.yarr[0])
            if self.stopCall:
                break
        self.imageData3D.emit([shgData,refData,imgData])
        self.Gal.stop_single_point_counter()
        self.Stage.set_zspeed(F=int(self.zhighspeed))
        self.saveData(shgData,refData,imgData)
        self.stop_program()
    
    def YXZ_Scan_Step_Stage(self):
        shgData = zeros((len(self.zarr),len(self.xarr),len(self.yarr)))
        refData = -ones_like(shgData)
        imgData = ones_like(shgData)
        self.Stage.goto_xyz(self.xpos,self.ypos,self.zpos)
        self.Stage.set_zspeed(F=int(self.zspeed))
        self.Gal.start_single_point_counter()
        for k,z in enumerate(self.zarr):
            self.Stage.set_xspeed(F=int(self.xspeed))
            self.Stage.goto_z(z)
            for i,x in enumerate(self.xarr):
                self.Stage.goto_x(x)
                self.Stage.set_yspeed(F=int(self.yhighspeed))
                self.Stage.goto_y(self.yarr[0])
                self.Stage.set_yspeed(F=int(self.yspeed))
                for j,y in enumerate(self.yarr):
                    self.Stage.goto_y(y)
                    c,r = self.Gal.readCounts()
                    img = c/r
                    shgData[k,i,j] = c
                    refData[k,i,j] = r
                    imgData[k,i,j] = img
                    self.imageData.emit([shgData[k,:,:],refData[k,:,:],imgData[k,:,:]])
                    if self.stopCall:
                        break
                if self.stopCall:
                    break
            self.Stage.set_xspeed(F=int(self.xhighspeed))
            self.Stage.set_yspeed(F=int(self.yhighspeed))
            self.Stage.goto_xy(self.xarr[0],self.yarr[0])
            if self.stopCall:
                break
        self.imageData3D.emit([shgData,refData,imgData])
        self.Gal.stop_single_point_counter()
        self.Stage.set_zspeed(F=int(self.zhighspeed))
        self.saveData(shgData,refData,imgData)
        self.stop_program()
    
    def stop_program(self):
        if self.scanNum in (29,30,37):
            self.Gal.stop_scanxy()
        else:
            self.Gal.counter.stop()
            self.Gal.reference.stop()
        self.finished.emit()