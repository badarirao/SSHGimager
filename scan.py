# -*- coding: utf-8 -*-
"""
Created on Mon Feb  8 10:12:14 2021

@author: Badari

-> Confirm the minimum laser spot size, so the minimum step possible should be this spot size
-> Find out what is the maximum scan rate that can be used,
and set that limit in the program
-> x and y gives the actual position in mm or um
   in the program you specify voltage to the galvanometer, and for that
   the corresponding x and y voltages are stored as _x and _y, so use these
   in the program
   
--> some useful code for 3D view convenience:
    https://jeanbilheux.pages.ornl.gov/post/pyqtgraph_states/

--> how to alternate plot between image and graph.

--> make sure that when galvanometer is -3V,-3V, it is falling at start scan position 

--> while clicking select_scan_area button, check if roi button is already pressed, and disable that button first.

    The relationship between angle and voltage is quite simple. 
Plus minus 3V equals to plus minus 20 degree.
DA convertor has 16bits so it has plus minus 32767 resolution.
@author: Badari

# TODO: Check definition of galvano xhome and yhome may have changed
#TODO: Implement z-focus function
#TODO: load and save scan parameters to file
#TODO: Increase resolution of z-stage so that we can focus it better.
#TODO: Improve resolution of x andy y stage also?
#TODO: stage moves to previous position during startup
#TODO: implement 1D galvanoscan
#TODO incorporate logger module into the software
#TODO Clear button is not working
#TODO send prompts to status bar
#TODO A Facility for Batch Program
#TODO incorporate camera module into the software
# TODO: If scan mode is changed, prompt to ensure adapters are changed accordingly.
# TODO: add scan mode information in scan information
# TODO: Disable laser scan in reflection mode
# TODO: If counts are not detected, prompt to ask if adapters are set appropriately.
# Continuous scan: only trace gives wrong counts at the edges. Need to account for it
# TODO: GUI to view, process, and analyze all info from the image files.
"""

from numpy import ones, ndarray, shape,array, VisibleDeprecationWarning
import os, sys
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox, QShortcut
from PyQt5.QtCore import QThread, QTimer, QEventLoop
import pyqtgraph as pg
from scanner_gui import Ui_Scanner
from galvanometer_settings import galsetting
from ds102_settings import ds102setting
from time import sleep
from utilities import checkInstrument, Select, BUF
from Worker import ScanImage
from SciFiReaders import NSIDReader
import warnings

warnings.simplefilter(action='ignore', category=(FutureWarning,VisibleDeprecationWarning))

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

class SHGscan(QtWidgets.QMainWindow, Ui_Scanner):
    def __init__(self,*args, obj=None, **kwargs):
        super().__init__(*args,**kwargs)
        self.filename = "SHGimage"
        self.setupUi(self)
        self.imageMenu = QtWidgets.QMenu()
        self.selectImage_Button.setMenu(self.imageMenu)
        self.scan_method = 0
        self.pth = os.getcwd()
        self.autochange = False
        self.selectScanMethod()
        self.original_scanKind = self.scan_kind.currentIndex()
        self.update_screen()
        self.Gal, self.Stage = checkInstrument(ds102Port = self.ds102dialog.com, Fake = False)
        self.functionalize_buttons()
        self.xpos.setValue(self.Stage.x)
        self.ypos.setValue(self.Stage.y)
        self.zpos.setValue(self.Stage.z)
        self.initialize()
        self.initialize_plot()
        self.show()
        self.initGalvano()
        self.initStage()
        self.stagemoved = False
        self.display_stagemove_msg()
        self.stopcall = False
        self.plotNumber = 2
        self.collection = []
        self.ra1 = 10
        self.rb1 = 10
        self.scan_type_change()
        self.last_saved_filename = self.filename+'.shg'
        self.remCurrentImage = QShortcut(QtGui.QKeySequence('Ctrl+Del'), self)
        self.remCurrentImage.activated.connect(self.removeImage)
        self.delCollection = QShortcut(QtGui.QKeySequence('Shift+Ctrl+Del'), self)
        self.delCollection.activated.connect(self.deleteCollection)
        if self.Gal.ID == 'Fake' and self.Stage.ID == 'Fake':
            self.statusBar().showMessage('Instrument not found, simulation mode running')
        elif self.Gal.ID !='Fake' and self.Stage.ID != 'Fake':
            self.statusBar().showMessage('Connection successful, Instrument ready to scan.')
        else:
            if self.Gal.ID == 'Fake':
                self.statusBar().showMessage('Could not connect to galvanomirror, simulation mode running')
                self.Stage.close()
            elif self.Stage.ID == 'Fake':
                self.statusBar().showMessage('Could not connect to stage, simulation mode running')
                self.Gal.close_all_channels()
            self.Gal, self.Stage = checkInstrument(ds102Port = self.ds102dialog.com, Fake= True)
    
    def update_screen(self):
        self.galvanodialog = galsetting()
        self.galvanodialog.setWindowModality(QtCore.Qt.ApplicationModal)
        self.ds102dialog = ds102setting()
        self.ds102dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        self.initialPath = os.getcwd()
        if os.path.isfile('address.txt'):
            with open('address.txt','r') as f:
                lines = f.readlines()
                if len(lines) > 0:
                    try:
                        self.data_address = lines[1]
                    except:
                        self.data_address = ''
            if self.data_address and os.path.isdir(self.data_address):
                    os.chdir(self.data_address)
            else:
                # set default path to store measured data as desktop
                self.defaultPath = os.path.join(
                    os.path.expandvars("%userprofile%"), "Desktop")
                # set default path as current directory if desktop is not found in C drive
                if not os.path.exists(self.defaultPath):
                    self.defaultPath = self.initialPath 
                self.defaultPath += '\\SHG_Data'
                if len(lines)>1:
                    lines[-1] = self.defaultPath
                else:
                    lines.append(self.defaultPath)
                with open('address.txt','w') as f:
                    f.writelines(lines)
                if os.path.exists(self.defaultPath):
                    os.chdir(self.defaultPath)
                else:
                    os.makedirs(self.defaultPath)
                    os.chdir(self.defaultPath)
        else:
            print('address.txt not found.')
            print(' Create address.txt in the program location')
            print('1st line should contain path of setting file')
            print('2nd line should contain path of save directory')
        style1 = {'color':'y','size':'18pt'}
        style2 = {'color':'r','size':'16pt'}
        self.liveplot.ui.menuBtn.hide()
        self.ref_plot.ui.menuBtn.hide()
        self.liveplot.view.getViewBox().setMouseMode(pg.ViewBox.RectMode)
        self.ref_plot.view.getViewBox().setMouseMode(pg.ViewBox.RectMode)
        font=QtGui.QFont()
        font.setPixelSize(14)
        labelStyle = {'color': '#FFF', 'font-size': '12pt'}
        self.liveplot.view.setTitle("Active Scan",**style1)
        self.ref_plot.view.setTitle("Scan Collection",**style2)
        self.liveplot1d.setTitle("Active Scan",**style1)
        self.ref_plot1d.setTitle("Scan Collection",**style2)
        self.liveplot.view.getAxis("bottom").setTickFont(font)
        self.liveplot.view.getAxis("left").setTickFont(font)
        self.liveplot.view.getAxis("top").setTickFont(font)
        self.liveplot.view.getAxis("right").setTickFont(font)
        self.liveplot.view.getAxis("bottom").setLabel('', units='', **labelStyle)
        self.liveplot.view.getAxis("left").setLabel('', units='', **labelStyle)
        self.liveplot.setPredefinedGradient('magma')
        self.liveplot1d.getAxis("bottom").setLabel('',units='',**labelStyle)
        self.liveplot1d.getAxis("left").setLabel('',units='',**labelStyle)
        self.ref_plot.setPredefinedGradient('magma')
        self.ref_plot.view.getAxis("bottom").setTickFont(font)
        self.ref_plot.view.getAxis("left").setTickFont(font)
        self.ref_plot.view.getAxis("top").setTickFont(font)
        self.ref_plot.view.getAxis("right").setTickFont(font)
        self.ref_plot.view.getAxis("bottom").setLabel('', units='', **labelStyle)
        self.ref_plot.view.getAxis("left").setLabel('', units='', **labelStyle)
        self.ref_plot1d.getAxis("bottom").setLabel('',units='',**labelStyle)
        self.ref_plot1d.getAxis("left").setLabel('',units='',**labelStyle)
        self.scanNum = 0
        labels={'bottom': ("X",'μm'), 'left':("Y",'μm'),'top':"",'right':""}
        self.liveplot.view.setLabels(**labels)
        self.ref_plot.view.setLabels(**labels)
        self.setWindowTitle("SHG Imaging")
    
    def functionalize_buttons(self):
        self.xactive.stateChanged.connect(self.x_state_change)
        self.yactive.stateChanged.connect(self.y_state_change)
        self.zactive.stateChanged.connect(self.z_state_change)
        self.scan_type.currentIndexChanged.connect(self.scan_type_change)
        self.plot_type.currentIndexChanged.connect(self.selectPlotType)
        self.scan_kind.currentIndexChanged.connect(self.selectScanMethod)
        self.start_button.clicked.connect(self.run_program)
        self.stop_button.clicked.connect(self.stop_program)
        self.loadImage_button.clicked.connect(self.load_image_from_file)
        self.stageStop_Button.clicked.connect(self.stopStage)
        self.saveDir_button.clicked.connect(self.change_save_directory)
        self.imageMenu.triggered.connect(self.get_image_from_collection)
        self.select_scan_area.setCheckable(True)
        self.select_scan_area.clicked.connect(self.hideroiplot)
        self.actionGalvanometer.triggered.connect(self.setgalvano)
        self.actionExit.triggered.connect(self.close)
        self.actionSteppermotor.triggered.connect(self.setstage)
        self.xstep.valueChanged.connect(lambda: self.steps_to_points(self.xsize,self.xstep,self.xpoints))
        self.ystep.valueChanged.connect(lambda: self.steps_to_points(self.ysize,self.ystep,self.ypoints))
        self.zstep.valueChanged.connect(lambda: self.steps_to_points(self.zsize,self.zstep,self.zpoints))
        self.xsize.valueChanged.connect(lambda: self.steps_to_points(self.xsize,self.xstep,self.xpoints))
        self.ysize.valueChanged.connect(lambda: self.steps_to_points(self.ysize,self.ystep,self.ypoints))
        self.zsize.valueChanged.connect(lambda: self.steps_to_points(self.zsize,self.zstep,self.zpoints))
        self.srate_set.valueChanged.connect(lambda: self.rate_to_tstep(self.srate_set,self.tperstep_set))
        self.xpos.valueChanged.connect(self.update_sizelimits)
        self.ypos.valueChanged.connect(self.update_sizelimits)
        self.zpos.valueChanged.connect(self.update_sizelimits)
        self.tperstep_set.valueChanged.connect(lambda: self.tstep_to_rate(self.srate_set,self.tperstep_set))
        self.setdefaults()
        if self.scan_type.currentIndex() == 0:
            self.xsize.setMaximum(self.galvanodialog.xmax-self.galvanodialog.xmin)
            self.ysize.setMaximum(self.galvanodialog.ymax-self.galvanodialog.ymin)
        self.ref_plot.roi.sigRegionChanged.connect(self.getroidata)
        self.ref_plot.ui.roiBtn.clicked.connect(self.chkselbutton)
        self.liveplot.view.scene().sigMouseMoved.connect(self.printliveplot_MousePos)
        self.ref_plot.view.scene().sigMouseMoved.connect(self.printrefplot_MousePos)
        self.liveplot.ui.roiBtn.hide()
        self.scan_mode.setEnabled(False)  # currently disable selecting scan mode
        self.sample_name.setText(self.filename)
        self.sample_name.textChanged.connect(self.updatefile)
        self.toolButton_xhome.clicked.connect(self.gohome_xstage)
        self.toolButton_yhome.clicked.connect(self.gohome_ystage)
        self.toolButton_zhome.clicked.connect(self.gohome_zstage)
        self.Stage.set_xspeed(F=int(self.ds102dialog.xspeed))
        self.Stage.set_yspeed(F=int(self.ds102dialog.yspeed))
        self.Stage.set_zspeed(F=int(self.ds102dialog.zspeed))
        self.stageX.setMaximum(self.ds102dialog.xmax)
        self.stageX.setMinimum(self.ds102dialog.xmin)
        self.stageX.setValue(self.Stage.x)
        self.stageX.valueChanged.connect(self.updateXstage)
        self.stageX.setKeyboardTracking(False)
        self.stageY.setMaximum(self.ds102dialog.ymax)
        self.stageY.setMinimum(self.ds102dialog.ymin)
        self.stageY.setValue(self.Stage.y)
        self.stageY.setKeyboardTracking(False)
        self.stageY.valueChanged.connect(self.updateYstage)
        self.stageZ.setMaximum(self.ds102dialog.zmax)
        self.stageZ.setMinimum(self.ds102dialog.zmin)
        self.stageZ.setValue(self.Stage.z)
        self.stageZ.setKeyboardTracking(False)
        self.stageZ.valueChanged.connect(self.updateZstage)
        self.zpos.setMinimum(self.ds102dialog.zmin)
        self.zpos.setMaximum(self.ds102dialog.zmax)
        self.zsize.setMaximum(self.ds102dialog.zmax-self.zpos.value())
        self.xpos.setMaximum(self.ds102dialog.xmax)
        self.xpos.setMinimum(self.ds102dialog.xmin)
        self.ypos.setMaximum(self.ds102dialog.ymax)
        self.ypos.setMinimum(self.ds102dialog.ymin)
        self.zpos.setMaximum(self.ds102dialog.zmax)
        self.zpos.setMinimum(self.ds102dialog.zmin)
        self.scan_type.setCurrentIndex(1)
        self.xsize.setValue(500)
        self.ysize.setValue(500)
        self.zsize.setValue(500)
        self.xpoints.setValue(101)
        self.ypoints.setValue(101)
        self.zpoints.setValue(101)
        self.tperstep_set.setValue(0.01)
        self.xpoints.setReadOnly(True)
        self.ypoints.setReadOnly(True)
        self.zpoints.setReadOnly(True)
    
    def hide_stageStop_Button(self):
        self.stageStop_Button.setEnabled(False)
        
    def stopStage(self):
        self.Stage.stop_allstage()
        self.stageStop_Button.setEnabled(False)
        self.stageX.setValue(self.Stage.x)
        self.stageY.setValue(self.Stage.y)
        self.stageZ.setValue(self.Stage.z)
    
    def checkStage(self):
        if self.Stage.is_xmoving() or self.Stage.is_ymoving() or self.Stage.is_zmoving():
            QTimer.singleShot(100, self.checkStage)
        else:
            self.stageStop_Button.setEnabled(False)
        
    def gohome_xstage(self):
        self.stageStop_Button.setEnabled(True)
        self.stageX.setValue(self.ds102dialog.xhome)
        self.checkStage()
        
    def gohome_ystage(self):
        self.stageStop_Button.setEnabled(True)
        self.stageY.setValue(self.ds102dialog.yhome)
        self.checkStage()
    
    def gohome_zstage(self):
        self.stageStop_Button.setEnabled(True)
        self.stageZ.setValue(self.ds102dialog.zhome)
        self.checkStage()
        
    def updateXstage(self):
        self.stageStop_Button.setEnabled(True)
        self.Stage.x = self.stageX.value()
        self.checkStage()
    
    def updateYstage(self):
        self.stageStop_Button.setEnabled(True)
        self.Stage.y = self.stageY.value()
        self.checkStage()
        
    def updateZstage(self):
        self.stageStop_Button.setEnabled(True)
        self.Stage.z = self.stageZ.value()
        self.checkStage()
        
    def updatefile(self):
        self.stageStop_Button.setEnabled(True)
        self.filename = self.sample_name.text().split('_')[0]
                
    def chkselbutton(self):
        if self.select_scan_area.isChecked():
            self.select_scan_area.setChecked(False)
            self.ref_plot.roi.rotateAllowed = True
            self.ref_plot.roi.addRotateHandle([0, 0], [0.5, 0.5])
            
    def printliveplot_MousePos(self,pos):
        position = self.liveplot.view.vb.mapSceneToView(pos)
        mx = position.x()
        my = position.y()
        if mx > 0 and my > 0 and mx < self.a1 and my < self.b1:
            xi = int(mx/self.ascale)
            yi = int(my/self.bscale)
            if len(shape(self.image)) == 2:
                s = '   x = ' + str("{:.3f}").format(mx) + '   y = ' + str("{:.3f}").format(my) + '   Intensity = ' + str(self.image[xi,yi])
            elif len(shape(self.image)) == 3:
                intensity = self.image[self.liveplot.currentIndex,xi,yi]
                s = 'x: ' + str("{:.3f}").format(mx) + '   y: ' + str("{:.3f}").format(my) + \
                    '   z: ' + str("{:.3f}").format(self.zarr[self.liveplot.currentIndex]) + \
                    '   Intensity = ' + str(intensity)
            self.lineEdit_messagePrompt.setText(s)
        else:
            self.lineEdit_messagePrompt.setText("")
    
    def printrefplot_MousePos(self,pos):
        position = self.ref_plot.view.vb.mapSceneToView(pos)
        mx = position.x()
        my = position.y()
        if mx > 0 and my > 0 and mx < self.ra1 and my < self.rb1:
            xi = int(mx/self.rascale)
            yi = int(my/self.rbscale)
            if len(shape(self.rimage)) == 2:
                s = '   x = ' + str("{:.3f}").format(mx) + '   y = ' + str("{:.3f}").format(my) + '   Intensity = ' + str(self.rimage[xi,yi])
            elif len(shape(self.rimage)) == 3:
                intensity = self.rimage[self.ref_plot.currentIndex,xi,yi]
                s = 'x: ' + str("{:.3f}").format(mx) + '   y: ' + str("{:.3f}").format(my) + \
                    '   z: ' + str("{:.3f}").format(self.rcAxis[self.ref_plot.currentIndex]) + \
                    '   Intensity = ' + str(intensity)
            self.lineEdit_messagePrompt.setText(s)
        else:
            self.lineEdit_messagePrompt.setText("")
        
    def getroidata(self):
        # Extract image data from ROI
        if self.ref_plot.image is None:
            return

        image = self.ref_plot.getProcessedImage()

        # getArrayRegion axes should be (x, y) of data array for col-major,
        # (y, x) for row-major
        # can't just transpose input because ROI is axisOrder aware
        colmaj = self.ref_plot.imageItem.axisOrder == 'col-major'
        if colmaj:
            axes = (self.ref_plot.axes['x'], self.ref_plot.axes['y'])
        else:
            axes = (self.ref_plot.axes['y'], self.ref_plot.axes['x'])

        data, coords = self.ref_plot.roi.getArrayRegion(
            image.view(ndarray), img=self.ref_plot.imageItem, axes=axes,
            returnMappedCoords=True)
        if self.nd == 2:
            if 'X' not in [self.raAx,self.rbAx]:
                self.ypos.setValue(coords[0][0][0]+self.rypos)
                self.zpos.setValue(coords[1][0][0]+self.rzpos)
                self.ysize.setValue(coords[0][-1][-1]-coords[0][0][0])
                self.zsize.setValue(coords[1][-1][-1]-coords[1][0][0])
            elif 'Y' not in [self.raAx,self.rbAx]:
                self.xpos.setValue(coords[0][0][0]+self.rxpos)
                self.zpos.setValue(coords[1][0][0]+self.rzpos)
                self.xsize.setValue(coords[0][-1][-1]-coords[0][0][0])
                self.zsize.setValue(coords[1][-1][-1]-coords[1][0][0])
            elif 'Z' not in [self.raAx,self.rbAx]:
                self.xpos.setValue(coords[0][0][0]+self.rxpos)
                self.ypos.setValue(coords[1][0][0]+self.rypos)
                self.xsize.setValue(coords[0][-1][-1]-coords[0][0][0])
                self.ysize.setValue(coords[1][-1][-1]-coords[1][0][0])
        elif self.nd == 3:
            self.xpos.setValue(coords[0][0][0]+self.rxpos)
            self.ypos.setValue(coords[1][0][0]+self.rypos)
            self.xsize.setValue(coords[0][-1][-1]-coords[0][0][0])
            self.ysize.setValue(coords[1][-1][-1]-coords[1][0][0])
                
    def hideroiplot(self):
        if not self.ref_plot.isVisible():
            self.select_scan_area.setChecked(False)
            return
        if self.select_scan_area.isChecked():
            if self.ref_plot.ui.roiBtn.isChecked():
                self.ref_plot.ui.roiBtn.setChecked(False)
            self.ref_plot.roi.show()
            self.ref_plot.ui.roiPlot.setMouseEnabled(True, True)
            self.ref_plot.roiChanged()
            self.ref_plot.roi.rotateAllowed = False
            self.ref_plot.roi.setAngle(0)
            self.ref_plot.roi.removeHandle(1)  # remove the rotate handle
            self.ref_plot.ui.roiPlot.hide()
            self.getroidata()
        else:
            self.ref_plot.roi.hide()
            self.ref_plot.roi.rotateAllowed = True
            self.ref_plot.roi.addRotateHandle([0, 0], [0.5, 0.5])

    def rate_to_tstep(self,srate,tstep):
        if not tstep.isEnabled():
            tstep.setValue(1/srate.value())
    
    def tstep_to_rate(self,srate,tstep):
        if not srate.isEnabled():
            srate.setValue(1/tstep.value())
        
    def points_to_steps(self,size,steps,points):
        if points.value() == 1:
            points.setValue(2)
        steps.setValue(size.value()/(points.value()-1))
        #TODO: try to get step * points exactly equal to size
    
    def steps_to_points(self,size,steps,points):
        steps.setMaximum(size.value())
        s = steps.value()
        if s == 0:
            if self.scan_type.currentIndex() == 0:
                steps.setValue(0.0001)
                s = 0.0001
            else:
                steps.setValue(1)
                s = 1
        points.setValue(int(size.value()/s+1))
    
    def setdefaults(self):
        pass
        
    def getpoints(self):
        if self.nd == 0:
            return None
        elif self.nd == 1:
            if self.xactive.isChecked():
                return self.xpoints.value()
            elif self.yactive.isChecked():
                return self.ypoints.value()
            elif self.zactive.isChecked():
                return self.zpoints.value()
        elif self.nd == 2:
            if not self.xactive.isChecked():
                return self.ypoints.value(),self.zpoints.value()
            elif not self.yactive.isChecked():
                return self.xpoints.value(),self.zpoints.value()
            elif not self.zactive.isChecked():
                return self.xpoints.value(),self.ypoints.value()
        elif self.nd == 3:
            return self.zpoints.value(), self.xpoints.value(), self.ypoints.value()
        
    def verify_scan_order(self):
        if self.nd == 1:
            if self.xactive.isChecked():
                self.xscanorder.setCurrentIndex(0)
            elif self.yactive.isChecked():
                self.yscanorder.setCurrentIndex(0)
            elif self.zactive.isChecked():
                self.zscanorder.setCurrentIndex(0)
        elif self.nd == 2:
            if not self.xactive.isChecked():
                if self.yscanorder.currentIndex() == 0:
                    self.zscanorder.setCurrentIndex(1)
                elif self.yscanorder.currentIndex() == 1:
                    self.zscanorder.setCurrentIndex(0)
            elif not self.yactive.isChecked():
                if self.xscanorder.currentIndex() == 0:
                    self.zscanorder.setCurrentIndex(1)
                elif self.xscanorder.currentIndex() == 1:
                    self.zscanorder.setCurrentIndex(0)
            elif not self.zactive.isChecked():
                if self.xscanorder.currentIndex() == 0:
                    self.yscanorder.setCurrentIndex(1)
                elif self.xscanorder.currentIndex() == 1:
                    self.yscanorder.setCurrentIndex(0)
        elif self.nd == 3:
            self.zscanorder.setCurrentIndex(2)
            if self.xscanorder.currentIndex() == 0:
                self.yscanorder.setCurrentIndex(1)
            elif self.xscanorder.currentIndex() == 1:
                self.yscanorder.setCurrentIndex(0)
            
    def initialize(self):
        self.xposition = int(self.xpos.value())
        self.yposition = int(self.ypos.value())
        self.zposition = int(self.zpos.value())
        self.nd = 0
        if self.xactive.isChecked():
            self.nd = self.nd + 1
        if self.yactive.isChecked():
            self.nd = self.nd + 1
        if self.zactive.isChecked():
            self.nd = self.nd + 1
        if self.nd == 0:
            info = QMessageBox(self)
            info.setWindowTitle("Error!")
            info.setIcon(QMessageBox.Critical)
            info.setText("No axis selected. Please select atleast 1 axis to scan..")
            info.setStandardButtons(QMessageBox.Ok)
            info.show()
            self.stopcall = True
            return
        # there is some problem when ypoints <= 4
        if self.nd == 3 and self.ypoints.value() <= 4:
            self.ypoints.setValue(5)
        self.points_to_steps(self.xsize,self.xstep,self.xpoints)
        self.points_to_steps(self.ysize,self.ystep,self.ypoints)
        self.points_to_steps(self.zsize,self.zstep,self.zpoints)
        self.apoints = 1
        self.bpoints = 1
        self.cpoints = 1
        self.verify_scan_order()
        if self.nd == 1:
            self.apoints = self.getpoints()
            self.image = -ones((self.apoints))
        elif self.nd == 2:
            self.apoints,self.bpoints = self.getpoints()
            self.image = -ones((self.apoints,self.bpoints))
        elif self.nd == 3:
            self.cpoints,self.apoints, self.bpoints = self.getpoints()
            self.image = -ones((self.apoints,self.bpoints))
        if self.nd == 1:
            if self.xactive.isChecked():
                self.stageX.setValue(int(self.xpos.value()))
                self.yposition = self.stageY.value()
                self.zposition = self.stageZ.value()
                self.x0,self.x1 = 0,self.xsize.value()
                self.xscale = (self.x1-self.x0)/self.image.shape[0]
                self.a0, self.a1, self.asize = self.x0, self.x1, self.xsize.value()
                if self.scan_type.currentIndex() == 0:
                    if self.scan_method == 0:
                        self.scanNum = Select.X_Scan_Continuous_Galvano
                    else:
                        self.scanNum = Select.X_Scan_Step_Galvano
                else:
                    if self.scan_method == 0:
                        self.scanNum = Select.X_Scan_Continuous_Stage
                    else:
                        self.scanNum = Select.X_Scan_Step_Stage
                labels={'bottom': ("X",'μm'), 'left':("Intensity",'counts'),'top':"",'right':""}
            elif self.yactive.isChecked():
                self.stageY.setValue(int(self.ypos.value()))
                self.xposition = self.stageX.value()
                self.zposition = self.stageZ.value()
                self.y0,self.y1 = 0,self.ysize.value()
                self.yscale = (self.y1-self.y0)/self.image.shape[0]
                self.a0, self.a1, self.asize = self.y0, self.y1, self.ysize.value()
                if self.scan_type.currentIndex() == 0:
                    if self.scan_method == 0:
                        self.scanNum = Select.Y_Scan_Continuous_Galvano
                    else:
                        self.scanNum = Select.Y_Scan_Step_Galvano
                else:
                    if self.scan_method == 0:
                        self.scanNum = Select.Y_Scan_Continuous_Stage
                    else:
                        self.scanNum = Select.Y_Scan_Step_Stage
                labels={'bottom': ("Y",'μm'), 'left':("Intensity",'counts'),'top':"",'right':""}
            elif self.zactive.isChecked():
                self.xposition = self.stageX.value()
                self.yposition = self.stageY.value()
                self.stageZ.setValue(int(self.zpos.value()))
                self.z0,self.z1 = 0,self.zsize.value()
                self.a0, self.a1, self.asize = self.z0, self.z1, self.zsize.value()
                self.zscale = (self.z1-self.z0)/self.image.shape[0]
                labels={'bottom': ("Z",'μm'), 'left':("Intensity",'counts'),'top':"",'right':""}
                if self.scan_type.currentIndex() == 0:
                    self.scan_type.setCurrentIndex(1)
                if self.scan_method == 0:
                    self.scanNum = Select.Z_Scan_Continuous_Stage
                else:
                    self.scanNum = Select.Z_Scan_Step_Stage
        elif self.nd == 2:
            if not self.xactive.isChecked(): # yz scan
                self.stageY.setValue(int(self.ypos.value()))
                self.stageZ.setValue(int(self.zpos.value()))
                self.xposition = self.stageX.value()
                self.y0,self.y1 = 0,self.ysize.value()
                self.z0,self.z1 = 0,self.zsize.value()
                self.yscale, self.zscale = (self.y1-self.y0)/self.image.shape[0],(self.z1-self.z0)/self.image.shape[1]
                self.a0, self.a1, self.asize = self.y0, self.y1, self.ysize.value()
                self.b0, self.b1, self.bsize = self.z0, self.z1, self.zsize.value()
                self.ascale, self.bscale = self.yscale, self.zscale
                self.scan_type.setCurrentIndex(1) # you can improve it later
                if self.scan_type.currentIndex() == 0:
                    if self.scan_method == 0:
                        if self.yscanorder.currentIndex() == 0:
                            self.scanNum = Select.YZ_Scan_Continuous_Galvano
                        else:
                            self.scanNum = Select.ZY_Scan_Continuous_Galvano
                    else:
                        if self.yscanorder.currentIndex() == 0:
                            self.scanNum = Select.YZ_Scan_Step_Galvano
                        else:
                            self.scanNum = Select.ZY_Scan_Step_Galvano
                else:
                    if self.scan_method == 0:
                        if self.yscanorder.currentIndex() == 0:
                            self.scanNum = Select.YZ_Scan_Continuous_Stage
                        else:
                            self.scanNum = Select.ZY_Scan_Continuous_Stage
                    else:
                        if self.yscanorder.currentIndex() == 0:
                            self.scanNum = Select.YZ_Scan_Step_Stage
                        else:
                            self.scanNum = Select.ZY_Scan_Step_Stage
                labels={'bottom': ("Y",'μm'), 'left':("Z",'μm'),'top':"",'right':""}
            elif not self.yactive.isChecked(): # xz scan
                self.stageX.setValue(int(self.xpos.value()))
                self.stageZ.setValue(int(self.zpos.value()))
                self.yposition = self.stageY.value()
                self.x0,self.x1 = 0,self.xsize.value()
                self.z0,self.z1 = 0,self.zsize.value()
                self.xscale, self.zscale = (self.x1-self.x0)/self.image.shape[0],(self.z1-self.z0)/self.image.shape[1]
                self.a0, self.a1, self.asize = self.x0, self.x1, self.xsize.value()
                self.b0, self.b1, self.bsize = self.z0, self.z1, self.zsize.value()
                self.ascale, self.bscale = self.xscale, self.zscale
                self.scan_type.setCurrentIndex(1)
                if self.scan_type.currentIndex() == 0:
                    if self.scan_method == 0:
                        if self.xscanorder.currentIndex() == 0:
                            self.scanNum = Select.XZ_Scan_Continuous_Galvano
                        else:
                            self.scanNum = Select.ZX_Scan_Continuous_Galvano
                    else:
                        if self.xscanorder.currentIndex() == 0:
                            self.scanNum = Select.XZ_Scan_Step_Galvano
                        else:
                            self.scanNum = Select.ZX_Scan_Step_Galvano
                else:
                    if self.scan_method == 0:
                        if self.xscanorder.currentIndex() == 0:
                            self.scanNum = Select.XZ_Scan_Continuous_Stage
                        else:
                            self.scanNum = Select.ZX_Scan_Continuous_Stage
                    else:
                        if self.xscanorder.currentIndex() == 0:
                            self.scanNum = Select.XZ_Scan_Step_Stage
                        else:
                            self.scanNum = Select.ZX_Scan_Step_Stage
                labels={'bottom': ("X",'μm'), 'left':("Z",'μm'),'top':"",'right':""}
            elif not self.zactive.isChecked(): # xy scan
                self.stageX.setValue(int(self.xpos.value()))
                self.stageY.setValue(int(self.ypos.value()))
                self.zposition = self.stageZ.value()
                self.x0,self.x1 = 0,self.xsize.value()
                self.y0,self.y1 = 0,self.ysize.value()
                self.xscale, self.yscale = (self.x1-self.x0)/self.image.shape[0],(self.y1-self.y0)/self.image.shape[1]
                self.a0, self.a1, self.asize = self.x0, self.x1, self.xsize.value()
                self.b0, self.b1, self.bsize = self.y0, self.y1, self.ysize.value()
                self.ascale, self.bscale = self.xscale, self.yscale
                if self.scan_type.currentIndex() == 0:
                    if self.scan_method == 0:
                        if self.xscanorder.currentIndex() == 0:
                            self.scanNum = Select.XY_Scan_Continuous_Galvano
                        else:
                            self.scanNum = Select.YX_Scan_Continuous_Galvano
                    else:
                        if self.xscanorder.currentIndex() == 0:
                            self.scanNum = Select.XY_Scan_Step_Galvano
                        else:
                            self.scanNum = Select.YX_Scan_Step_Galvano
                else:
                    if self.scan_method == 0:
                        if self.xscanorder.currentIndex() == 0:
                            self.scanNum = Select.XY_Scan_Continuous_Stage
                        else:
                            self.scanNum = Select.YX_Scan_Continuous_Stage
                    else:
                        if self.xscanorder.currentIndex() == 0:
                            self.scanNum = Select.XY_Scan_Step_Stage
                        else:
                            self.scanNum = Select.YX_Scan_Step_Stage
                labels={'bottom': ("X",'μm'), 'left':("Y",'μm'),'top':"",'right':""}
        elif self.nd == 3: #xyz scan
            self.stageX.setValue(int(self.xpos.value()))
            self.stageY.setValue(int(self.ypos.value()))
            self.stageZ.setValue(int(self.zpos.value()))
            self.x0, self.x1 = 0,self.xsize.value()
            self.y0, self.y1 = 0,self.ysize.value()
            self.z0, self.z1 = 0,self.zsize.value()
            self.xscale, self.yscale = (self.x1-self.x0)/self.apoints,(self.y1-self.y0)/self.bpoints
            self.zscale = (self.z1-self.z0)/self.cpoints
            self.a0, self.a1, self.asize = self.x0, self.x1, self.xsize.value()
            self.b0, self.b1, self.bsize  = self.y0, self.y1, self.ysize.value()
            self.c0, self.c1, self.csize  = self.z0, self.z1, self.zsize.value()
            self.ascale, self.bscale, self.cscale  = self.xscale, self.yscale, self.zscale
            if self.scan_type.currentIndex() == 0:
                if self.scan_method == 0:
                    if self.xscanorder.currentIndex() == 0:
                        self.scanNum = Select.XYZ_Scan_Continuous_Galvano
                    else:
                        self.scanNum = Select.YXZ_Scan_Continuous_Galvano
                else:
                    if self.xscanorder.currentIndex() == 0:
                        self.scanNum = Select.XYZ_Scan_Step_Galvano
                    else:
                        self.scanNum = Select.YXZ_Scan_Step_Galvano
            else:
                if self.scan_method == 0:
                    if self.xscanorder.currentIndex() == 0:
                        self.scanNum = Select.XYZ_Scan_Continuous_Stage
                    else:
                        self.scanNum = Select.YXZ_Scan_Continuous_Stage
                else:
                    if self.xscanorder.currentIndex() == 0:
                        self.scanNum = Select.XYZ_Scan_Step_Stage
                    else:
                        self.scanNum = Select.YXZ_Scan_Step_Stage
            labels={'bottom': ("X",'μm'), 'left':("Y",'μm'),'top':"",'right':""}
        if self.nd >1:
            if not self.liveplot.isVisible():
                self.liveplot.show()
                #self.ref_plot.show()
                self.liveplot1d.hide()
                #self.ref_plot1d.hide()
            self.liveplot.view.setLabels(**labels)
            self.liveplot.setImage(self.image,pos=[self.a0,self.b0],scale=[self.ascale,self.bscale])
        elif self.nd == 1: # 1d plot
            # yet to be implemented
            if self.liveplot.isVisible():
                self.liveplot.hide()
                #self.ref_plot.hide()
                self.liveplot1d.show()
                #self.ref_plot1d.show()
            self.liveplot1d.setLabels(**labels)
            
        
    def setgalvano(self):
        if self.galvanodialog.exec_():
            self.initGalvano()
    
    def initGalvano(self):
        self.Gal.xscale = self.galvanodialog.xscale
        self.Gal.yscale = self.galvanodialog.yscale
        self.Gal.x = self.galvanodialog.xpos/self.galvanodialog.xscale
        self.Gal.y = self.galvanodialog.ypos/self.galvanodialog.yscale
        self.Gal.xhome = self.galvanodialog.xpos
        self.Gal.yhome = self.galvanodialog.ypos
        if self.scan_type.currentIndex() == 0:
            self.update_sizelimits()

    def update_sizelimits(self):
        self.zsize.setMaximum(self.ds102dialog.zmax-self.zpos.value())
        if self.scan_type.currentIndex() == 1:
            self.xsize.setMaximum(self.ds102dialog.xmax-self.xpos.value())
            self.ysize.setMaximum(self.ds102dialog.ymax-self.ypos.value())
        else:
            self.xsize.setMaximum(self.galvanodialog.xmax-self.galvanodialog.xmin)
            self.ysize.setMaximum(self.galvanodialog.ymax-self.galvanodialog.ymin)
            
    def setstage(self):
        if self.ds102dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.initStage()
    
    def initStage(self):
        self.zpos.setMaximum(self.ds102dialog.zmax)
        self.zpos.setMinimum(self.ds102dialog.zmin)
        self.stageX.setMaximum(self.ds102dialog.xmax)
        self.stageX.setMinimum(self.ds102dialog.xmin)
        self.stageY.setMaximum(self.ds102dialog.ymax)
        self.stageY.setMinimum(self.ds102dialog.ymin)
        self.stageZ.setMaximum(self.ds102dialog.zmax)
        self.stageZ.setMinimum(self.ds102dialog.zmin)
        self.Stage.set_xspeed(F=int(self.ds102dialog.xspeed))
        sleep(0.1)
        self.Stage.set_yspeed(F=int(self.ds102dialog.yspeed))
        sleep(0.1)
        self.Stage.xscale = self.ds102dialog.xscale
        self.Stage.yscale = self.ds102dialog.yscale
        self.Stage.zscale = self.ds102dialog.zscale
        self.Stage.xhome = self.ds102dialog.xhome
        self.Stage.yhome = self.ds102dialog.yhome
        self.Stage.zhome = self.ds102dialog.zhome
        self.Stage.set_zspeed(F=int(self.ds102dialog.zspeed))
        self.xpos.setMaximum(self.ds102dialog.xmax)
        self.xpos.setMinimum(self.ds102dialog.xmin)
        self.ypos.setMaximum(self.ds102dialog.ymax)
        self.ypos.setMinimum(self.ds102dialog.ymin)
        self.update_sizelimits()
            
    def initialize_plot(self):
        self.rx0,self.rx1 = (0,self.ds102dialog.xmax)
        self.ry0,self.ry1 = (0,self.ds102dialog.ymax)
        self.rimg = -ones((500,500))
        self.rxscale, self.ryscale = 1,1
        self.ref_plot.setImage(self.rimg,pos=[self.rx0,self.ry0],scale=[self.rxscale,self.ryscale])

        if self.nd > 1:
            self.liveplot.setImage(self.image,pos=[self.a0,self.b0],scale=[self.ascale,self.bscale])
            #self.ref_plot.setImage(self.img,pos=[self.a0,self.y0],scale=[self.xscale,self.yscale])
        elif self.nd == 1:
            pass # implement to plot a 2d graph instead of image
        elif self.nd == 0:
            pass # prompt dialogue to say that no axis is selected for scanning
                 
      
    def stagefinished(self):
        self.stagemoved = True
    
    def display_stagemove_msg(self):
        loop = QEventLoop()
        info = QMessageBox(self)
        info.setWindowTitle("Stage in Motion..")
        info.setIcon(QMessageBox.Information)
        info.setText("Stage is moving, Please wait...")
        info.setStandardButtons(QMessageBox.NoButton)
        if self.Stage.ID == 'Fake':
            info.show()
            QTimer.singleShot(1000, loop.quit)
            loop.exec()
        else:
            if self.Stage.is_xmoving() or self.Stage.is_ymoving() or self.Stage.is_zmoving():
                info.show()
                while self.Stage.is_xmoving() or self.Stage.is_ymoving() or self.Stage.is_zmoving():
                    QTimer.singleShot(100, loop.quit)
                    loop.exec()
        info.hide()
    
    """
    def display_stagemove_msg(self):
        #loop = QEventLoop()
        info = QMessageBox(self)
        info.setWindowTitle("Stage in Motion..")
        info.setIcon(QMessageBox.Information)
        info.setText("Stage is moving, Please wait...")
        info.setStandardButtons(QMessageBox.NoButton)
        stageStatus = MonitorStage(self.Stage)
        stageStatus.start()
        stageStatus.finished.connect(info.hide)
        stageStatus.finished.connect(self.stagefinished)
        stageStatus.finished.connect(stageStatus.deleteLater)
        info.exec()
        while not self.stagefinished:
            sleep(0.1)
            #QTimer.singleShot(1000, loop.quit)
            #loop.exec_()
    """
    
    def get_savefilename(self):
        if self.filename.find('.') != -1:
            index = self.filename.rindex('.')  # rindex returns the last location of '.'
            self.filename = self.filename[:index]
        self.sample_name.setText(self.filename)
        
    def selectScanMethod(self):
        i = self.scan_kind.currentIndex()
        if not self.autochange:
            self.original_scanKind = i
        if i == 0:
            self.scanKind = 1
        elif i == 1:
            self.scanKind = -1
        elif i == 2:
            self.scanKind = 0
        elif i == 3:
            self.scanKind = 2
        
    def run_program(self):
        self.stopcall = False
        self.initialize()
        if self.stopcall:
            return
        self.display_stagemove_msg()
        self.Stage.x = self.xposition-BUF
        self.Stage.y = self.yposition-BUF
        self.Stage.z = self.zposition-BUF
        self.display_stagemove_msg()
        self.Stage.x = self.xposition
        self.Stage.y = self.yposition
        self.Stage.z = self.zposition
        self.display_stagemove_msg()
        print('Started {0} Scan...'.format(Select.scanName(self.scanNum)))
        self.stop_button.setEnabled(True)
        self.start_button.setEnabled(False)
        self.scan_type.setEnabled(False)
        self.stageStop_Button.setEnabled(False)
        self.sample_name.setEnabled(False)
        self.comments.setEnabled(False)
        self.get_savefilename()
        self.draw_original_PlotType_menu()
        self.initiallevel = 0
        self.autolevel = True
        #print("Initial: {0} {1}".format(self.Gal._x,self.Gal._y))
        self.scanParams = [self.nd,
                           self.scanNum, 
                           self.xposition, 
                           self.yposition, 
                           self.zposition, 
                           self.xsize.value(),
                           self.ysize.value(),
                           self.zsize.value(),
                           self.xpoints.value(),
                           self.ypoints.value(),
                           self.zpoints.value(),
                           self.ds102dialog.xscanspeed,
                           self.ds102dialog.yscanspeed,
                           self.ds102dialog.zscanspeed,
                           self.srate_set.value(),
                           self.ds102dialog.xspeed,
                           self.ds102dialog.yspeed,
                           self.ds102dialog.zspeed,
                           self.scanKind,
                           self.comments.toPlainText()
                           ]
        # start Thread
        self.thread = QThread()
        self.worker = ScanImage(self.scanParams,self.Gal, self.Stage, self.filename)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.startScan)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.lineData.connect(self.plotLine)
        self.worker.imageData.connect(self.plotImage)
        self.worker.imageData3D.connect(self.plot3DImage)
        self.worker.checkRef.connect(self.ref_status)
        self.worker.initialData.connect(self.updateInitialData)
        self.worker.finalEmit.connect(self.getfilename)
        self.thread.finished.connect(self.finishAction)
        self.thread.start()
        
    def getfilename(self,fname):
        self.last_saved_filename = fname
        
    def ref_status(self, reference_ON):
        if not reference_ON:
            prompt = "Reference signal is not turned on. Continue without reference?"
            reply = QtGui.QMessageBox.question(self, 'Message', 
                     prompt, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
            if reply == QtGui.QMessageBox.Yes:
                self.worker.go_ahead.emit(True)
            else:
                self.worker.go_ahead.emit(False)
        else:
            self.worker.go_ahead.emit(True)
            
    def updateInitialData(self, mes):
        self.current_Scan_detail = mes[0]
        self.axis1 = mes[1]
        if self.nd == 1:
            self.liveplot1d.clear()
            self.axis2 = 'counts (a.u.)'
            pen2 = pg.mkPen(color = (0,0,255), width = 2)
            self.data_line = self.liveplot1d.plot([mes[2]],[0],pen=pen2)
        elif self.nd == 2:
            self.ascale = mes[3]
            self.bscale = mes[4]
            #self.liveplot.setImage(mes[2],pos=[self.a0,self.b0],scale=[self.ascale,self.bscale])
        elif self.nd == 3:
            self.ascale = mes[4]
            self.bscale = mes[5]
            self.zarr = mes[6]
    
    def selectPlotType(self):
        self.plotNumber = self.plot_type.currentIndex()
        if self.stopcall:
            if self.nd == 1:
                self.image = self.imageData[self.plotNumber+1]
                self.image = self.image.round(decimals = 6)
                self.liveplot1d.enableAutoRange(enable = True)
                self.data_line.setData(self.imageData[0],self.image)
            elif self.nd == 2:
                self.image = self.imageData[self.plotNumber]
                self.image = self.image.round(decimals = 6)
                self.liveplot.setImage(self.image,pos=[0,0],scale=[self.ascale,self.bscale])
            elif self.nd == 3:
                self.image = self.imageData[self.plotNumber]
                self.image = self.image.round(decimals = 6)
                self.liveplot.setImage(self.image,pos=[0,0],scale=[self.ascale,self.bscale],xvals = self.zarr)
        
    def plotLine(self,imageData):
        self.image = array(imageData[self.plotNumber+1])
        self.image = self.image.round(decimals = 6)
        self.data_line.setData(imageData[0],self.image)
        
    def plotImage(self,imageData):
        if self.autolevel == True:
            self.initiallevel += 1
            if self.initiallevel > 10:
                self.autolevel = False
        self.image = imageData[self.plotNumber]
        self.image = self.image.round(decimals = 6)
        self.liveplot.setImage(self.image,pos=[0,0],scale=[self.ascale,self.bscale],autoLevels=self.autolevel)
    
    def plot3DImage(self,imageData):
        self.image = imageData[self.plotNumber]
        self.image = self.image.round(decimals = 6)
        self.liveplot.setImage(self.image,pos=[0,0],scale=[self.ascale,self.bscale],xvals = self.zarr,autoHistogramRange=False)
    
    def change_save_directory(self):
        folderpath = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folderpath:
            os.chdir(self.pth)
            with open('address.txt','r') as f:
                lines = f.readlines()
            if len(lines)>1:
                lines[-1] = folderpath
            else:
                lines.append(folderpath)
            with open('address.txt','w') as f:
                f.writelines(lines)
            os.chdir(folderpath)
        
    def load_image_from_file(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(self,"QFileDialog.getOpenFileNames()", "","All Files (*);;Parameter Files (*.txt)", options=options)
        if files:
            dataSet = NSIDReader(files[0]).read()
            self.loadData(dataSet)
        
    def loadData(self, dataSet):
        no_of_datasets = len(dataSet)
        for dset in dataSet:
            if dset.modality == 'Scan Information':
                info = dset.metadata['metadata']
                break
        self.imageData = [[]]
        l = 0
        if info['Dimension'] == 1:
            l = 1
            self.imageData[0] = array(dataSet[0].aAxis)
        for i in range(no_of_datasets-2+l):
            self.imageData.append([])
        for dset in dataSet:
            if 'raw' in dset.title:
                if 'Retrace' in dset.title:
                    self.imageData[l+3] = array(dset)
                else:
                    self.imageData[l] = array(dset)
            elif 'reference' in dset.title:
                if 'Retrace' in dset.title:
                    self.imageData[l+4] = array(dset)
                else:
                    self.imageData[l+1] = array(dset)
            elif 'processed' in dset.title:
                if 'Retrace' in dset.title:
                    self.imageData[l+5] = array(dset)
                else:
                    self.imageData[l+2] = array(dset)
        #print(len(self.imageData))
        #print(self.imageData[0].shape)
        dset = []
        for data in dataSet:
            dset.append(data.copy())
        self.collection.append(dset)
        self.updateCollection(self.collection[-1])
        self.display_image_from_collection(dset,'processed')
        dataSet[0].h5_dataset.file.close()
    
    def add_menu(self, data, menu_obj):
        if isinstance(data,dict):
            for k,v in data.items():
                sub_menu = QtWidgets.QMenu(k, menu_obj)
                menu_obj.addMenu(sub_menu)
                self.add_menu(v, sub_menu)
        elif isinstance(data, list):
            for element in data:
                self.add_menu(element, menu_obj)
        else:
            action = menu_obj.addAction(data)
            action.setIconVisibleInMenu(False)
        
    def updateCollection(self,dset):
        imageNames = []
        for item in dset:
            if item.modality == 'Scan Information':
                fname = item.metadata['metadata']['File Name']
            else:
                imageNames.append(item.title.split('/')[-1])
        menuItem = {fname:imageNames}
        self.add_menu(menuItem,self.imageMenu)
    
    def get_image_from_collection(self,x):
        imageName = x.text()
        fileName = x.parent().title()
        for item in self.collection:
            for image in item:
                if image.modality == 'Scan Information':
                    info = image.metadata['metadata']
                    break
            if info['File Name'] == fileName:
                self.display_image_from_collection(item,imageName)
                break
    
    def display_image_from_collection(self,item,imageName):
        for image in item:
            if image.modality == 'Scan Information':
                info = image.metadata['metadata']
                break
        fileName = info['File Name']
        for image in item:
            if imageName.lower() in image.title.lower():
                self.rimage = array(image)
                self.rxpos = info['x-position']
                self.rypos = info['y-position']
                self.rzpos = info['z-position']
                self.raAx = info['aAxis']['Axis']
                if info['Dimension'] == 1:
                    self.raAxis = array(image.aAxis)
                    labels={'bottom': (image.aAxis.quantity,image.aAxis.units), 
                            'left':(image.quantity,image.units),
                            'top':"",
                            'right':""}
                    if self.ref_plot.isVisible():
                        self.ref_plot.hide()
                        self.ref_plot1d.show()
                    self.ref_plot1d.setLabels(**labels)
                    self.ref_plot1d.clear()
                    self.ref_plot1d.enableAutoRange(enable = True)
                    pen2 = pg.mkPen(color = (0,0,255), width = 2)
                    self.ref_plot1d.plot(self.raAxis,self.rimage,pen=pen2)
                    self.ref_plot1d.setTitle("Scan Collection"+'<br><font size="-0.5" color="white">'+fileName+', '+imageName+ ' Image')
                elif info['Dimension'] == 2:
                    self.rbAx = info['bAxis']['Axis']
                    self.ra1 = info['aAxis']['Size']
                    self.rb1 = info['bAxis']['Size']
                    self.rascale = info['aAxis']['Scale']
                    self.rbscale = info['bAxis']['Scale']
                    labels={'bottom': (image.aAxis.quantity,image.aAxis.units), 
                            'left':(image.bAxis.quantity,image.bAxis.units),
                            'top':"",
                            'right':""}
                    if not self.ref_plot.isVisible():
                        self.ref_plot1d.hide()
                        self.ref_plot.show()
                    self.ref_plot.view.setLabels(**labels)
                    self.ref_plot.setImage(self.rimage,pos=[0,0],scale=[info['aAxis']['Scale'],info['bAxis']['Scale']])                        
                    self.ref_plot.view.setTitle("Scan Collection"+'<br><font size="-0.5" color="white">'+fileName+', '+imageName+ ' Image')
                elif info['Dimension'] == 3:
                    self.rbAx = info['bAxis']['Axis']
                    self.rcAxis = array(image.cAxis)
                    self.ra1 = info['aAxis']['Size']
                    self.rb1 = info['bAxis']['Size']
                    self.rascale = info['aAxis']['Scale']
                    self.rbscale = info['bAxis']['Scale']
                    labels={'bottom': (image.aAxis.quantity,image.aAxis.units), 
                            'left':(image.bAxis.quantity,image.bAxis.units),
                            'top':"",
                            'right':""}
                    if not self.ref_plot.isVisible():
                        self.ref_plot1d.hide()
                        self.ref_plot.show()
                    self.ref_plot.view.setLabels(**labels)
                    self.ref_plot.setImage(self.rimage,pos=[0,0],scale=[info['aAxis']['Scale'],info['bAxis']['Scale']],xvals = self.rcAxis)
                    self.ref_plot.view.setTitle("Scan Collection"+'<br><font size="-0.5" color="white">'+fileName+', '+imageName+ ' Image')
                break

    def redraw_PlotType_menu(self):
        self.plot_type.clear()
        self.plot_type.addItems(['Raw SHG Data Trace',
                                 'Reference Data Trace',
                                 'Processed Data Trace',
                                 'Raw SHG Data Retrace',
                                 'Reference Data Retrace',
                                 'Processed Data Retrace'])
    
    def draw_original_PlotType_menu(self):
        self.plot_type.clear()
        self.plot_type.addItems(['Raw SHG Data',
                                 'Reference Data',
                                 'Processed Data'])
        
    def finishAction(self):
        # set stage speed to original
        # be ready for next scan
        self.start_button.setEnabled(True)
        self.scan_type.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.stopcall = True
        self.comments.setEnabled(True)
        self.sample_name.setEnabled(True)
        dataSet = NSIDReader(self.last_saved_filename).read()
        self.loadData(dataSet)
        if len(dataSet) > 4:
            self.redraw_PlotType_menu()
        self.stageX.setValue(int(self.Stage.x))
        self.stageY.setValue(int(self.Stage.y))
        self.stageZ.setValue(int(self.Stage.z))
        if self.scanNum == Select.Z_Scan_Step_Stage:
            info = None
            for dset in dataSet:
                if dset.modality == 'Scan Information':
                    info = dset.metadata['metadata']
                    break
            if info:
                peak_position = 0
                peak_intensity = 0
                try:
                    peak_position = int(info['Z-Focus Peak Position'])
                    peak_intensity = info['Z-Focus Peak Intensity']
                except KeyError:
                    pass
                if peak_position and peak_intensity:
                    peak_label = pg.TextItem('',**{'color': '#FFF'})
                    font=QtGui.QFont()
                    font.setPixelSize(20)
                    peak_label.setFont(font)
                    peak_label.setPos(QtCore.QPointF(info['z-position'],peak_intensity))
                    peak_label.setText('Peak Position: {}'.format(peak_position))
                    self.ref_plot1d.addItem(peak_label)
                    mesBox = QMessageBox(self)
                    mesBox.setWindowTitle("Move Z to Focus?")
                    mesBox.setIcon(QMessageBox.Question)
                    mesBox.setText("Automatically set Z to focus?")
                    mesBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                    returnValue = mesBox.exec()
                    if returnValue == QMessageBox.Ok:
                        if info['Z-Focus peak on'] == 'Retrace':
                            self.Stage.z = peak_position + 20
                        elif info['Z-Focus peak on'] == 'Trace':
                            self.Stage.z = peak_position - 20
                        while self.Stage.is_zmoving():
                            pass
                        self.stageZ.setValue(peak_position)
                
        #print("Final laser position: {0} {1}".format(self.Gal._x,self.Gal._y))
        
    def x_state_change(self):
        if self.xactive.isChecked():
            self.xpos.setEnabled(True)
            self.xsize.setEnabled(True)
            self.xstep.setEnabled(True)
            self.xpoints.setEnabled(True)
            self.xscanorder.setEnabled(True)
        else:
            self.xpos.setEnabled(False)
            self.xsize.setEnabled(False)
            self.xstep.setEnabled(False)
            self.xpoints.setEnabled(False)
            self.xscanorder.setEnabled(False)
    
    def y_state_change(self):
        if self.yactive.isChecked():
            self.ypos.setEnabled(True)
            self.ysize.setEnabled(True)
            self.ystep.setEnabled(True)
            self.ypoints.setEnabled(True)
            self.yscanorder.setEnabled(True)
        else:
            self.ypos.setEnabled(False)
            self.ysize.setEnabled(False)
            self.ystep.setEnabled(False)
            self.ypoints.setEnabled(False)
            self.yscanorder.setEnabled(False)
            
    def z_state_change(self):
        if self.zactive.isChecked():
            self.zpos.setEnabled(True)
            self.zsize.setEnabled(True)
            self.zstep.setEnabled(True)
            self.zpoints.setEnabled(True)
            self.zscanorder.setEnabled(True)
        else:
            self.zpos.setEnabled(False)
            self.zsize.setEnabled(False)
            self.zstep.setEnabled(False)
            self.zpoints.setEnabled(False)
            self.zscanorder.setEnabled(False)
    
    def scan_type_change(self):
        if self.scan_type.currentIndex() == 1:
            self.scan_method = 1
            self.scan_kind.setCurrentIndex(self.original_scanKind)
            self.autochange = False
            self.srate_set.setEnabled(False)
            self.tperstep_set.setEnabled(True)
            self.xsize.setMaximum(self.ds102dialog.xmax-self.xpos.value())
            self.xsize.setSingleStep(1)
            self.xsize.setDecimals(0)
            self.ysize.setMaximum(self.ds102dialog.ymax-self.ypos.value())
            self.ysize.setSingleStep(1)
            self.ysize.setDecimals(0)
            self.xstep.setMinimum(1)
            self.xstep.setMaximum(self.ds102dialog.xmax-self.xpos.value())
            self.xstep.setDecimals(0)
            self.xstep.setSingleStep(1)
            self.ystep.setMinimum(1)
            self.ystep.setMaximum(self.ds102dialog.ymax-self.ypos.value())
            self.ystep.setDecimals(0)
            self.ystep.setSingleStep(1)
            self.xpos.setDecimals(0)
            self.ypos.setDecimals(0)
        else:
            self.scan_method = 0
            self.original_scanKind = self.scan_kind.currentIndex()
            self.autochange = True
            self.scan_kind.setCurrentIndex(3)
            self.srate_set.setEnabled(True)
            self.tperstep_set.setEnabled(False)
            self.xstep.setMinimum(0.0001)
            self.xstep.setMaximum(self.galvanodialog.xmax-self.galvanodialog.xmin)
            self.xstep.setDecimals(4)
            self.xstep.setSingleStep(0.01)
            self.ystep.setMinimum(0.0001)
            self.ystep.setMaximum(self.galvanodialog.ymax-self.galvanodialog.ymin)
            self.ystep.setDecimals(4)
            self.ystep.setSingleStep(0.01)
            self.xsize.setMaximum(self.galvanodialog.xmax-self.galvanodialog.xmin)
            self.xsize.setDecimals(4)
            self.xsize.setSingleStep(0.1)
            self.ysize.setMaximum(self.galvanodialog.ymax-self.galvanodialog.ymin)
            self.ysize.setDecimals(4)
            self.ysize.setSingleStep(0.1)
    
    def deleteCollection(self):
        self.collection = []
        self.imageMenu.clear()
        self.ref_plot1d.clear()
        self.ref_plot.clear()
    
    def removeImage(self):
        # Remove the active image from the collection
        print('Not Implemented yet')
    
    def stop_program(self):
        self.worker.stopcall.emit()
        self.start_button.setEnabled(True)
        self.scan_type.setEnabled(True)
        self.stop_button.setEnabled(False)
        
    def close_channels(self):
        self.Gal.close_all_channels()
        self.Stage.close()
   
    def closeEvent(self, event):
        quit_msg = "Are you sure you want to exit the program?"
        reply = QtGui.QMessageBox.question(self, 'Message', 
                     quit_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            try:
                self.close_channels()
            except AttributeError:
                pass
            event.accept()
        else:
            event.ignore()

def main():
    app = QtWidgets.QApplication(sys.argv)
    gui = SHGscan()
    gui.show()
    #main.connect_instrument()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
      


        
        
    

