# -*- coding: utf-8 -*-
"""
Created on Mon Feb  8 10:12:14 2021

@author: Badari

-> Add z-focus function
-> Confirm the minimum laser spot size, so the minimum step possible should be this spot size
-> Find out what is the maximum scan rate that can be used, 
and set that limit in the program
-> x and y gives the actual position in mm or um 
   in the program you specify voltage to the galvanometer, and for that 
   the corresponding x and y voltages are stored as _x and _y, so use these 
   in the program
-> Take care of proper handling of the tasks during abrupt closing
-> Check partial buffering -> register every n samples, and display it in the screen
https://stackoverflow.com/questions/56366033/continuous-acquistion-with-nidaqmx
https://stackoverflow.com/questions/60947373/continuous-analog-read-from-national-instruments-daq-with-nidaqmx-python-package

-> How to count for a specific time period exactly
    
--> some useful code for 3D view convenience:
    https://jeanbilheux.pages.ornl.gov/post/pyqtgraph_states/

--> how to alternate plot between image and graph.

--> make sure that when galvanometer is -3V,-3V, it is falling at start scan position 

--> while clicking select_scan_area button, check if roi button is already pressed, and disable that button first.

    The relationship between angle and voltage is quite simple. 
Plus minus 3V equals to plus minus 20 degree.
DA convertor has 16bits so it has plus minus 32767 resolution.
@author: Badari


#TODO ABRUPT stop button for stage (to stop accidental movement of stage)
        When stage position is changed, until it is done moving, paint the box in red.
        Once it has stopped moving, paint it back to grey color.
        The abrupt stop button must be active only when any of the stage is moving.

#TODO incorporate logger module into the software
#TODO Clear button is not working
#TODO galsetting and ds102setting widget has "reset to default button" and "set as default button" pending
#TODO send prompts to status bar
#TODO A Facility for Batch Program
#TODO incorporate camera module into the software
#TODO Make use of reference image to determine next scan parameters 
# TODO make use of new python style - " match - case ""
# Initial stage moving before scan is very slow
# Abort scan when stage is moving to scan position
# TODO: in scan type 37, if y has less than 5 points to scan, there is some problem
# in drawing the final 3d image. Only half of 2d image of last scan is drawn.
# TODO: If scan mode is changed, prompt to ensure adapters are changed accordingly.
# TODO: If counts are not detected, prompt to ask if adapters are set appropriately.

"""

from numpy import ones, ndarray, shape,array
import os, sys
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QThread
import pyqtgraph as pg
from scanner_gui import Ui_Scanner
from galvanometer_settings import galsetting
from ds102_settings import ds102setting
from time import sleep
from utilities import checkInstrument, MonitorStage, Select
from Worker import ScanImage

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
        self.scan_method = 0
        self.autochange = False
        self.selectScanMethod()
        self.original_scanKind = self.scan_kind.currentIndex()
        self.update_screen()
        self.Gal, self.Stage = checkInstrument(ds102Port = self.ds102dialog.com, Fake= True)
        self.functionalize_buttons()
        self.initialize()
        self.initialize_plot()
        self.show()
        self.initGalvano()
        self.initStage()
        self.display_stagemove_msg()
        self.stopcall = True
        self.plotNumber = 2
        self.scan_type_change()
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
        self.pth = os.path.dirname(__file__)
        self.galvanodialog = galsetting()
        os.chdir(self.pth)
        self.galvanodialog.setWindowModality(QtCore.Qt.ApplicationModal)
        self.ds102dialog = ds102setting()
        self.ds102dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        style1 = {'color':'y','size':'18pt'}
        style2 = {'color':'r','size':'18pt'}
        self.liveplot.ui.menuBtn.hide()
        self.ref_plot.ui.menuBtn.hide()
        self.liveplot.view.getViewBox().setMouseMode(pg.ViewBox.RectMode)
        self.ref_plot.view.getViewBox().setMouseMode(pg.ViewBox.RectMode)
        font=QtGui.QFont()
        font.setPixelSize(14)
        labelStyle = {'color': '#FFF', 'font-size': '12pt'}
        self.liveplot.view.setTitle("Active Mapping",**style1)
        self.ref_plot.view.setTitle("Reference Map",**style2)
        self.liveplot.view.getAxis("bottom").setTickFont(font)
        self.liveplot.view.getAxis("left").setTickFont(font)
        self.liveplot.view.getAxis("top").setTickFont(font)
        self.liveplot.view.getAxis("right").setTickFont(font)
        self.liveplot.view.getAxis("bottom").setLabel('', units='', **labelStyle)
        self.liveplot.view.getAxis("left").setLabel('', units='', **labelStyle)
        self.liveplot.setPredefinedGradient('magma')
        self.ref_plot.view.getAxis("bottom").setTickFont(font)
        self.ref_plot.view.getAxis("left").setTickFont(font)
        self.ref_plot.view.getAxis("top").setTickFont(font)
        self.ref_plot.view.getAxis("right").setTickFont(font)
        self.ref_plot.view.getAxis("bottom").setLabel('', units='', **labelStyle)
        self.ref_plot.view.getAxis("left").setLabel('', units='', **labelStyle)
        self.scanNum = 0
        #self.liveplot1d.setLabel('left','Intensity (counts)',**style1)
        #self.liveplot1d.setLabel('bottom','X (μm)',**style1)
        #self.ref_plot1d.setLabel('left','Intensity (counts)',**style1)
        #self.ref_plot1d.setLabel('bottom','X (μm)',**style1)
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
        self.select_scan_area.setCheckable(True)
        self.select_scan_area.clicked.connect(self.hideroiplot)
        #self.actionSave.triggered.connect(self.save_imagefile)
        self.actionGalvanometer.triggered.connect(self.setgalvano)
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
        self.scan_mode.setEnabled(False)  # currently disable selecting scan mode
        self.sample_name.setText(self.filename)
        self.sample_name.textChanged.connect(self.updatefile)
        self.toolButton_xhome.clicked.connect(self.gohome_xstage)
        self.toolButton_yhome.clicked.connect(self.gohome_ystage)
        self.toolButton_zhome.clicked.connect(self.gohome_zstage)
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
        self.Stage.set_xspeed(F=int(self.ds102dialog.xspeed))
        self.Stage.set_yspeed(F=int(self.ds102dialog.yspeed))
        self.Stage.set_zspeed(F=int(self.ds102dialog.zspeed))
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
    
    def gohome_xstage(self):
        self.stageX.setValue(self.ds102dialog.xhome)
    
    def gohome_ystage(self):
        self.stageY.setValue(self.ds102dialog.yhome)
    
    def gohome_zstage(self):
        self.stageZ.setValue(self.ds102dialog.zhome)
        
    def updateXstage(self):
        self.Stage.x = self.stageX.value()
    
    def updateYstage(self):
        self.Stage.y = self.stageY.value()
        
    def updateZstage(self):
        self.Stage.z = self.stageZ.value()
        
    def updatefile(self):
        self.filename = self.sample_name.text().split('_')[0]
                
    def chkselbutton(self):
        if self.select_scan_area.isChecked():
            self.select_scan_area.setChecked(False)
            self.ref_plot.roi.rotateAllowed = True
            self.ref_plot.roi.addRotateHandle([0, 0], [0.5, 0.5])
            
    def promptSave_imagefiles(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        self.filename, _ = QtWidgets.QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()","","All Files (*);;Parameter Files (*.txt)", options=options)
        if self.filename:
            curpth = os.getcwd()
            os.chdir(self.pth)
            with open('address.txt','r') as f:
                lines = f.readlines()
            lines[-1] = os.path.dirname(self.filename)
            with open('address.txt','w') as f:
                f.writelines(lines)
            os.chdir(curpth)
            self.save_imagefile()
    
    def printliveplot_MousePos(self,pos):
        position = self.liveplot.view.vb.mapSceneToView(pos)
        mx = position.x()
        my = position.y()
        if mx > self.a0 and my > self.b0 and mx < self.a1 and my < self.b1:
            xi = int((position.x()-self.a0)/self.ascale)
            yi = int((position.y()-self.b0)/self.bscale)
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
        if mx > self.rx0 and my > self.ry0 and mx < self.rx1 and my < self.ry1:
            xi = int((position.x()-self.rx0)/self.rxscale)
            yi = int((position.y()-self.ry0)/self.ryscale)
            s = '   x = ' + str("{:.3f}").format(mx) + '   y = ' + str("{:.3f}").format(my) + '   Intensity = ' + str(self.rimg[xi,yi])
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
            if not self.xactive.isChecked():
                self.ypos.setValue(coords[0][0][0])
                self.zpos.setValue(coords[1][0][0])
                self.ysize.setValue(coords[0][-1][-1]-coords[0][0][0])
                self.zsize.setValue(coords[1][-1][-1]-coords[1][0][0])
                self.xpos.setValue(coords[0][0][0])
                self.zpos.setValue(coords[1][0][0])
                self.xsize.setValue(coords[0][-1][-1]-coords[0][0][0])
                self.zsize.setValue(coords[1][-1][-1]-coords[1][0][0])
            elif not self.zactive.isChecked():
                self.xpos.setValue(coords[0][0][0])
                self.ypos.setValue(coords[1][0][0])
                self.xsize.setValue(coords[0][-1][-1]-coords[0][0][0])
                self.ysize.setValue(coords[1][-1][-1]-coords[1][0][0])
        elif self.nd == 3:
            self.xpos.setValue(coords[0][0][0])
            self.ypos.setValue(coords[1][0][0])
            self.xsize.setValue(coords[0][-1][-1]-coords[0][0][0])
            self.ysize.setValue(coords[1][-1][-1]-coords[1][0][0])
                
    def hideroiplot(self):
        if self.select_scan_area.isChecked():
            if self.ref_plot.ui.roiBtn.isChecked():
                self.ref_plot.ui.roiBtn.setChecked(False)
            self.ref_plot.roi.show()
            self.ref_plot.ui.roiPlot.setMouseEnabled(True, True)
            self.ref_plot.roiChanged()
            self.ref_plot.roi.rotateAllowed = False
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
        if steps.value() == 0:
            if self.scan_type.currentIndex() == 0:
                steps.setValue(0.0001)
            else:
                steps.setValue(1)
        points.setValue(int(size.value()/steps.value()+1))
    
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
        self.points_to_steps(self.xsize,self.xstep,self.xpoints)
        self.points_to_steps(self.ysize,self.ystep,self.ypoints)
        self.points_to_steps(self.zsize,self.zstep,self.zpoints)
        self.nd = 0
        if self.xactive.isChecked():
            self.nd = self.nd + 1
        if self.yactive.isChecked():
            self.nd = self.nd + 1
        if self.zactive.isChecked():
            self.nd = self.nd + 1
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
            if not self.xactive.isChecked():
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
            elif not self.yactive.isChecked():
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
            elif not self.zactive.isChecked():
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
        elif self.nd == 3:
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
            
        elif self.nd == 0:
            inst = QtWidgets.QDialog(self)
            inst.resize(400, 60)
            hl = QtWidgets.QHBoxLayout(inst)
            inst.setWindowTitle("No axis selected")
            l = QtWidgets.QLabel(inst)
            l.setText("Please select atleast 1 axis to scan")
            hl.addWidget(l)
            inst.exec_()
            #self.ref_plot1d.getPlotItem().setLabels(**labels)
        print('Scan Type: {0}'.format(Select.scanName(self.scanNum)))
        
    def setgalvano(self):
        if self.galvanodialog.exec_():
            self.initGalvano()
    
    def initGalvano(self):
        self.Gal.x = self.galvanodialog.xpos
        self.Gal.y = self.galvanodialog.ypos
        self.Gal.xscale = self.galvanodialog.xscale
        self.Gal.yscale = self.galvanodialog.yscale
        self.Gal.xhome = self.galvanodialog.xpos
        self.Gal.yhome = self.galvanodialog.ypos
        if self.scan_type.currentIndex() == 0:
            self.xpos.setMaximum(self.galvanodialog.xmax)
            self.ypos.setMaximum(self.galvanodialog.ymax)
            self.xpos.setMinimum(self.galvanodialog.xmin)
            self.ypos.setMinimum(self.galvanodialog.ymin)
            self.update_sizelimits()

    def update_sizelimits(self):
        self.zsize.setMaximum(self.ds102dialog.zmax-self.zpos.value())
        if self.scan_type.currentIndex() == 1:
            self.xsize.setMaximum(self.ds102dialog.xmax-self.xpos.value())
            self.ysize.setMaximum(self.ds102dialog.ymax-self.ypos.value())
        else:
            self.xsize.setMaximum(self.galvanodialog.xmax-self.xpos.value())
            self.ysize.setMaximum(self.galvanodialog.ymax-self.ypos.value())
            
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
        self.Stage.set_zspeed(F=int(self.ds102dialog.zspeed))
        if self.scan_type.currentIndex() == 1:
            self.xpos.setMaximum(self.ds102dialog.xmax)
            self.xpos.setMinimum(self.ds102dialog.xmin)
            self.ypos.setMaximum(self.ds102dialog.ymax)
            self.ypos.setMinimum(self.ds102dialog.ymin)
            self.update_sizelimits()
            
    def initialize_plot(self):
        self.rx0,self.rx1 = (0,self.ds102dialog.xmax)
        self.ry0,self.ry1 = (0,self.ds102dialog.ymax)
        self.rimg = -ones((400,400))
        for i in range(10):
            self.rimg[20+i,30:100] = 10
        self.rxscale, self.ryscale = (self.rx1-self.rx0)/self.rimg.shape[0],(self.ry1-self.ry0)/self.rimg.shape[1]
        self.ref_plot.setImage(self.rimg,pos=[self.rx0,self.ry0],scale=[self.rxscale,self.ryscale])

        if self.nd > 1:
            self.liveplot.setImage(self.image,pos=[self.a0,self.b0],scale=[self.ascale,self.bscale])
            #self.ref_plot.setImage(self.img,pos=[self.a0,self.y0],scale=[self.xscale,self.yscale])
        elif self.nd == 1:
            pass # implement to plot a 2d graph instead of image
        elif self.nd == 0:
            pass # prompt dialogue to say that no axis is selected for scanning
                 
      
    def display_stagemove_msg(self):
        info = QMessageBox(self)
        info.setWindowTitle("Stage in Motion..")
        info.setIcon(QMessageBox.Information)
        info.setText("Stage is moving, Please wait...")
        info.setStandardButtons(QMessageBox.NoButton)
        stageStatus = MonitorStage(self.Stage)
        stageStatus.start()
        stageStatus.finished.connect(info.hide)
        info.exec()
    
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
        self.initialize()
        self.stop_button.setEnabled(True)
        self.start_button.setEnabled(False)
        self.scan_type.setEnabled(False)
        self.stopcall = False
        self.get_savefilename()
        self.scanParams = [self.nd,
                           self.scanNum, 
                           self.xpos.value(), 
                           self.ypos.value(), 
                           self.zpos.value(), 
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
                           self.scanKind
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
        self.thread.finished.connect(self.finishAction)
        self.thread.start()
        
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
        
    def plotLine(self,imageData):
        self.image = array(imageData[self.plotNumber])
        self.image = self.image.round(decimals = 6)
        self.data_line.setData(imageData[0],self.image)
        
    def plotImage(self,imageData):
        self.image = imageData[self.plotNumber]
        self.image = self.image.round(decimals = 6)
        self.liveplot.setImage(self.image,pos=[0,0],scale=[self.ascale,self.bscale])
    
    def plot3DImage(self,imageData):
        self.image = imageData[self.plotNumber]
        self.image = self.image.round(decimals = 6)
        self.liveplot.setImage(self.image,pos=[0,0],scale=[self.ascale,self.bscale],xvals = self.zarr)
    
    def finishAction(self):
        # set stage speed to original
        # be ready for next scan
        self.start_button.setEnabled(True)
        self.scan_type.setEnabled(True)
        self.stop_button.setEnabled(False)
        
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
            self.xstep.setMaximum(10)
            self.xstep.setDecimals(0)
            self.xstep.setSingleStep(1)
            self.ystep.setMinimum(1)
            self.ystep.setMaximum(10)
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
            self.xstep.setMaximum(1)
            self.xstep.setDecimals(4)
            self.xstep.setSingleStep(0.01)
            self.ystep.setMinimum(0.0001)
            self.ystep.setMaximum(1)
            self.ystep.setDecimals(4)
            self.ystep.setSingleStep(0.01)
            self.xsize.setMaximum(self.galvanodialog.xmax)
            self.xsize.setDecimals(4)
            self.xsize.setSingleStep(0.1)
            self.ysize.setMaximum(self.galvanodialog.ymax)
            self.ysize.setDecimals(4)
            self.ysize.setSingleStep(0.1)
            
    def stop_program(self):
        self.worker.stopcall.emit()
        self.stopcall = True
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
      


        
        
    
