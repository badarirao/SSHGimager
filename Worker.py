# -*- coding: utf-8 -*-
"""
Created on Tue Dec  7 16:23:49 2021

@author: Badari
"""
from PyQt5.QtCore import QObject, pyqtSignal
from utilities import Select
from time import sleep
from numpy import linspace, array, ones_like, zeros
import h5py
import sidpy
import pyNSID
from pymeasure.experiment import unique_filename
from datetime import datetime
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


#TODO 1D scan using galvano

class ScanImage(QObject):
    finished = pyqtSignal()
    initialData = pyqtSignal(list)
    imageData = pyqtSignal(list)
    imageData3D = pyqtSignal(list)
    lineData = pyqtSignal(list)
    stopcall = pyqtSignal()
    go_ahead = pyqtSignal(bool)
    checkRef = pyqtSignal(bool)
    finalEmit = pyqtSignal(str)
    
    def __init__(self, scanParams, Gal, Stage, filename="sample"):
        super(ScanImage,self).__init__()
        self.stopCall = False
        self.go = 0
        self.scanParams = scanParams
        self.Gal = Gal
        self.Stage = Stage
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
        self.comment = scanParams[19]
        self.Gal.srate = self.srate
        self.xarr = list(linspace(self.xpos,self.xpos+self.xsize,self.xpoints,dtype=int))
        self.yarr = list(linspace(self.ypos,self.ypos+self.ysize,self.ypoints,dtype=int))
        self.zarr = list(linspace(self.zpos,self.zpos+self.zsize,self.zpoints,dtype=int))
        self.xscale = self.xsize/self.xpoints
        self.yscale = self.ysize/self.ypoints
        self.zscale = self.zsize/self.zpoints
        self.filename = filename + '_{}D'.format(self.nd)
       
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
        if self.nd == 1:
            self.xarr = array(self.xarr[:len(self.shgData)])
            self.yarr = array(self.yarr[:len(self.shgData)])
            self.zarr = array(self.zarr[:len(self.shgData)])
        else:
            self.xarr = array(self.xarr)
            self.yarr = array(self.yarr)
            self.zarr = array(self.zarr)
        xarr = self.xarr
        yarr = self.yarr
        zarr = self.zarr
        shgData = sidpy.Dataset.from_array(self.shgData.round(6))  # RAW shg signals
        refData = sidpy.Dataset.from_array(self.refData.round(6))  # Reference intensity in μV
        imgData = sidpy.Dataset.from_array(self.imgData.round(6)) # shg/ref signal
        if self.scanKind == 0 and self.nd > 1:
            shgData2 = sidpy.Dataset.from_array(self.shgData2.round(6))  # RAW shg signals
            refData2 = sidpy.Dataset.from_array(self.refData2.round(6))  # Reference intensity in μV
            imgData2 = sidpy.Dataset.from_array(self.imgData2.round(6)) # shg/ref signal
        # Add information about scanning parameters as metadata
        info = sidpy.Dataset.from_array([-1])
        self.fullfilename = unique_filename(directory='.',prefix=self.filename,datetimeformat="",ext='shg')
        info.title = 'Scan Info'
        info.metadata = {'File Name': self.fullfilename.split('\\')[-1][:-4],
                         'Scan Type':Select.scanName(self.scanNum),
                         'Scan Kind':self.getScanKind(self.scanKind),
                         'Scan Speed': self.srate,
                         'Date & Time': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                         'Dimension': self.nd,
                         'x-position': self.xpos,
                         'y-position': self.ypos,
                         'z-position': self.zpos,
                         'Comments': self.comment}
        if self.nd == 1: # 1D scan data
            shgData.data_type = 'LINE_PLOT'
            refData.data_type = 'LINE_PLOT'
            imgData.data_type = 'LINE_PLOT'
            if self.scanNum in (1,2,3,4): # x-scan
                shgData.set_dimension(0, sidpy.Dimension(xarr, 'aAxis'))
                refData.set_dimension(0, sidpy.Dimension(xarr, 'aAxis'))
                imgData.set_dimension(0, sidpy.Dimension(xarr, 'aAxis'))
                refData.aAxis.quantity = 'X'
                shgData.aAxis.quantity = 'X'
                imgData.aAxis.quantity = 'X'
            elif self.scanNum in (5,6,7,8): # y-scan
                shgData.set_dimension(0, sidpy.Dimension(yarr, 'aAxis'))
                refData.set_dimension(0, sidpy.Dimension(yarr, 'aAxis'))
                imgData.set_dimension(0, sidpy.Dimension(yarr, 'aAxis'))
                refData.aAxis.quantity = 'Y'
                shgData.aAxis.quantity = 'Y'
                imgData.aAxis.quantity = 'Y'
            elif self.scanNum in (9,10,11,12): # z-scan
                shgData.set_dimension(0, sidpy.Dimension(zarr, 'aAxis'))
                refData.set_dimension(0, sidpy.Dimension(zarr, 'aAxis'))
                imgData.set_dimension(0, sidpy.Dimension(zarr, 'aAxis'))
                refData.aAxis.quantity = 'Z'
                shgData.aAxis.quantity = 'Z'
                imgData.aAxis.quantity = 'Z'
        elif self.nd == 2: # 2D scan data
            shgData.data_type = 'IMAGE'
            refData.data_type = 'IMAGE'
            imgData.data_type = 'IMAGE'
            if self.scanKind == 0:
                shgData2.data_type = 'IMAGE'
                refData2.data_type = 'IMAGE'
                imgData2.data_type = 'IMAGE'
            if self.scanNum in range(13,21): 
                shgData.set_dimension(0, sidpy.Dimension(yarr, 'aAxis'))
                shgData.set_dimension(1, sidpy.Dimension(zarr, 'bAxis'))
                refData.set_dimension(0, sidpy.Dimension(yarr, 'aAxis'))
                refData.set_dimension(1, sidpy.Dimension(zarr, 'bAxis'))
                imgData.set_dimension(0, sidpy.Dimension(yarr, 'aAxis'))
                imgData.set_dimension(1, sidpy.Dimension(zarr, 'bAxis'))
                shgData.aAxis.quantity = 'Y'
                shgData.bAxis.quantity = 'Z'
                refData.aAxis.quantity = 'Y'
                refData.bAxis.quantity = 'Z'
                imgData.aAxis.quantity = 'Y'
                imgData.bAxis.quantity = 'Z'
                if self.scanKind == 0:
                    shgData2.set_dimension(0, sidpy.Dimension(yarr, 'aAxis'))
                    shgData2.set_dimension(1, sidpy.Dimension(zarr, 'bAxis'))
                    refData2.set_dimension(0, sidpy.Dimension(yarr, 'aAxis'))
                    refData2.set_dimension(1, sidpy.Dimension(zarr, 'bAxis'))
                    imgData2.set_dimension(0, sidpy.Dimension(yarr, 'aAxis'))
                    imgData2.set_dimension(1, sidpy.Dimension(zarr, 'bAxis'))
                    shgData2.aAxis.quantity = 'Y'
                    shgData2.bAxis.quantity = 'Z'
                    refData2.aAxis.quantity = 'Y'
                    refData2.bAxis.quantity = 'Z'
                    imgData2.aAxis.quantity = 'Y'
                    imgData2.bAxis.quantity = 'Z'
            elif self.scanNum in range(21,29): 
                shgData.set_dimension(0, sidpy.Dimension(xarr, 'aAxis'))
                shgData.set_dimension(1, sidpy.Dimension(zarr, 'bAxis'))
                refData.set_dimension(0, sidpy.Dimension(xarr, 'aAxis'))
                refData.set_dimension(1, sidpy.Dimension(zarr, 'bAxis'))
                imgData.set_dimension(0, sidpy.Dimension(xarr, 'aAxis'))
                imgData.set_dimension(1, sidpy.Dimension(zarr, 'bAxis'))
                shgData.aAxis.quantity = 'X'
                shgData.bAxis.quantity = 'Z'
                refData.aAxis.quantity = 'X'
                refData.bAxis.quantity = 'Z'
                imgData.aAxis.quantity = 'X'
                imgData.bAxis.quantity = 'Z'
                if self.scanKind == 0:
                    shgData2.set_dimension(0, sidpy.Dimension(xarr, 'aAxis'))
                    shgData2.set_dimension(1, sidpy.Dimension(zarr, 'bAxis'))
                    refData2.set_dimension(0, sidpy.Dimension(xarr, 'aAxis'))
                    refData2.set_dimension(1, sidpy.Dimension(zarr, 'bAxis'))
                    imgData2.set_dimension(0, sidpy.Dimension(xarr, 'aAxis'))
                    imgData2.set_dimension(1, sidpy.Dimension(zarr, 'bAxis'))
                    shgData2.aAxis.quantity = 'X'
                    shgData2.bAxis.quantity = 'Z'
                    refData2.aAxis.quantity = 'X'
                    refData2.bAxis.quantity = 'Z'
                    imgData2.aAxis.quantity = 'X'
                    imgData2.bAxis.quantity = 'Z'
            elif self.scanNum in range(29,37): 
                shgData.set_dimension(0, sidpy.Dimension(xarr, 'aAxis'))
                shgData.set_dimension(1, sidpy.Dimension(yarr, 'bAxis'))
                refData.set_dimension(0, sidpy.Dimension(xarr, 'aAxis'))
                refData.set_dimension(1, sidpy.Dimension(yarr, 'bAxis'))
                imgData.set_dimension(0, sidpy.Dimension(xarr, 'aAxis'))
                imgData.set_dimension(1, sidpy.Dimension(yarr, 'bAxis'))
                shgData.aAxis.quantity = 'X'
                shgData.bAxis.quantity = 'Y'
                refData.aAxis.quantity = 'X'
                refData.bAxis.quantity = 'Y'
                imgData.aAxis.quantity = 'X'
                imgData.bAxis.quantity = 'Y'
                if self.scanKind == 0:
                    shgData2.set_dimension(0, sidpy.Dimension(xarr, 'aAxis'))
                    shgData2.set_dimension(1, sidpy.Dimension(yarr, 'bAxis'))
                    refData2.set_dimension(0, sidpy.Dimension(xarr, 'aAxis'))
                    refData2.set_dimension(1, sidpy.Dimension(yarr, 'bAxis'))
                    imgData2.set_dimension(0, sidpy.Dimension(xarr, 'aAxis'))
                    imgData2.set_dimension(1, sidpy.Dimension(yarr, 'bAxis'))
                    shgData2.aAxis.quantity = 'X'
                    shgData2.bAxis.quantity = 'Y'
                    refData2.aAxis.quantity = 'X'
                    refData2.bAxis.quantity = 'Y'
                    imgData2.aAxis.quantity = 'X'
                    imgData2.bAxis.quantity = 'Y'
        elif self.nd == 3: # 3D scan data
            shgData.data_type = 'image_stack'
            refData.data_type = 'image_stack'
            imgData.data_type = 'image_stack'
            if self.scanKind == 0:
                shgData2.data_type = 'image_stack'
                refData2.data_type = 'image_stack'
                imgData2.data_type = 'image_stack'                
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
                shgData.aAxis.quantity = 'X'
                refData.aAxis.quantity = 'X'
                imgData.aAxis.quantity = 'X'
                shgData.bAxis.quantity = 'Y'
                refData.bAxis.quantity = 'Y'
                imgData.bAxis.quantity = 'Y'
                shgData.cAxis.quantity = 'Z'
                refData.cAxis.quantity = 'Z'
                imgData.cAxis.quantity = 'Z'
                if self.scanKind == 0:
                    shgData2.set_dimension(0, sidpy.Dimension(zarr, 'cAxis'))
                    shgData2.set_dimension(1, sidpy.Dimension(xarr, 'aAxis'))
                    shgData2.set_dimension(2, sidpy.Dimension(yarr, 'bAxis'))
                    refData2.set_dimension(0, sidpy.Dimension(zarr, 'cAxis'))
                    refData2.set_dimension(1, sidpy.Dimension(xarr, 'aAxis'))
                    refData2.set_dimension(2, sidpy.Dimension(yarr, 'bAxis'))
                    imgData2.set_dimension(0, sidpy.Dimension(zarr, 'cAxis'))
                    imgData2.set_dimension(1, sidpy.Dimension(xarr, 'aAxis'))
                    imgData2.set_dimension(2, sidpy.Dimension(yarr, 'bAxis'))
                    shgData2.aAxis.quantity = 'X'
                    refData2.aAxis.quantity = 'X'
                    imgData2.aAxis.quantity = 'X'
                    shgData2.bAxis.quantity = 'Y'
                    refData2.bAxis.quantity = 'Y'
                    imgData2.bAxis.quantity = 'Y'
                    shgData2.cAxis.quantity = 'Z'
                    refData2.cAxis.quantity = 'Z'
                    imgData2.cAxis.quantity = 'Z'
        try:    
            shgData.aAxis.dimension_type = 'spatial'
            refData.aAxis.dimension_type = 'spatial'
            imgData.aAxis.dimension_type = 'spatial'
            shgData.aAxis.units = 'μm'
            refData.aAxis.units = 'μm'
            imgData.aAxis.units = 'μm'
            if shgData.aAxis.quantity == 'X':
                info.metadata['aAxis'] = {'Axis': 'X', 'Points': self.xpoints, 'Position': self.xpos, 'Scale': self.xscale, 'Size': self.xsize}
            elif shgData.aAxis.quantity == 'Y':
                info.metadata['aAxis'] = {'Axis': 'Y', 'Points': self.ypoints, 'Position': self.ypos, 'Scale': self.yscale, 'Size': self.ysize}
            elif shgData.aAxis.quantity == 'Z':
                info.metadata['aAxis'] = {'Axis': 'Z', 'Points': self.zpoints, 'Position': self.zpos, 'Scale': self.zscale, 'Size': self.zsize}
            shgData.bAxis.dimension_type = 'spatial'
            refData.bAxis.dimension_type = 'spatial'
            imgData.bAxis.dimension_type = 'spatial'
            shgData.bAxis.units = 'μm'
            refData.bAxis.units = 'μm'
            imgData.bAxis.units = 'μm'
            if shgData.bAxis.quantity == 'X':
                info.metadata['bAxis'] = {'Axis': 'X', 'Points': self.xpoints, 'Position': self.xpos, 'Scale': self.xscale, 'Size': self.xsize}
            elif shgData.bAxis.quantity == 'Y':
                info.metadata['bAxis'] = {'Axis': 'Y', 'Points': self.ypoints, 'Position': self.ypos, 'Scale': self.yscale, 'Size': self.ysize}
            elif shgData.bAxis.quantity == 'Z':
                info.metadata['bAxis'] = {'Axis': 'Z', 'Points': self.zpoints, 'Position': self.zpos, 'Scale': self.zscale, 'Size': self.zsize}
            shgData.cAxis.dimension_type = 'spatial'
            refData.cAxis.dimension_type = 'spatial'
            imgData.cAxis.dimension_type = 'spatial'
            shgData.cAxis.units = 'μm'
            refData.cAxis.units = 'μm'
            imgData.cAxis.units = 'μm'
            if shgData.cAxis.quantity == 'X':
                info.metadata['cAxis'] = {'Axis': 'X', 'Points': self.xpoints, 'Position': self.xpos, 'Scale': self.xscale, 'Size': self.xsize}
            elif shgData.aAxis.quantity == 'Y':
                info.metadata['cAxis'] = {'Axis': 'Y', 'Points': self.ypoints, 'Position': self.ypos, 'Scale': self.yscale, 'Size': self.ysize}
            elif shgData.aAxis.quantity == 'Z':
                info.metadata['cAxis'] = {'Axis': 'Z', 'Points': self.zpoints, 'Position': self.zpos, 'Scale': self.zscale, 'Size': self.zsize}
        except Exception:
            pass
        if self.scanKind == 0 and self.nd > 1:
            try:    
                shgData2.aAxis.dimension_type = 'spatial'
                refData2.aAxis.dimension_type = 'spatial'
                imgData2.aAxis.dimension_type = 'spatial'
                shgData2.aAxis.units = 'μm'
                refData2.aAxis.units = 'μm'
                imgData2.aAxis.units = 'μm'
                shgData2.bAxis.dimension_type = 'spatial'
                refData2.bAxis.dimension_type = 'spatial'
                imgData2.bAxis.dimension_type = 'spatial'
                shgData2.bAxis.units = 'μm'
                refData2.bAxis.units = 'μm'
                imgData2.bAxis.units = 'μm'
                shgData2.cAxis.dimension_type = 'spatial'
                refData2.cAxis.dimension_type = 'spatial'
                imgData2.cAxis.dimension_type = 'spatial'
                shgData2.cAxis.units = 'μm'
                refData2.cAxis.units = 'μm'
                imgData2.cAxis.units = 'μm'
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
        info.modality = 'Scan Information'
        if self.scanKind == 0 and self.nd > 1:
            shgData2.modality = 'SHG micorscopy Raw Image'
            shgData2.title = self.filename+'_shg_RAW'
            shgData2.quantity = 'intensity'
            shgData2.units = 'counts'
            refData2.modality = 'SHG micorscopy Reference Intensity data'
            refData2.title = self.filename+'_reference'
            refData2.quantity = 'intensity'
            refData2.units = 'μV'
            imgData2.modality = 'SHG micorscopy Processed Image'
            imgData2.title = self.filename+'_processed'
            imgData2.quantity = 'intensity'
            imgData2.units = 'arb.units'
        # save all data as HDF5 file
        hf = h5py.File(self.fullfilename,'w')
        hf.create_group('Processed Data')
        hf.create_group('Raw Data')
        hf.create_group('Reference Data')
        hf.create_group('Scan Info')
        pyNSID.hdf_io.write_nsid_dataset(info, hf['Scan Info'], main_data_name="")
        if self.scanKind == 0 and self.nd > 1:
            pyNSID.hdf_io.write_nsid_dataset(shgData, hf['Raw Data'], main_data_name="RAW SHG Trace")
            pyNSID.hdf_io.write_nsid_dataset(imgData, hf['Processed Data'], main_data_name="PROCESSED Trace")
            pyNSID.hdf_io.write_nsid_dataset(refData, hf['Reference Data'], main_data_name="REFERENCE Trace")
            pyNSID.hdf_io.write_nsid_dataset(shgData2, hf['Raw Data'], main_data_name="RAW SHG Retrace")
            pyNSID.hdf_io.write_nsid_dataset(imgData2, hf['Processed Data'], main_data_name="PROCESSED Retrace")
            pyNSID.hdf_io.write_nsid_dataset(refData2, hf['Reference Data'], main_data_name="REFERENCE Retrace")
        else:
            pass
            pyNSID.hdf_io.write_nsid_dataset(shgData, hf['Raw Data'], main_data_name="RAW SHG")
            pyNSID.hdf_io.write_nsid_dataset(imgData, hf['Processed Data'], main_data_name="PROCESSED")
            pyNSID.hdf_io.write_nsid_dataset(refData, hf['Reference Data'], main_data_name="REFERENCE")
        hf.close()
        self.finalEmit.emit(self.fullfilename)
    
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
            self.X_Scan_Step_Stage()
        elif self.scanNum == Select.Y_Scan_Continuous_Galvano:
            pass
        elif self.scanNum == Select.Y_Scan_Step_Galvano:
            pass
        elif self.scanNum == Select.Y_Scan_Continuous_Stage:
            pass
        elif self.scanNum == Select.Y_Scan_Step_Stage:
            self.initialData.emit(['1D y-scan using Stage', 'y (μm)',self.ypos])
            self.Stage.set_yspeed(F=int(self.yspeed))                
            self.Y_Scan_Step_Stage()
        elif self.scanNum == Select.Z_Scan_Continuous_Stage:
            pass
        elif self.scanNum == Select.Z_Scan_Step_Stage:
            self.initialData.emit(['1D z-scan using Stage', 'z (μm)',self.zpos])
            self.Stage.set_zspeed(F=int(self.zspeed))                
            self.Z_Scan_Step_Stage()
        elif self.scanNum == Select.YZ_Scan_Continuous_Galvano:
            pass
        elif self.scanNum == Select.YZ_Scan_Step_Galvano:
            pass
        elif self.scanNum == Select.YZ_Scan_Continuous_Stage:
            pass
        elif self.scanNum == Select.YZ_Scan_Step_Stage:
            self.initialData.emit(['2D YZ-scan using Stage','y (μm)','z (μm)',self.yscale,self.zscale])
            self.YZ_Scan_Step_Stage()
        elif self.scanNum == Select.ZY_Scan_Continuous_Galvano:
            pass
        elif self.scanNum == Select.ZY_Scan_Step_Galvano:
            pass
        elif self.scanNum == Select.ZY_Scan_Continuous_Stage:
            pass
        elif self.scanNum == Select.ZY_Scan_Step_Stage:
            self.initialData.emit(['2D ZY-scan using Stage', 'y (μm)','z (μm)',self.yscale,self.zscale])
            self.ZY_Scan_Step_Stage()
        elif self.scanNum == Select.XZ_Scan_Continuous_Galvano:
            pass
        elif self.scanNum == Select.XZ_Scan_Step_Galvano:
            pass
        elif self.scanNum == Select.XZ_Scan_Continuous_Stage:
            pass
        elif self.scanNum == Select.XZ_Scan_Step_Stage:
            self.initialData.emit(['2D XZ-scan using Stage', 'x (μm)','z (μm)',self.xscale,self.zscale])
            self.XZ_Scan_Step_Stage()
        elif self.scanNum == Select.ZX_Scan_Continuous_Galvano:
            pass
        elif self.scanNum == Select.ZX_Scan_Step_Galvano:
            pass
        elif self.scanNum == Select.ZX_Scan_Continuous_Stage:
            pass
        elif self.scanNum == Select.ZX_Scan_Step_Stage:
            self.initialData.emit(['2D ZX-scan using Stage', 'x (μm)','z (μm)',self.xscale,self.zscale])
            self.ZX_Scan_Step_Stage()
        elif self.scanNum == Select.XY_Scan_Continuous_Galvano:
            self.initialData.emit(['2D XY-scan using Laser', 'x (μm)','y (μm)',self.xscale,self.yscale])
            self.xarr = linspace(-self.xsize/2+self.Gal.xhome,self.xsize/2+self.Gal.xhome,self.xpoints)
            self.yarr = linspace(-self.ysize/2+self.Gal.yhome,self.ysize/2+self.Gal.yhome,self.ypoints)
            self.Gal.x = self.Gal.xhome
            self.Gal.y = self.Gal.yhome
            self.Stage.x = self.xpos
            self.Stage.y = self.ypos
            self.Gal.srate = self.srate
            while self.Stage.is_xmoving() or self.Stage.is_ymoving():
                sleep(0.1)
            self.XY_Scan_Continuous_Galvano()
        elif self.scanNum == Select.XY_Scan_Step_Galvano:
            pass
        elif self.scanNum == Select.XY_Scan_Continuous_Stage:
            pass
        elif self.scanNum == Select.XY_Scan_Step_Stage:
            self.initialData.emit(['2D XY-scan using Stage', 'x (μm)','y (μm)',self.xscale,self.yscale])
            self.XY_Scan_Step_Stage()
        elif self.scanNum == Select.YX_Scan_Continuous_Galvano:
            self.initialData.emit(['2D YX-scan using Laser', 'x (μm)','y (μm)',self.xscale,self.yscale])
            self.xarr = linspace(-self.xsize/2+self.Gal.xhome,self.xsize/2+self.Gal.xhome,self.xpoints)
            self.yarr = linspace(-self.ysize/2+self.Gal.yhome,self.ysize/2+self.Gal.yhome,self.ypoints)
            self.Gal.srate = self.srate
            self.Gal.x = self.Gal.xhome
            self.Gal.y = self.Gal.yhome
            self.Stage.x = self.xpos
            self.Stage.y = self.ypos
            while self.Stage.is_xmoving() or self.Stage.is_ymoving():
                sleep(0.1)
            self.YX_Scan_Continuous_Galvano()
        elif self.scanNum == Select.YX_Scan_Step_Galvano:
            pass
        elif self.scanNum == Select.YX_Scan_Continuous_Stage:
            pass
        elif self.scanNum == Select.YX_Scan_Step_Stage:
            self.initialData.emit(['2D YX-scan using Stage', 'x (μm)','y (μm)',self.xscale,self.yscale])
            self.YX_Scan_Step_Stage()
        elif self.scanNum == Select.XYZ_Scan_Continuous_Galvano:
            self.initialData.emit(['3D XYZ-scan using Laser', 'x (μm)','y (μm)','z (μm)',self.xscale,self.yscale,array(self.zarr)])
            self.Stage.set_zspeed(F=int(self.zspeed))
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
            self.initialData.emit(['3D XYZ-scan using Stage', 'x (μm)','y (μm)','z (μm)',self.xscale,self.yscale,array(self.zarr)])
            self.XYZ_Scan_Step_Stage()
        elif self.scanNum == Select.YXZ_Scan_Continuous_Galvano:
            #self.spinBox_zmove.setValue(int(self.zpos.value()))
            self.initialData.emit(['3D YXZ-scan using Laser', 'x (μm)','y (μm)','z (μm)',self.xscale,self.yscale,array(self.zarr)])
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
            self.initialData.emit(['3D YXZ-scan using Stage', 'x (μm)','y (μm)','z (μm)',self.xscale,self.yscale,array(self.zarr)])
            self.YXZ_Scan_Step_Stage()
    
    def scan1D_Stage(self,goto,setSpeed,arr,speed,highSpeed,stage_is_moving):
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
        while stage_is_moving():
            sleep(0.1)
        self.stage_move_finished.emit(True)
        setSpeed(F=int(speed))
        self.Gal.start_single_point_counter()
        for i,q in enumerate(arr):
            goto(q)
            #while stage_is_moving():
            #    pass
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
        self.scan1D_Stage(self.Stage.goto_x,self.Stage.set_xspeed,self.xarr,self.xspeed,self.xhighspeed,self.Stage.is_xmoving)
        
    def Y_Scan_Step_Stage(self):
        self.scan1D_Stage(self.Stage.goto_y,self.Stage.set_yspeed,self.yarr,self.yspeed,self.yhighspeed,self.Stage.is_ymoving)
    
    def Z_Scan_Step_Stage(self):
        self.scan1D_Stage(self.Stage.goto_z,self.Stage.set_zspeed,self.zarr,self.zspeed,self.zhighspeed,self.Stage.is_zmoving )
        
    def collect_2DSHG_Signal(self,goto,p,q,i,j):
        goto(p,q)
        #while self.Stage.is_xmoving() or self.Stage.is_ymoving() or self.Stage.is_zmoving():
        #    pass
        c,r = self.Gal.readCounts()
        img = c/r
        self.shgData[i,j] = c
        self.refData[i,j] = r
        self.imgData[i,j] = img
        self.imageData.emit([self.shgData,self.refData,self.imgData])
    
    def collect_2DSHG_secondSignal(self,goto,p,q,i,j):
        goto(p,q)
        #while self.Stage.is_xmoving() or self.Stage.is_ymoving() or self.Stage.is_zmoving():
        #    pass
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
        while self.Stage.is_xmoving() or self.Stage.is_ymoving() or self.Stage.is_zmoving():
            sleep(0.1)
        set2speed(F=int(speed2))
        set1speed(F=int(speed1))
        self.Gal.start_single_point_counter()
        iStart = 0
        iEnd = len(arr1)-1
        if scanKind == 1:
            while True:
                p = arr1[i]
                q = arr2[j]
                self.collect_2DSHG_Signal(goto,p,q,i,j)
                i += 1
                if i >= len(arr1):
                    j += 1
                    if j >= len(arr2):
                        break
                    #set1speed(F=int(highspeed1))
                    gotoP(arr1[0])
                    while self.Stage.is_xmoving() or self.Stage.is_ymoving() or self.Stage.is_zmoving():
                        pass
                    #set1speed(F=int(speed1))
                    i = iStart
                if self.stopCall:
                    break
        elif scanKind == -1:
            while True:
                p = arr1[i]
                q = arr2[j]
                self.collect_2DSHG_Signal(goto,p,q,i,j)
                i -= 1
                if i < 0:
                    j += 1
                    if j >= len(arr2):
                        break
                    #set1speed(F=int(highspeed1))
                    gotoP(arr1[-1])
                    while self.Stage.is_xmoving() or self.Stage.is_ymoving() or self.Stage.is_zmoving():
                        pass
                    #set1speed(F=int(speed1))
                    i = iEnd
                if self.stopCall:
                    break
        elif scanKind == 2:
            while True:
                p = arr1[i]
                q = arr2[j]
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
                p = arr1[i]
                q = arr2[j]
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
            j = len(arr2)-1
        if scanKind == 0:
            self.shgData2 = zeros((len(arr1),len(arr2)))
            self.refData2 = -ones_like(self.shgData2)
            self.imgData2 = ones_like(self.shgData2)
        p = arr1[i]
        q = arr2[j]
        goto(p,q)
        while self.Stage.is_xmoving() or self.Stage.is_ymoving() or self.Stage.is_zmoving():
            sleep(0.1)
        set1speed(F=int(speed1))
        set2speed(F=int(speed2))
        self.Gal.start_single_point_counter()
        jStart = 0
        jEnd = len(arr2)-1
        if scanKind == 1:
            while True:
                p = arr1[i]
                q = arr2[j]
                self.collect_2DSHG_Signal(goto,p,q,i,j)
                j += 1
                if j >= len(arr2):
                    i += 1
                    if i >= len(arr1):
                        break
                    #set2speed(F=int(highspeed2))
                    gotoQ(arr2[0])
                    while self.Stage.is_xmoving() or self.Stage.is_ymoving() or self.Stage.is_zmoving():
                        pass
                    #set2speed(F=int(speed2))
                    j = jStart
                if self.stopCall:
                    break
        elif scanKind == -1:
            while True:
                p = arr1[i]
                q = arr2[j]
                self.collect_2DSHG_Signal(goto,p,q,i,j)
                j -= 1
                if j < 0:
                    i += 1
                    if i >= len(arr1):
                        break
                    #set2speed(F=int(highspeed2))
                    gotoQ(arr2[-1])
                    while self.Stage.is_xmoving() or self.Stage.is_ymoving() or self.Stage.is_zmoving():
                        pass
                    #set2speed(F=int(speed2))
                    j = jEnd
                if self.stopCall:
                    break
        elif scanKind == 2:
            while True:
                p = arr1[i]
                q = arr2[j]
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
                p = arr1[i]
                q = arr2[j]
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
                          self.scanKind,self.Stage.goto_z)
    
    def XY_Scan_Step_Stage(self):
        self.scan2D_Stage(self.Stage.goto_xy,
                          self.xarr,self.yarr,
                          self.Stage.set_xspeed,self.Stage.set_yspeed,
                          self.xspeed,self.yspeed,
                          self.xhighspeed,self.yhighspeed,
                          self.scanKind,self.Stage.goto_x)
    
    def YX_Scan_Step_Stage(self):
        self.altScan2D_Stage(self.Stage.goto_xy,
                          self.xarr,self.yarr,
                          self.Stage.set_xspeed,self.Stage.set_yspeed,
                          self.xspeed,self.yspeed,
                          self.xhighspeed,self.yhighspeed,
                          self.scanKind,self.Stage.goto_y)
    
    def scan2D_Continuous_Galvano(self):
        self.Gal.start_scanxy(self.xarr,self.yarr,retrace = self.scanKind)
        while True:
            sleep(1)
            if self.stopCall:
                self.Gal.startscan = False
            if self.Gal.update_scanxy():
                self.imageData.emit([self.Gal.img_dataSHG,self.Gal.img_dataRef,self.Gal.img_Processed])
            else:
                break
        self.imageData.emit([self.Gal.img_dataSHG,self.Gal.img_dataRef,self.Gal.img_Processed])
        self.shgData = self.Gal.img_dataSHG
        self.refData = self.Gal.img_dataRef
        self.imgData = self.Gal.img_Processed
        if self.scanKind == 0:
            self.shgData2 = self.Gal.img_dataSHG2
            self.refData2 = self.Gal.img_dataRef2
            self.imgData2 = self.Gal.img_Processed2
        self.saveData()
        self.stop_program()
        
    def XY_Scan_Continuous_Galvano(self):
        self.Gal.fast_dir = 'x'
        self.scan2D_Continuous_Galvano()
    
    def YX_Scan_Continuous_Galvano(self):
        self.Gal.fast_dir = 'y'
        self.scan2D_Continuous_Galvano()
    
    def Scan3D_Continuous_Galvano(self):
        self.shgData = zeros((len(self.zarr),len(self.xarr),len(self.yarr)))
        self.refData = -ones_like(self.shgData)
        self.imgData = ones_like(self.shgData)
        if self.scanKind == 0:
            self.shgData2 = zeros((len(self.zarr),len(self.xarr),len(self.yarr)))
            self.refData2 = -ones_like(self.shgData2)
            self.imgData2 = ones_like(self.shgData2)
        self.Stage.goto_xyz(self.xpos,self.ypos,self.zpos)
        while self.Stage.is_xmoving() or self.Stage.is_ymoving() or self.Stage.is_zmoving():
            sleep(0.1)
        self.Stage.set_zspeed(F=int(self.zspeed))
        for k,z in enumerate(self.zarr):
            self.Stage.goto_z(z)
            while self.Stage.is_zmoving():
                pass
            self.Gal.start_scanxy(self.xarr,self.yarr,retrace = self.scanKind)
            while True:
                if self.stopCall:
                    self.Gal.startscan = False
                if self.Gal.update_scanxy():
                    self.imageData.emit([self.Gal.img_dataSHG,self.Gal.img_dataRef,self.Gal.img_Processed])
                else:
                    break
            self.Gal.stop_scanxy()
            self.imageData.emit([self.Gal.img_dataSHG,self.Gal.img_dataRef,self.Gal.img_Processed])
            self.shgData[k,:,:] = self.Gal.img_dataSHG
            self.refData[k,:,:] = self.Gal.img_dataRef
            self.imgData[k,:,:] = self.Gal.img_Processed
            if self.scanKind == 0:
                self.shgData2[k,:,:] = self.Gal.img_dataSHG2
                self.refData2[k,:,:] = self.Gal.img_dataRef2
                self.imgData2[k,:,:] = self.Gal.img_Processed2
            if self.stopCall:
                self.Gal.startscan = False
                break
        self.imageData3D.emit([self.shgData,self.refData,self.imgData])
        self.saveData()
        self.stop_program()
        self.Stage.set_zspeed(F=int(self.zhighspeed))
        
    def XYZ_Scan_Continuous_Galvano(self):
        self.Gal.fast_dir = 'x'
        self.Scan3D_Continuous_Galvano()
    
    def YXZ_Scan_Continuous_Galvano(self):
        self.Gal.fast_dir = 'y'
        self.Scan3D_Continuous_Galvano()
        
    def collect_3DSHG_Signal(self,goto,p,q,i,j,k):
        goto(p,q)
        #while self.Stage.is_xmoving() or self.Stage.is_ymoving() or self.Stage.is_zmoving():
        #    pass
        c,r = self.Gal.readCounts()
        img = c/r
        self.shgData[k,i,j] = c
        self.refData[k,i,j] = r
        self.imgData[k,i,j] = img
        self.imageData.emit([self.shgData[k,:,:],self.refData[k,:,:],self.imgData[k,:,:]])
    
    def collect_3DSHG_secondSignal(self,goto,p,q,i,j,k):
        goto(p,q)
        #while self.Stage.is_xmoving() or self.Stage.is_ymoving() or self.Stage.is_zmoving():
        #    pass
        c,r = self.Gal.readCounts()
        img = c/r
        self.shgData2[k,i,j] = c
        self.refData2[k,i,j] = r
        self.imgData2[k,i,j] = img
        #self.imageData.emit([self.shgData[k,:,:],self.refData[k,:,:],self.imgData[k,:,:]])
    
    def scan3D_Stage(self,goto,arr1,arr2,set1speed,set2speed,speed1,speed2,highspeed1,highspeed2,scanKind,gotoP,k):
        j = 0
        if scanKind in (0,1,2):
            i = 0
        elif scanKind == -1:
            i = len(arr1)-1
        p = arr1[i]
        q = arr2[j]
        goto(p,q)
        while self.Stage.is_xmoving() or self.Stage.is_ymoving() or self.Stage.is_zmoving():
            sleep(0.1)
        set2speed(F=int(speed2))
        set1speed(F=int(speed1))
        self.Gal.start_single_point_counter()
        iStart = 0
        iEnd = len(arr1)-1
        if scanKind == 1:
            while True:
                p = arr1[i]
                q = arr2[j]
                self.collect_3DSHG_Signal(goto,p,q,i,j,k)
                i += 1
                if i >= len(arr1):
                    j += 1
                    if j >= len(arr2):
                        break
                    #set1speed(F=int(highspeed1))
                    gotoP(arr1[0])
                    #set1speed(F=int(speed1))
                    i = iStart
                if self.stopCall:
                    break
        elif scanKind == -1:
            while True:
                p = arr1[i]
                q = arr2[j]
                self.collect_3DSHG_Signal(goto,p,q,i,j,k)
                i -= 1
                if i < 0:
                    j += 1
                    if j >= len(arr2):
                        break
                    #set1speed(F=int(highspeed1))
                    gotoP(arr1[-1])
                    while self.Stage.is_xmoving() or self.Stage.is_ymoving() or self.Stage.is_zmoving():
                        pass
                    #set1speed(F=int(speed1))
                    i = iEnd
                if self.stopCall:
                    break
        elif scanKind == 2:
            while True:
                p = arr1[i]
                q = arr2[j]
                self.collect_3DSHG_Signal(goto,p,q,i,j,k)
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
                p = arr1[i]
                q = arr2[j]
                self.collect_3DSHG_Signal(goto,p,q,i,j,k)
                i += 1
                if i >= len(arr1):
                    i = iEnd
                    while True:
                        self.collect_3DSHG_secondSignal(goto,p,q,i,j,k)
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
        set1speed(F=int(highspeed1))
        set2speed(F=int(highspeed2))
        goto(arr1[0],arr2[0])
        while self.Stage.is_xmoving() or self.Stage.is_ymoving() or self.Stage.is_zmoving():
            pass
    
    def altScan3D_Stage(self,goto,arr1,arr2,set1speed,set2speed,speed1,speed2,highspeed1,highspeed2,scanKind,gotoQ,k):
        i = 0
        if scanKind in (0,1,2):
            j = 0
        elif scanKind == -1:
            j = len(arr2)-1
        p = arr1[i]
        q = arr2[j]
        goto(p,q)
        while self.Stage.is_xmoving() or self.Stage.is_ymoving() or self.Stage.is_zmoving():
            sleep(0.1)
        set1speed(F=int(speed1))
        set2speed(F=int(speed2))
        self.Gal.start_single_point_counter()
        jStart = 0
        jEnd = len(arr2)-1
        if scanKind == 1:
            while True:
                self.collect_2DSHG_Signal(goto,p,q,i,j,k)
                j += 1
                if j >= len(arr2):
                    i += 1
                    if i >= len(arr1):
                        break
                    #set2speed(F=int(highspeed2))
                    gotoQ(arr2[0])
                    while self.Stage.is_xmoving() or self.Stage.is_ymoving() or self.Stage.is_zmoving():
                        pass
                    #set2speed(F=int(speed2))
                    j = jStart
                if self.stopCall:
                    break
        elif scanKind == -1:
            while True:
                self.collect_2DSHG_Signal(goto,p,q,i,j,k)
                j -= 1
                if j < 0:
                    i += 1
                    if i >= len(arr1):
                        break
                    #set2speed(F=int(highspeed2))
                    gotoQ(arr2[-1])
                    while self.Stage.is_xmoving() or self.Stage.is_ymoving() or self.Stage.is_zmoving():
                        pass
                    #set2speed(F=int(speed2))
                    j = jEnd
                if self.stopCall:
                    break
        elif scanKind == 2:
            while True:
                self.collect_2DSHG_Signal(goto,p,q,i,j,k)
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
                self.collect_2DSHG_Signal(goto,p,q,i,j,k)
                j += 1
                if j >= len(arr2):
                    j = jEnd
                    while True:
                        self.collect_2DSHG_secondSignal(goto,p,q,i,j,k)
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
        goto(arr1[0],arr2[0])
        while self.Stage.is_xmoving() or self.Stage.is_ymoving() or self.Stage.is_zmoving():
            sleep(0.1)
        
    def XYZ_Scan_Step_Stage(self):
        self.shgData = zeros((len(self.zarr),len(self.xarr),len(self.yarr)))
        self.refData = -ones_like(self.shgData)
        self.imgData = ones_like(self.shgData)
        if self.scanKind == 0:
            self.shgData2 = zeros((len(self.zarr),len(self.xarr),len(self.yarr)))
            self.refData2 = -ones_like(self.shgData2)
            self.imgData2 = ones_like(self.shgData2)
        self.Stage.goto_xyz(self.xpos,self.ypos,self.zpos)
        while self.Stage.is_xmoving() or self.Stage.is_ymoving() or self.Stage.is_zmoving():
            sleep(0.1)
        self.Stage.set_zspeed(F=int(self.zspeed))
        self.Gal.start_single_point_counter()
        for k,z in enumerate(self.zarr):
            self.Stage.set_yspeed(F=int(self.yspeed))
            self.Stage.goto_z(z)
            while self.Stage.is_zmoving():
                pass
            self.scan3D_Stage(self.Stage.goto_xy,
                              self.xarr,self.yarr,
                              self.Stage.set_xspeed,self.Stage.set_yspeed,
                              self.xspeed,self.yspeed,
                              self.xhighspeed,self.yhighspeed,
                              self.scanKind,self.Stage.goto_x,k)
            if self.stopCall:
                break
        self.imageData3D.emit([self.shgData,self.refData,self.imgData])
        self.Gal.stop_single_point_counter()
        self.Stage.set_zspeed(F=int(self.zhighspeed))
        self.saveData()
        self.stop_program()
    
    def YXZ_Scan_Step_Stage(self):
        self.shgData = zeros((len(self.zarr),len(self.xarr),len(self.yarr)))
        self.refData = -ones_like(self.shgData)
        self.imgData = ones_like(self.shgData)
        if self.scanKind == 0:
            self.shgData2 = zeros((len(self.zarr),len(self.xarr),len(self.yarr)))
            self.refData2 = -ones_like(self.shgData2)
            self.imgData2 = ones_like(self.shgData2)
        self.Stage.goto_xyz(self.xpos,self.ypos,self.zpos)
        while self.Stage.is_xmoving() or self.Stage.is_ymoving() or self.Stage.is_zmoving():
            sleep(0.1)
        self.Stage.set_zspeed(F=int(self.zspeed))
        self.Gal.start_single_point_counter()
        for k,z in enumerate(self.zarr):
            self.Stage.set_xspeed(F=int(self.xspeed))
            self.Stage.goto_z(z)
            while self.Stage.is_zmoving():
                pass
            self.altscan3D_Stage(self.Stage.goto_xy,
                              self.xarr,self.yarr,
                              self.Stage.set_xspeed,self.Stage.set_yspeed,
                              self.xspeed,self.yspeed,
                              self.xhighspeed,self.yhighspeed,
                              self.scanKind,self.Stage.goto_y,k)
            if self.stopCall:
                break
        self.imageData3D.emit([self.shgData,self.refData,self.imgData])
        self.Gal.stop_single_point_counter()
        self.Stage.set_zspeed(F=int(self.zhighspeed))
        self.saveData()
        self.stop_program()
    
    def stop_program(self):
        if self.scanNum in (29,30,37):
            self.Gal.stop_scanxy()
        else:
            self.Gal.counter.stop()
            self.Gal.reference.stop()
        self.finished.emit()