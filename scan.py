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
-> the scanning functions which are active is hardware timed.
   Software timed scanning functions are in the end comment section. It is 
   not implimented as it does not yield exact timing
-> Take care of proper handling of the tasks during abrupt closing
-> Check partial buffering -> register every n samples, and display it in the screen
https://stackoverflow.com/questions/56366033/continuous-acquistion-with-nidaqmx
https://stackoverflow.com/questions/60947373/continuous-analog-read-from-national-instruments-daq-with-nidaqmx-python-package

-> Check if period counting is necessary, if the counter cannot handle total counts of whole scan
-> How to count for a specific time period exactly
    
-> when initialize is clicked,
    make sure the scan order is consistent, if not, autocorrect it

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
"""

from galvanometer import Scan
from numpy import linspace, ones, ndarray, savetxt, column_stack, shape
import os, sys
from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
from scanner_gui import Ui_Scanner
from galvanometer_settings import galsetting
from ds102_settings import ds102setting
from pymeasure.experiment import unique_filename
from ds102 import DS102
from PyQt5.QtCore import QEventLoop, QTimer
from time import sleep
from utilities import checkInstrument

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
        pth = os.getcwd()
        self.galvanodialog = galsetting()
        os.chdir(pth)
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
        self.scan_method_change()
        self.xactive.stateChanged.connect(self.x_state_change)
        self.yactive.stateChanged.connect(self.y_state_change)
        self.zactive.stateChanged.connect(self.z_state_change)
        self.scan_method.currentIndexChanged.connect(self.scan_method_change)
        self.scan_type.currentIndexChanged.connect(self.scan_type_change)
        self.scan_method.setEnabled(False)
        self.start_button.clicked.connect(self.run_program)
        self.stop_button.clicked.connect(self.stop_program)
        self.verify_button.clicked.connect(self.initialize)
        self.select_scan_area.setCheckable(True)
        self.select_scan_area.clicked.connect(self.hideroiplot)
        self.actionSave.triggered.connect(self.save_imagefile)
        self.actionSave_as.triggered.connect(self.promptSave_imagefiles)
        self.actionGalvanometer.triggered.connect(self.setgalvano)
        self.actionSteppermotor.triggered.connect(self.setstage)
        self.xstep.editingFinished.connect(lambda: self.steps_to_points(self.xsize,self.xstep,self.xpoints))
        self.ystep.editingFinished.connect(lambda: self.steps_to_points(self.ysize,self.ystep,self.ypoints))
        self.zstep.editingFinished.connect(lambda: self.steps_to_points(self.zsize,self.zstep,self.zpoints))
        self.xsize.valueChanged.connect(lambda: self.steps_to_points(self.xsize,self.xstep,self.xpoints))
        self.ysize.valueChanged.connect(lambda: self.steps_to_points(self.ysize,self.ystep,self.ypoints))
        self.zsize.valueChanged.connect(lambda: self.steps_to_points(self.zsize,self.zstep,self.zpoints))
        self.srate_set.valueChanged.connect(lambda: self.rate_to_tstep(self.srate_set,self.tperstep_set))
        self.xpos.valueChanged.connect(self.update_sizelimits)
        self.ypos.valueChanged.connect(self.update_sizelimits)
        self.zpos.valueChanged.connect(self.update_sizelimits)
        self.tperstep_set.valueChanged.connect(lambda: self.tstep_to_rate(self.srate_set,self.tperstep_set))
        self.xpos.valueChanged.connect(self.restrict_start_before_initialize)
        self.ypos.valueChanged.connect(self.restrict_start_before_initialize)
        self.zpos.valueChanged.connect(self.restrict_start_before_initialize)
        self.xsize.valueChanged.connect(self.restrict_start_before_initialize)
        self.ysize.valueChanged.connect(self.restrict_start_before_initialize)
        self.zsize.valueChanged.connect(self.restrict_start_before_initialize)
        self.xpoints.valueChanged.connect(self.restrict_start_before_initialize)
        self.ypoints.valueChanged.connect(self.restrict_start_before_initialize)
        self.zpoints.valueChanged.connect(self.restrict_start_before_initialize)
        self.xscanorder.currentIndexChanged.connect(self.restrict_start_before_initialize)
        self.yscanorder.currentIndexChanged.connect(self.restrict_start_before_initialize)
        self.zscanorder.currentIndexChanged.connect(self.restrict_start_before_initialize)
        self.tperstep_set.valueChanged.connect(self.restrict_start_before_initialize)
        self.xactive.stateChanged.connect(self.restrict_start_before_initialize)
        self.yactive.stateChanged.connect(self.restrict_start_before_initialize)
        self.zactive.stateChanged.connect(self.restrict_start_before_initialize)
        self.scan_type.currentIndexChanged.connect(self.restrict_start_before_initialize)
        self.scan_method.currentIndexChanged.connect(self.restrict_start_before_initialize)
        self.setdefaults()
        if self.scan_type.currentIndex() == 0:
            self.xsize.setMaximum(self.galvanodialog.xmax-self.galvanodialog.xmin)
            self.ysize.setMaximum(self.galvanodialog.ymax-self.galvanodialog.ymin)
        self.initialize()
        self.initialize_plot()
        self.restrict_start_before_initialize()
        self.ref_plot.roi.sigRegionChanged.connect(self.getroidata)
        self.ref_plot.ui.roiBtn.clicked.connect(self.chkselbutton)
        self.liveplot.view.scene().sigMouseMoved.connect(self.printliveplot_MousePos)
        self.ref_plot.view.scene().sigMouseMoved.connect(self.printrefplot_MousePos)
        self.scan_mode.setEnabled(False)  # currently disable selecting scan mode
        self.sample_name.setText(self.filename)
        self.sample_name.textChanged.connect(self.updatefile)
        self.actionSave.setShortcut('Ctrl+S')
        self.actionSave.setStatusTip('Save the current image to file')
        self.Gal, self.Stage = checkInstrument(ds102Port = self.ds102dialog.com)
        self.initGalvano()
        self.initStage()
        self.display_stagemove_msg()
        self.toolButton_xhome.clicked.connect(self.gohome_xstage)
        self.toolButton_yhome.clicked.connect(self.gohome_ystage)
        self.toolButton_zhome.clicked.connect(self.gohome_zstage)
        self.spinBox_xmove.setMaximum(self.ds102dialog.xmax)
        self.spinBox_xmove.setMinimum(self.ds102dialog.xmin)
        self.spinBox_xmove.setValue(self.Stage.x)
        self.spinBox_xmove.valueChanged.connect(self.updateXstage)
        self.spinBox_xmove.setKeyboardTracking(False)
        self.spinBox_ymove.setMaximum(self.ds102dialog.ymax)
        self.spinBox_ymove.setMinimum(self.ds102dialog.ymin)
        self.spinBox_ymove.setValue(self.Stage.y)
        self.spinBox_ymove.setKeyboardTracking(False)
        self.spinBox_ymove.valueChanged.connect(self.updateYstage)
        self.spinBox_zmove.setMaximum(self.ds102dialog.zmax)
        self.spinBox_zmove.setMinimum(self.ds102dialog.zmin)
        self.spinBox_zmove.setValue(self.Stage.z)
        self.spinBox_zmove.setKeyboardTracking(False)
        self.spinBox_zmove.valueChanged.connect(self.updateZstage)
        self.xscanorder.setEnabled(False) # currently scan order is not changable
        self.yscanorder.setEnabled(False)
        self.zscanorder.setEnabled(False)
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
        self.stopcall = True
        self.xsize.setValue(500)
        self.ysize.setValue(500)
        self.zsize.setValue(500)
        self.xpoints.setValue(101)
        self.ypoints.setValue(101)
        self.zpoints.setValue(101)
        self.tperstep_set.setValue(0.01)
    
    def gohome_xstage(self):
        self.spinBox_xmove.setValue(self.ds102dialog.xhome)
    
    def gohome_ystage(self):
        self.spinBox_ymove.setValue(self.ds102dialog.yhome)
    
    def gohome_zstage(self):
        self.spinBox_zmove.setValue(self.ds102dialog.zhome)
        
    def updateXstage(self):
        self.Stage.x = self.spinBox_xmove.value()
    
    def updateYstage(self):
        self.Stage.y = self.spinBox_ymove.value()
        
    def updateZstage(self):
        self.Stage.z = self.spinBox_zmove.value()
        
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
            self.save_imagefile()
    
    def save_imagefile(self):
        if self.filename.find('.') != -1:
            index = self.filename.rindex('.')  # rindex returns the last location of '.'
            self.filename = self.filename[:index]
        self.filename_shg = unique_filename(directory='.',prefix=self.filename+'_shg',datetimeformat="",ext='txt')
        self.filename_ref = unique_filename(directory='.',prefix=self.filename+'_ref',datetimeformat="",ext='txt')
        self.filename_processed = unique_filename(directory='.',prefix=self.filename+'_processed',datetimeformat="",ext='txt')
        self.filenamedisp = self.filename_shg.split('\\')[-1].split('_')[0]
        self.filenamedisp = self.filenamedisp.split('/')[-1].split('.')[0]
        if self.scanNum in {4,8,12}:
            whole_data = column_stack((self.Stage.Oneddata,self.Stage.count_data))
            savetxt(self.filename_shg,whole_data,fmt='%g',delimiter='\t')
        elif self.scanNum == 40:
            with open(self.filename_shg,'ab') as f:
                for i in range(self.imgSHG.shape[0]):
                    a=self.imgSHG[i,:,:]
                    savetxt(f,a.T,fmt='%g',delimiter='\t')
                    f.write(b'\n\n')
            with open(self.filename_ref,'ab') as f:
                for i in range(self.imgRef.shape[0]):
                    a=self.imgRef[i,:,:]
                    savetxt(f,a.T,fmt='%g',delimiter='\t')
                    f.write(b'\n\n')
            with open(self.filename_processed,'ab') as f:
                for i in range(self.imgProcessed.shape[0]):
                    a=self.imgProcessed[i,:,:]
                    savetxt(f,a.T,fmt='%g',delimiter='\t')
                    f.write(b'\n\n')
        else:
            savetxt(self.filename_shg, self.imgSHG.T, fmt='%g',delimiter='\t')
            savetxt(self.filename_ref, self.imgRef.T, fmt='%g',delimiter='\t')
            savetxt(self.filename_processed, self.imgProcessed.T, fmt='%g',delimiter='\t')
        self.sample_name.setText(self.filenamedisp)
        
    def printliveplot_MousePos(self,pos):
        position = self.liveplot.view.vb.mapSceneToView(pos)
        mx = position.x()
        my = position.y()
        if mx > self.a0 and my > self.b0 and mx < self.a1 and my < self.b1:
            xi = int((position.x()-self.a0)/self.ascale)
            yi = int((position.y()-self.b0)/self.bscale)
            if len(shape(self.img)) == 2:
                s = '   x = ' + str("{:.3f}").format(mx) + '   y = ' + str("{:.3f}").format(my) + '   Intensity = ' + str(self.img[xi,yi])
            elif len(shape(self.img)) == 3:
                intensity = self.img[self.liveplot.currentIndex,xi,yi]
                s = 'x: ' + str("{:.3f}").format(mx) + '   y: ' + str("{:.3f}").format(my) + \
                    '   z: ' + str("{:.3f}").format(self.Stage.zarr[self.liveplot.currentIndex]) + \
                    '   Intensity = ' + str(intensity)
            self.lineEdit.setText(s)
        else:
            self.lineEdit.setText("")
    
    def printrefplot_MousePos(self,pos):
        position = self.ref_plot.view.vb.mapSceneToView(pos)
        mx = position.x()
        my = position.y()
        if mx > self.rx0 and my > self.ry0 and mx < self.rx1 and my < self.ry1:
            xi = int((position.x()-self.rx0)/self.rxscale)
            yi = int((position.y()-self.ry0)/self.ryscale)
            s = '   x = ' + str("{:.3f}").format(mx) + '   y = ' + str("{:.3f}").format(my) + '   Intensity = ' + str(self.rimg[xi,yi])
            self.lineEdit.setText(s)
        else:
            self.lineEdit.setText("")
        
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
    
    def steps_to_points(self,size,steps,points):
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
        
    def restrict_start_before_initialize(self):
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.verify_button.setEnabled(True)
        #self.scan_method.setEnabled(True)
        self.scan_type.setEnabled(True)
    
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
            self.img = -ones((self.apoints))
        elif self.nd == 2:
            self.apoints,self.bpoints = self.getpoints()
            self.img = -ones((self.apoints,self.bpoints))
        elif self.nd == 3:
            self.cpoints,self.apoints, self.bpoints = self.getpoints()
            self.img = -ones((self.apoints,self.bpoints))
        if self.nd == 1:
            if self.xactive.isChecked():
                self.x0,self.x1 = 0,self.xsize.value()
                self.xscale = (self.x1-self.x0)/self.img.shape[0]
                self.a0, self.a1, self.asize = self.x0, self.x1, self.xsize.value()
                if self.scan_type.currentIndex() == 0:
                    if self.scan_method.currentIndex() == 0:
                        self.scanNum = 1
                    else:
                        self.scanNum = 2
                else:
                    if self.scan_method.currentIndex() == 0:
                        self.scanNum = 3
                    else:
                        self.scanNum = 4
                labels={'bottom': ("X",'μm'), 'left':("Intensity",'counts'),'top':"",'right':""}
            elif self.yactive.isChecked():
                self.y0,self.y1 = 0,self.ysize.value()
                self.yscale = (self.y1-self.y0)/self.img.shape[0]
                self.a0, self.a1, self.asize = self.y0, self.y1, self.ysize.value()
                if self.scan_type.currentIndex() == 0:
                    if self.scan_method.currentIndex() == 0:
                        self.scanNum = 5
                    else:
                        self.scanNum = 6
                else:
                    if self.scan_method.currentIndex() == 0:
                        self.scanNum = 7
                    else:
                        self.scanNum = 8
                labels={'bottom': ("Y",'μm'), 'left':("Intensity",'counts'),'top':"",'right':""}
            elif self.zactive.isChecked():
                self.z0,self.z1 = 0,self.zsize.value()
                self.a0, self.a1, self.asize = self.z0, self.z1, self.zsize.value()
                self.zscale = (self.z1-self.z0)/self.img.shape[0]
                labels={'bottom': ("Z",'μm'), 'left':("Intensity",'counts'),'top':"",'right':""}
                if self.scan_type.currentIndex() == 0:
                    self.scan_type.setCurrentIndex(1)
                if self.scan_method.currentIndex() == 0:
                    self.scanNum = 11
                else:
                    self.scanNum = 12
        elif self.nd == 2:
            if not self.xactive.isChecked():
                self.y0,self.y1 = 0,self.ysize.value()
                self.z0,self.z1 = 0,+self.zsize.value()
                self.yscale, self.zscale = (self.y1-self.y0)/self.img.shape[0],(self.z1-self.z0)/self.img.shape[1]
                self.a0, self.a1, self.asize = self.y0, self.y1, self.ysize.value()
                self.b0, self.b1, self.bsize = self.z0, self.z1, self.zsize.value()
                self.ascale, self.bscale = self.yscale, self.zscale
                self.scan_type.setCurrentIndex(1) # you can improve it later
                if self.scan_type.currentIndex() == 0:
                    if self.scan_method.currentIndex() == 0:
                        if self.yscanorder.currentIndex() == 0:
                            self.scanNum = 13
                        else:
                            self.scanNum = 17
                    else:
                        if self.yscanorder.currentIndex() == 0:
                            self.scanNum = 14
                        else:
                            self.scanNum = 18
                else:
                    if self.scan_method.currentIndex() == 0:
                        if self.yscanorder.currentIndex() == 0:
                            self.scanNum = 15
                        else:
                            self.scanNum = 19
                    else:
                        if self.yscanorder.currentIndex() == 0:
                            self.scanNum = 16
                        else:
                            self.scanNum = 20
                labels={'bottom': ("Y",'μm'), 'left':("Z",'μm'),'top':"",'right':""}
            elif not self.yactive.isChecked():
                self.x0,self.x1 = 0,self.xsize.value()
                self.z0,self.z1 = 0,self.zsize.value()
                self.xscale, self.zscale = (self.x1-self.x0)/self.img.shape[0],(self.z1-self.z0)/self.img.shape[1]
                self.a0, self.a1, self.asize = self.x0, self.x1, self.xsize.value()
                self.b0, self.b1, self.bsize = self.z0, self.z1, self.zsize.value()
                self.ascale, self.bscale = self.xscale, self.zscale
                self.scan_type.setCurrentIndex(1)
                if self.scan_type.currentIndex() == 0:
                    if self.scan_method.currentIndex() == 0:
                        if self.xscanorder.currentIndex() == 0:
                            self.scanNum = 21
                        else:
                            self.scanNum = 25
                    else:
                        if self.xscanorder.currentIndex() == 0:
                            self.scanNum = 22
                        else:
                            self.scanNum = 26
                else:
                    if self.scan_method.currentIndex() == 0:
                        if self.xscanorder.currentIndex() == 0:
                            self.scanNum = 23
                        else:
                            self.scanNum = 27
                    else:
                        if self.xscanorder.currentIndex() == 0:
                            self.scanNum = 24
                        else:
                            self.scanNum = 28
                labels={'bottom': ("X",'μm'), 'left':("Z",'μm'),'top':"",'right':""}
            elif not self.zactive.isChecked():
                self.x0,self.x1 = 0,self.xsize.value()
                self.y0,self.y1 = 0,self.ysize.value()
                self.xscale, self.yscale = (self.x1-self.x0)/self.img.shape[0],(self.y1-self.y0)/self.img.shape[1]
                self.a0, self.a1, self.asize = self.x0, self.x1, self.xsize.value()
                self.b0, self.b1, self.bsize = self.y0, self.y1, self.ysize.value()
                self.ascale, self.bscale = self.xscale, self.yscale
                if self.scan_type.currentIndex() == 0:
                    if self.scan_method.currentIndex() == 0:
                        if self.xscanorder.currentIndex() == 0:
                            self.scanNum = 29
                        else:
                            self.scanNum = 33
                    else:
                        if self.xscanorder.currentIndex() == 0:
                            self.scanNum = 30
                        else:
                            self.scanNum = 34
                else:
                    if self.scan_method.currentIndex() == 0:
                        if self.xscanorder.currentIndex() == 0:
                            self.scanNum = 31
                        else:
                            self.scanNum = 35
                    else:
                        if self.xscanorder.currentIndex() == 0:
                            self.scanNum = 32
                        else:
                            self.scanNum = 36
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
                if self.scan_method.currentIndex() == 0:
                    if self.xscanorder.currentIndex() == 0:
                        self.scanNum = 37
                    else:
                        self.scanNum = 41
                else:
                    if self.xscanorder.currentIndex() == 0:
                        self.scanNum = 38
                    else:
                        self.scanNum = 42
            else:
                if self.scan_method.currentIndex() == 0:
                    if self.xscanorder.currentIndex() == 0:
                        self.scanNum = 39
                    else:
                        self.scanNum = 43
                else:
                    if self.xscanorder.currentIndex() == 0:
                        self.scanNum = 40
                    else:
                        self.scanNum = 44
            labels={'bottom': ("X",'μm'), 'left':("Y",'μm'),'top':"",'right':""}
        if self.nd >1:
            if not self.liveplot.isVisible():
                self.liveplot.show()
                #self.ref_plot.show()
                self.liveplot1d.hide()
                #self.ref_plot1d.hide()
            self.liveplot.view.setLabels(**labels)
            self.liveplot.setImage(self.img,pos=[self.a0,self.b0],scale=[self.ascale,self.bscale])
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
            self.restrict_start_before_initialize()
            #self.ref_plot1d.getPlotItem().setLabels(**labels)
        print('Scan Type: {0}'.format(self.scanNum))
        self.start_button.setEnabled(True)
        self.verify_button.setEnabled(False)
        
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
        self.spinBox_xmove.setMaximum(self.ds102dialog.xmax)
        self.spinBox_xmove.setMinimum(self.ds102dialog.xmin)
        self.spinBox_ymove.setMaximum(self.ds102dialog.ymax)
        self.spinBox_ymove.setMinimum(self.ds102dialog.ymin)
        self.spinBox_zmove.setMaximum(self.ds102dialog.zmax)
        self.spinBox_zmove.setMinimum(self.ds102dialog.zmin)
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
            self.liveplot.setImage(self.img,pos=[self.a0,self.b0],scale=[self.ascale,self.bscale])
            #self.ref_plot.setImage(self.img,pos=[self.a0,self.y0],scale=[self.xscale,self.yscale])
        elif self.nd == 1:
            pass # implement to plot a 2d graph instead of image
        elif self.nd == 0:
            pass # prompt dialogue to say that no axis is selected for scanning
                 
      
    def display_stagemove_msg(self):
        loop = QEventLoop()
        wait_msg = "Stage is moving to starting position. Please wait..."
        info = QtGui.QMessageBox()
        if self.Stage.is_xmoving() or self.Stage.is_ymoving() or self.Stage.is_zmoving():
            info.setText(wait_msg)   # check why it is not displaying this message
            info.setStandardButtons(QtGui.QMessageBox.NoButton)
            info.setWindowTitle("Moving Stage. Please wait...")
            info.show()
        while self.Stage.is_xmoving() or self.Stage.is_ymoving() or self.Stage.is_zmoving():
            QTimer.singleShot(100, loop.quit)
        info.close()
         
    def check_ref_ON(self):
        loop = QEventLoop()
        self.Gal.reference.start()
        QTimer.singleShot(100, loop.quit)
        ref = self.Gal.reference.read() * 1000000
        self.Gal.reference.stop()
        if  ref < 1000:
            prompt = "Reference signal is not turned on. Continue without reference?"
            reply = QtGui.QMessageBox.question(self, 'Message', 
                     prompt, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
            if reply == QtGui.QMessageBox.Yes:
                return 1
            else:
                return 0
        return 1
    
    def run_program(self):
        self.pause_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.start_button.setEnabled(False)
        self.scan_type.setEnabled(False)
        self.stopcall = False
        if self.nd == 1:
            if self.scanNum == 4: # 1D x scan
                sleep(0.1)
                self.spinBox_xmove.setValue(int(self.xpos.value()))
                self.Stage.set_xspeed(F=int(self.ds102dialog.xscanspeed))                
                self.display_stagemove_msg()
                self.arr_a = linspace(self.xpos.value(),self.xpos.value()+self.xsize.value(),self.apoints,dtype=int)
                self.stage_stepscanx(self.arr_a)
            elif self.scanNum == 8: # 1D Y Scan
                sleep(0.1)
                self.spinBox_ymove.setValue(int(self.ypos.value()))
                self.Stage.set_yspeed(F=int(self.ds102dialog.yscanspeed))                
                self.display_stagemove_msg()
                self.arr_b = linspace(self.ypos.value(),self.ypos.value()+self.ysize.value(),self.apoints,dtype=int)
                self.stage_stepscany(self.arr_b)
            elif self.scanNum == 12:  # 1D Z Scan
                sleep(0.1)
                self.spinBox_zmove.setValue(int(self.zpos.value()))
                self.Stage.set_zspeed(F=int(self.ds102dialog.zscanspeed))                
                self.display_stagemove_msg()
                self.arr_c = linspace(self.zpos.value(),self.zpos.value()+self.zsize.value(),self.apoints,dtype=int)
                self.stage_stepscanz(self.arr_c)
        elif self.nd == 2:
            if not self.check_ref_ON():
                self.stopcall = True
                self.start_button.setEnabled(True)
                self.scan_type.setEnabled(True)
                self.stop_button.setEnabled(False)
                self.pause_button.setEnabled(False)
                return
            if self.scanNum == 20:
                self.spinBox_ymove.setValue(int(self.ypos.value()))
                self.spinBox_zmove.setValue(int(self.zpos.value()))
                self.Stage.set_yspeed(F=int(self.ds102dialog.yscanspeed))
                sleep(0.1)
                self.Stage.set_zspeed(F=int(self.ds102dialog.zscanspeed))
                self.display_stagemove_msg()
                self.arr_a = linspace(self.ypos.value(),self.ypos.value()+self.ysize.value(),self.apoints,dtype=int)
                self.arr_b = linspace(self.zpos.value(),self.zpos.value()+self.zsize.value(),self.bpoints,dtype=int)
                self.stage_stepscanyz(self.arr_a,self.arr_b)
            elif self.scanNum == 24:
                self.spinBox_xmove.setValue(int(self.xpos.value()))
                self.spinBox_zmove.setValue(int(self.zpos.value()))
                self.Stage.set_xspeed(F=int(self.ds102dialog.xscanspeed))
                sleep(0.1)
                self.Stage.set_zspeed(F=int(self.ds102dialog.zscanspeed))
                self.display_stagemove_msg()
                self.arr_a = linspace(self.xpos.value(),self.xpos.value()+self.xsize.value(),self.apoints,dtype=int)
                self.arr_b = linspace(self.zpos.value(),self.zpos.value()+self.zsize.value(),self.bpoints,dtype=int)
                self.stage_stepscanxz(self.arr_a,self.arr_b)
            elif self.scanNum == 29:
                self.arr_a = linspace(self.xpos.value(),self.xpos.value()+self.asize,self.apoints)
                self.arr_b = linspace(self.ypos.value(),self.ypos.value()+self.bsize,self.bpoints)
                #self.spinBox_xmove.setValue(int(self.xpos.value()+self.asize/2))
                #self.spinBox_ymove.setValue(int(self.ypos.value()+self.bsize/2))
                #self.display_stagemove_msg()
                #self.Gal.start_scanxy(self.arr_a-self.asize/2,self.arr_b-self.bsize/2)
                self.Gal.x = self.arr_a[0]+self.Gal.xhome
                self.Gal.y = self.arr_b[0]+self.Gal.yhome
                self.Gal.srate = self.srate_set.value()
                self.Gal.start_scanxy(self.arr_a,self.arr_b)
                self.plot_realtime_data29()
            elif self.scanNum == 30:
                self.arr_a = linspace(self.xpos.value(),self.xpos.value()+self.asize,self.apoints)
                self.arr_b = linspace(self.ypos.value(),self.ypos.value()+self.bsize,self.bpoints)
                #self.spinBox_xmove.setValue(int(self.xpos.value()+self.asize/2))
                #self.spinBox_ymove.setValue(int(self.ypos.value()+self.bsize/2))
                #self.display_stagemove_msg()
                #self.gal_stepscanxy(self.arr_a-self.asize/2,self.arr_b-self.bsize/2)
                self.gal_stepscanxy(self.arr_a,self.arr_b)
                #self.img = self.Gal.img_data
                #self.liveplot.setImage(self.img,pos=[self.a0,self.b0],scale=[self.ascale,self.bscale])
            elif self.scanNum == 32:
                self.spinBox_xmove.setValue(int(self.xpos.value()))
                self.spinBox_ymove.setValue(int(self.ypos.value()))
                self.Stage.set_xspeed(F=int(self.ds102dialog.xscanspeed))
                sleep(0.1)
                self.Stage.set_yspeed(F=int(self.ds102dialog.yscanspeed))
                self.display_stagemove_msg()
                self.arr_a = linspace(self.xpos.value(),self.xpos.value()+self.xsize.value(),self.apoints,dtype=int)
                self.arr_b = linspace(self.ypos.value(),self.ypos.value()+self.ysize.value(),self.bpoints,dtype=int)
                self.stage_stepscanxy(self.arr_a,self.arr_b)
        elif self.nd == 3:
            if not self.check_ref_ON():
                self.stopcall = True
                self.start_button.setEnabled(True)
                self.scan_type.setEnabled(True)
                self.stop_button.setEnabled(False)
                self.pause_button.setEnabled(False)
                return
            if self.scanNum == 40:
                self.spinBox_xmove.setValue(int(self.xpos.value()))
                self.spinBox_ymove.setValue(int(self.ypos.value()))
                self.spinBox_zmove.setValue(int(self.zpos.value()))
                self.Stage.set_xspeed(F=int(self.ds102dialog.xscanspeed))
                sleep(0.1)
                self.Stage.set_yspeed(F=int(self.ds102dialog.yscanspeed))
                sleep(0.1)
                self.Stage.set_zspeed(F=int(self.ds102dialog.zscanspeed))
                self.display_stagemove_msg()
                self.arr_a = linspace(self.xpos.value(),self.xpos.value()+self.xsize.value(),self.apoints,dtype=int)
                self.arr_b = linspace(self.ypos.value(),self.ypos.value()+self.ysize.value(),self.bpoints,dtype=int)
                self.arr_c = linspace(self.zpos.value(),self.zpos.value()+self.zsize.value(),self.cpoints,dtype=int)
                self.stage_stepscanxyz(self.arr_a,self.arr_b,self.arr_c)
            elif self.scanNum == 37:
                self.spinBox_zmove.setValue(int(self.zpos.value()))
                sleep(0.1)
                self.Stage.set_zspeed(F=int(self.ds102dialog.zscanspeed))
                self.display_stagemove_msg()
                self.arr_a = linspace(self.xpos.value(),self.xpos.value()+self.xsize.value(),self.apoints,dtype=float)
                self.arr_b = linspace(self.ypos.value(),self.ypos.value()+self.ysize.value(),self.bpoints,dtype=float)
                self.arr_c = linspace(self.zpos.value(),self.zpos.value()+self.zsize.value(),self.cpoints,dtype=int)
                self.galscan37()
        
    def plot_realtime_data29(self):
        self.timer = QtCore.QTimer()
        self.timecount = QtCore.QElapsedTimer()
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.update_data29)
        self.timer.start()
        self.timecount.start()
        #self.liveplot.setImage(self.img,pos=[self.x0,self.y0],scale=[self.xscale,self.yscale])
        
    def update_data29(self):
        # update the plot data, and anything you want to change on screen
        if self.Gal.update_scanxy():
            self.imgProcessed = self.Gal.img_Processed
        else:
            self.imgProcessed = self.Gal.img_Processed
            self.imgSHG = self.Gal.img_dataSHG
            self.imgRef = self.Gal.img_dataRef
            self.stop_program()
            self.Gal.create_ctr()
            self.Gal.create_ref()
            self.Gal.taskxy.close()
            self.Gal.create_taskxy()
            print("moved mirror to home position")
            self.Gal.x = self.galvanodialog.xpos
            self.Gal.y = self.galvanodialog.ypos            
            #self.spinBox_xmove.setValue(int(self.xpos.value()))
            #self.spinBox_ymove.setValue(int(self.ypos.value()))
        self.liveplot.setImage(self.imgProcessed,pos=[self.a0,self.b0],scale=[self.ascale,self.bscale])
    
    def galscan37(self):
        self.Stage.zarr = self.arr_c
        self.img3dSHG = -ones((len(self.arr_c),len(self.arr_a),len(self.arr_b)))
        self.img3dRef = -ones((len(self.arr_c),len(self.arr_a),len(self.arr_b)))
        self.img3dProcessed = -ones((len(self.arr_c),len(self.arr_a),len(self.arr_b)))
        self.i = 0
        self.frameFinishedFlag = 0
        self.timer = QtCore.QTimer()
        self.timer.singleShot(0, self.update_data37)
        
    def update_data37Frame(self):
        # update the plot data, and anything you want to change on screen
        if self.Gal.update_scanxy():
            self.imgSHG = self.Gal.img_dataSHG
            self.imgRef = self.Gal.img_dataRef
            self.imgProcessed = self.Gal.img_Processed
        else:
            self.timer1.stop()
            self.Gal.stop_scanxy()
            self.Gal.create_ctr()
            self.Gal.create_ref()
            self.imgSHG = self.Gal.img_dataSHG
            self.imgRef = self.Gal.img_dataRef
            self.imgProcessed = self.Gal.img_Processed
            self.img3dProcessed[self.i,:,:] = self.Gal.img_Processed
            self.img3dSHG[self.i,:,:] = self.Gal.img_dataSHG
            self.img3dRef[self.i,:,:] = self.Gal.img_dataRef
            self.i = self.i+1
            if self.i < len(self.arr_c) and self.stopcall == False:
                self.timer.singleShot(0,self.update_data37)
            else:
                self.stop_program()
                print("moved mirror to home position")
                self.Gal.x = self.galvanodialog.xpos
                self.Gal.y = self.galvanodialog.ypos
                self.imgProcessed = self.img3dProcessed
                self.imgSHG = self.img3dSHG
                self.imgRef = self.img3dRef
                self.liveplot.setImage(self.imgProcessed,pos=[self.a0,self.b0],scale=[self.ascale,self.bscale],xvals=self.arr_c)
                return
        self.liveplot.setImage(self.imgProcessed,pos=[self.a0,self.b0],scale=[self.ascale,self.bscale])
        
    def update_data37(self):
        self.spinBox_zmove.setValue(int(self.arr_c[self.i]))
        self.display_stagemove_msg()
        self.Gal.x = self.arr_a[0]+self.Gal.xhome
        self.Gal.y = self.arr_b[0]+self.Gal.yhome
        self.Gal.start_scanxy(self.arr_a,self.arr_b)
        self.timer1 = QtCore.QTimer()
        self.timecount = QtCore.QElapsedTimer()
        self.timer1.setInterval(200)
        self.timer1.timeout.connect(self.update_data37Frame)
        self.timer1.start()
        self.timecount.start()
        
    def gal_stepscanxy(self,xarr,yarr):
        self.Gal.xarr = xarr/self.Gal.xscale
        self.Gal.yarr = yarr/self.Gal.yscale
        self.Gal.img_data = -ones((len(xarr),len(yarr)))
        self.Gal.ref_data = -ones((len(xarr),len(yarr)))
        self.Gal.processed_data = -ones((len(xarr),len(yarr)))
        self.j = 0
        self.i = 0
        self.plot_realtime_data30()
        """
        tstep = int(self.tperstep_set.value()*1000) # ms
        loop = QEventLoop()
        for j in range(len(self.Gal.yarr)):
            for i in range(len(self.Gal.xarr)):
                if j%2 == 0:
                    self.Gal.gotoxy(self.Gal.xarr[i],self.Gal.yarr[j])
                else:
                    self.Gal.gotoxy(self.Gal.xarr[-i-1],self.Gal.yarr[j])
                self.Gal.counter.start()
                QTimer.singleShot(tstep, loop.quit)
                self.Gal.counter.stop()
                self.Gal.reference.stop()
                if j%2 == 0:
                    self.Gal.img_data[i,j] = self.Gal.counter.read()    
                else:
                    self.Gal.img_data[-i-1,j] = self.Gal.counter.read()
        """

    def plot_realtime_data30(self):
        self.timer = QtCore.QTimer()
        self.timecount = QtCore.QElapsedTimer()
        tstep = int(self.tperstep_set.value()*1000)
        self.timer.setInterval(tstep)
        self.timer.timeout.connect(self.update_data30)
        self.timer.start()
        self.timecount.start()
        self.Gal.counter.start()
        self.Gal.reference.start()
        #self.liveplot.setImage(self.img,pos=[self.x0,self.y0],scale=[self.xscale,self.yscale])
        
    def update_data30(self):
        # update the plot data, and anything you want to change on screen
        shg = self.Gal.counter.read()
        ref = self.Gal.reference.read()*1000000
        # TODO prompt if reference detector is not switched on
        if ref < 1000:
            ref = 1
        if self.j%2 == 0:
            self.Gal.img_data[self.i,self.j] = shg
            self.Gal.ref_data[self.i,self.j] = ref
            self.Gal.processed_data[self.i,self.j] = shg/ref
            self.Gal.gotoxy(self.Gal.xarr[self.i],self.Gal.yarr[self.j])
        else:
            self.Gal.img_data[-self.i-1,self.j] = shg
            self.Gal.ref_data[-self.i-1,self.j] = ref
            self.Gal.processed_data[-self.i-1,self.j] = shg/ref
            self.Gal.gotoxy(self.Gal.xarr[-self.i-1],self.Gal.yarr[self.j])
        self.Gal.counter.stop()
        self.Gal.reference.stop()
        self.imgProcessed = self.Gal.processed_data
        self.i = self.i + 1
        if self.i > len(self.Gal.xarr)-1:
            self.j = self.j+1
            self.i = 0
        if self.j > len(self.Gal.yarr)-1:
            self.imgSHG = self.Gal.img_data
            self.imgRef = self.Gal.ref_data
            self.stop_program()
            self.liveplot.setImage(self.imgProcessed,pos=[self.a0,self.b0],scale=[self.ascale,self.bscale])
            #self.spinBox_xmove.setValue(int(self.xpos.value()))
            #self.spinBox_ymove.setValue(int(self.ypos.value()))
            return
        self.liveplot.setImage(self.imgProcessed,pos=[self.a0,self.b0],scale=[self.ascale,self.bscale])
        self.Gal.counter.start()
        self.Gal.reference.start()
        
    def stage_stepscanxy(self,xarr,yarr):
        self.Stage.img_data = -ones((len(xarr),len(yarr)))
        self.Stage.ref_data = -ones((len(xarr),len(yarr)))
        self.Stage.processed_data = -ones((len(xarr),len(yarr)))
        self.Stage.xarr = xarr
        self.Stage.yarr = yarr
        self.i = 0
        self.j = 0
        self.timer = QtCore.QTimer()
        self.tstep = int(self.tperstep_set.value()*1000)
        self.Gal.counter.start()
        self.Gal.reference.start()
        self.timer.singleShot(self.tstep, QtCore.Qt.PreciseTimer, self.update_data32)        
        #self.liveplot.setImage(self.img,pos=[self.x0,self.y0],scale=[self.xscale,self.yscale])
        
    def update_data32(self):
        # update the plot data, and anything you want to change on screen
        shg = self.Gal.counter.read()
        ref = self.Gal.reference.read()*1000000
        if ref < 1000:
            ref = 1
        if self.j%2 == 0:
            self.Stage.img_data[self.i,self.j] = shg
            self.Stage.ref_data[self.i,self.j] = ref
            self.Stage.processed_data[self.i,self.j] = shg/ref
            self.Stage.goto_xy(self.Stage.xarr[self.i],self.Stage.yarr[self.j])
        else:
            self.Stage.img_data[-self.i-1,self.j] = shg
            self.Stage.ref_data[-self.i-1,self.j] = ref
            self.Stage.processed_data[-self.i-1,self.j] = shg/ref
            self.Stage.goto_xy(self.Stage.xarr[-self.i-1],self.Stage.yarr[self.j])
        self.Gal.counter.stop()
        self.Gal.reference.stop()
        self.imgProcessed = self.Stage.processed_data
        self.i = self.i + 1
        if self.i > len(self.Stage.xarr)-1:
            self.j = self.j+1
            self.i = 0
        if self.j > len(self.Stage.yarr)-1 or self.stopcall:
            self.imgSHG = self.Stage.img_data
            self.imgRef = self.Stage.ref_data
            self.start_button.setEnabled(True)
            self.scan_type.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.pause_button.setEnabled(False)
            self.liveplot.setImage(self.imgProcessed,pos=[self.a0,self.b0],scale=[self.ascale,self.bscale])
            self.Stage.set_xspeed(F=int(self.ds102dialog.xspeed))
            sleep(0.1)
            self.Stage.set_yspeed(F=int(self.ds102dialog.yspeed))
            self.spinBox_xmove.setValue(self.Stage.x)
            self.spinBox_ymove.setValue(self.Stage.y)            
            return
        self.liveplot.setImage(self.imgProcessed,pos=[self.a0,self.b0],scale=[self.ascale,self.bscale])
        if self.xstep.value() > 20 or self.ystep.value() > 20:
            while self.Stage.is_xmoving():
                while self.Stage.is_ymoving():
                    pass
        self.Gal.counter.start()
        self.Gal.reference.start()
        self.timer.singleShot(self.tstep, QtCore.Qt.PreciseTimer, self.update_data32)        

    def stage_stepscanyz(self,yarr,zarr):
        self.Stage.img_data = -ones((len(yarr),len(zarr)))
        self.Stage.ref_data = -ones((len(yarr),len(zarr)))
        self.Stage.processed_data = -ones((len(yarr),len(zarr)))
        self.Stage.yarr = yarr
        self.Stage.zarr = zarr
        self.i = 0
        self.j = 0
        self.timer = QtCore.QTimer()
        self.tstep = int(self.tperstep_set.value()*1000)
        self.Gal.counter.start()
        self.Gal.reference.start()
        self.timer.singleShot(self.tstep, QtCore.Qt.PreciseTimer, self.update_data20)        
        
    def update_data20(self):
        # update the plot data, and anything you want to change on screen
        shg = self.Gal.counter.read()
        ref = self.Gal.reference.read()*1000000
        if ref < 1000:
            ref = 1
        if self.j%2 == 0:
            self.Stage.img_data[self.i,self.j] = shg
            self.Stage.ref_data[self.i,self.j] = ref
            self.Stage.processed_data[self.i,self.j] = shg/ref
            self.Stage.goto_yz(self.Stage.yarr[self.i],self.Stage.zarr[self.j])
        else:
            self.Stage.img_data[-self.i-1,self.j] = shg
            self.Stage.ref_data[-self.i-1,self.j] = ref
            self.Stage.processed_data[-self.i-1,self.j] = shg/ref
            self.Stage.goto_yz(self.Stage.yarr[-self.i-1],self.Stage.zarr[self.j])
        self.Gal.counter.stop()
        self.Gal.reference.stop()
        self.imgProcessed = self.Stage.processed_data
        self.i = self.i + 1
        if self.i > len(self.Stage.yarr)-1:
            self.j = self.j+1
            self.i = 0
        if self.j > len(self.Stage.zarr)-1 or self.stopcall:
            self.imgSHG = self.Stage.img_data
            self.imgRef = self.Stage.ref_data
            self.start_button.setEnabled(True)
            self.scan_type.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.pause_button.setEnabled(False)
            self.liveplot.setImage(self.imgProcessed,pos=[self.a0,self.b0],scale=[self.ascale,self.bscale])
            self.Stage.set_yspeed(F=int(self.ds102dialog.yspeed))
            sleep(0.1)
            self.Stage.set_zspeed(F=int(self.ds102dialog.zspeed))
            self.spinBox_ymove.setValue(self.Stage.y)
            self.spinBox_zmove.setValue(self.Stage.z)
            return
        self.liveplot.setImage(self.imgProcessed,pos=[self.a0,self.b0],scale=[self.ascale,self.bscale])
        if self.ystep.value() > 20 or self.zstep.value() > 20:
            while self.Stage.is_ymoving():
                while self.Stage.is_zmoving():
                    pass
        self.Gal.counter.start()
        self.Gal.reference.start()
        self.timer.singleShot(self.tstep, QtCore.Qt.PreciseTimer, self.update_data20)
        
    def stage_stepscanxz(self,xarr,zarr):
        self.Stage.img_data = -ones((len(xarr),len(zarr)))
        self.Stage.ref_data = -ones((len(xarr),len(zarr)))
        self.Stage.processed_data = -ones((len(xarr),len(zarr)))
        self.Stage.xarr = xarr
        self.Stage.zarr = zarr
        self.i = 0
        self.j = 0
        self.timer = QtCore.QTimer()
        self.tstep = int(self.tperstep_set.value()*1000)
        self.Gal.counter.start()
        self.Gal.reference.start()
        self.timer.singleShot(self.tstep, QtCore.Qt.PreciseTimer, self.update_data24)        
        
    def update_data24(self):
        # update the plot data, and anything you want to change on screen
        shg = self.Gal.counter.read()
        ref = self.Gal.reference.read()*1000000
        if ref < 1000:
            ref = 1
        if self.j%2 == 0:
            self.Stage.img_data[self.i,self.j] = shg
            self.Stage.ref_data[self.i,self.j] = ref
            self.Stage.processed_data[self.i,self.j] = shg/ref
            self.Stage.goto_xz(self.Stage.xarr[self.i],self.Stage.zarr[self.j])
        else:
            self.Stage.ref_data[-self.i-1,self.j] = shg
            self.Stage.ref_data[-self.i-1,self.j] = ref
            self.Stage.processed_data[self.i,self.j] = shg/ref
            self.Stage.goto_xz(self.Stage.xarr[-self.i-1],self.Stage.zarr[self.j])
        self.Gal.counter.stop()
        self.Gal.reference.stop()
        self.imgProcessed = self.Stage.processed_data
        self.i = self.i + 1
        if self.i > len(self.Stage.xarr)-1:
            self.j = self.j+1
            self.i = 0
        if self.j > len(self.Stage.zarr)-1 or self.stopcall:
            self.imgSHG = self.Stage.img_data
            self.imgRef = self.Stage.ref_data
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.pause_button.setEnabled(False)
            self.liveplot.setImage(self.imgProcessed,pos=[self.a0,self.b0],scale=[self.ascale,self.bscale])
            self.Stage.set_xspeed(F=int(self.ds102dialog.xspeed))
            sleep(0.1)
            self.Stage.set_zspeed(F=int(self.ds102dialog.zspeed))
            self.spinBox_xmove.setValue(self.Stage.x)
            self.spinBox_zmove.setValue(self.Stage.z)
            return
        self.liveplot.setImage(self.imgProcessed,pos=[self.a0,self.b0],scale=[self.ascale,self.bscale])
        if self.xstep.value() > 20 or self.zstep.value() > 20:
            while self.Stage.is_xmoving():
                while self.Stage.is_zmoving():
                    pass
        self.Gal.counter.start()
        self.Gal.reference.start()
        self.timer.singleShot(self.tstep, QtCore.Qt.PreciseTimer, self.update_data24)
        
    def stage_stepscanx(self,xarr):
        self.lineEdit.setText('Stage: x = {0}'.format(self.Stage.xpos()))
        self.xarr = xarr
        self.Stage.Oneddata = [self.xarr[0]]
        self.Stage.count_data = [0]
        self.liveplot1d.clear()
        self.i = 0
        pen2 = pg.mkPen(color = (0,0,255), width = 2)
        self.data_line = self.liveplot1d.plot(self.Stage.Oneddata,self.Stage.count_data,pen=pen2)
        del self.Stage.Oneddata[0]
        del self.Stage.count_data[0]
        self.timer = QtCore.QTimer()
        self.tstep = int(self.tperstep_set.value()*1000)
        self.Gal.counter.start()
        self.timer.singleShot(self.tstep, QtCore.Qt.PreciseTimer, self.update_data4)
        
    def update_data4(self):
        self.Stage.count_data.append(self.Gal.counter.read())
        self.Gal.counter.stop()
        self.Stage.Oneddata.append(self.xarr[self.i])
        self.data_line.setData(self.Stage.Oneddata,self.Stage.count_data)
        self.lineEdit.setText('Stage: x = {0}'.format(self.xarr[self.i]))
        self.i = self.i + 1
        if self.i >= self.apoints or self.stopcall:
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.pause_button.setEnabled(False)
            #self.data_line.setData(self.Stage.Oneddata,self.Stage.count_data)
            self.Stage.set_xspeed(F=int(self.ds102dialog.xspeed))
            self.spinBox_xmove.setValue(self.Stage.x)
            return
        self.Stage.x = self.xarr[self.i]
        if self.xstep.value() > 20:
            while self.Stage.is_xmoving():
                pass
        self.Gal.counter.start()
        self.timer.singleShot(self.tstep, QtCore.Qt.PreciseTimer, self.update_data4)
        
    def stage_stepscany(self,yarr):
        self.yarr = yarr
        self.Stage.Oneddata = [self.yarr[0]]
        self.Stage.count_data = [0]
        self.liveplot1d.clear()
        self.i = 0
        pen2 = pg.mkPen(color = (0,0,255), width = 2)
        self.data_line = self.liveplot1d.plot(self.Stage.Oneddata,self.Stage.count_data,pen=pen2)
        del self.Stage.Oneddata[0]
        del self.Stage.count_data[0]
        self.timer = QtCore.QTimer()
        self.tstep = int(self.tperstep_set.value()*1000)
        self.Gal.counter.start()
        self.timer.singleShot(self.tstep, QtCore.Qt.PreciseTimer, self.update_data8)
        
    def update_data8(self):
        self.Stage.count_data.append(self.Gal.counter.read())
        self.Gal.counter.stop()
        self.Stage.Oneddata.append(self.yarr[self.i])
        self.data_line.setData(self.Stage.Oneddata,self.Stage.count_data)
        self.lineEdit.setText('Stage: y = {0}'.format(self.yarr[self.i]))
        self.i = self.i + 1
        if self.i >= self.apoints or self.stopcall:
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.pause_button.setEnabled(False)
            self.data_line.setData(self.Stage.Oneddata,self.Stage.count_data)
            self.Stage.set_yspeed(F=int(self.ds102dialog.yspeed))
            self.spinBox_ymove.setValue(self.Stage.y)
            return
        self.Stage.y = self.yarr[self.i]
        if self.ystep.value() > 20:
            while self.Stage.is_ymoving():
                pass
        self.Gal.counter.start()
        self.timer.singleShot(self.tstep, QtCore.Qt.PreciseTimer, self.update_data8)
        
    def stage_stepscanz(self,zarr):
        self.zarr = zarr
        self.Stage.Oneddata = [self.zarr[0]]
        self.Stage.count_data = [0]
        self.liveplot1d.clear()
        self.i = 0
        pen2 = pg.mkPen(color = (0,0,255), width = 2)
        self.data_line = self.liveplot1d.plot(self.Stage.Oneddata,self.Stage.count_data,pen=pen2)
        del self.Stage.Oneddata[0]
        del self.Stage.count_data[0]
        self.timer = QtCore.QTimer()
        self.tstep = int(self.tperstep_set.value()*1000)
        self.Gal.counter.start()
        self.timer.singleShot(self.tstep, QtCore.Qt.PreciseTimer, self.update_data12)
        
    def update_data12(self):
        self.Stage.count_data.append(self.Gal.counter.read())
        self.Gal.counter.stop()
        self.Stage.Oneddata.append(self.zarr[self.i])
        self.data_line.setData(self.Stage.Oneddata,self.Stage.count_data)
        self.lineEdit.setText('Stage: z = {0}'.format(self.zarr[self.i]))
        self.i = self.i + 1
        if self.i >= self.apoints or self.stopcall:
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.pause_button.setEnabled(False)
            self.data_line.setData(self.Stage.Oneddata,self.Stage.count_data)
            self.Stage.set_zspeed(F=int(self.ds102dialog.zspeed))
            self.spinBox_zmove.setValue(self.Stage.z)
            return
        self.Stage.z = self.zarr[self.i]
        if self.zstep.value() > 20:
            while self.Stage.is_zmoving():
                pass
        self.Gal.counter.start()
        self.timer.singleShot(self.tstep, QtCore.Qt.PreciseTimer, self.update_data12)
        
    def stage_stepscanxyz(self,xarr,yarr,zarr):
        self.Stage.img_data = -ones((len(xarr),len(yarr)))
        self.Stage.ref_data = -ones((len(xarr),len(yarr)))
        self.Stage.processed_data = -ones((len(xarr),len(yarr)))
        self.img3dSHG = -ones((len(zarr),len(xarr),len(yarr)))
        self.img3dRef = -ones((len(zarr),len(xarr),len(yarr)))
        self.img3dProcessed = -ones((len(zarr),len(xarr),len(yarr)))
        self.Stage.xarr = xarr
        self.Stage.yarr = yarr
        self.Stage.zarr = zarr
        self.i = 0
        self.j = 0
        self.k = 0
        self.timer = QtCore.QTimer()
        self.tstep = int(self.tperstep_set.value()*1000)
        self.Gal.counter.start()
        self.Gal.reference.start()
        self.timer.singleShot(self.tstep, QtCore.Qt.PreciseTimer, self.update_data40)        
        
    def update_data40(self):
        # update the plot data, and anything you want to change on screen
        shg = self.Gal.counter.read()
        ref = self.Gal.reference.read()*1000000
        if ref < 1000:
            ref = 1
        if self.j%2 == 0:
            self.Stage.img_data[self.i,self.j] = shg
            self.Stage.ref_data[self.i,self.j] = ref
            self.Stage.processed_data[self.i,self.j] = shg/ref
            self.Stage.goto_xy(self.Stage.xarr[self.i],self.Stage.yarr[self.j])
        else:
            self.Stage.img_data[-self.i-1,self.j] = shg
            self.Stage.ref_data[-self.i-1,self.j] = ref
            self.Stage.processed_data[-self.i-1,self.j] = shg/ref
            self.Stage.goto_xy(self.Stage.xarr[-self.i-1],self.Stage.yarr[self.j])
        self.Gal.counter.stop()
        self.Gal.reference.stop()
        self.imgProcessed = self.Stage.Processed_data
        self.liveplot.setImage(self.imgProcessed,pos=[self.a0,self.b0],scale=[self.ascale,self.bscale])
        self.i = self.i + 1        
        if self.i > len(self.Stage.xarr)-1:
            self.j = self.j+1
            self.i = 0
        if self.j > len(self.Stage.yarr)-1:
            self.img3dProcessed[self.k,:,:] = self.Stage.processed_data
            self.img3dSHG[self.k,:,:] = self.Stage.img_data
            self.img3dRef[self.k,:,:] = self.Stage.ref_data
            self.k = self.k+1
            self.i = 0
            self.j = 0
            self.Stage.img_data = -ones((len(self.Stage.xarr),len(self.Stage.yarr)))
        if self.k > len(self.Stage.zarr)-1 or self.stopcall:
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.pause_button.setEnabled(False)
            self.imgProcessed = self.img3dProcessed
            self.imgSHG = self.img3dSHG
            self.imgRef = self.img3dRef
            self.liveplot.setImage(self.imgProcessed,pos=[self.a0,self.b0],scale=[self.ascale,self.bscale],xvals=self.Stage.zarr)
            self.Stage.set_xspeed(F=int(self.ds102dialog.xspeed))
            sleep(0.1)
            self.Stage.set_yspeed(F=int(self.ds102dialog.yspeed))
            sleep(0.1)
            self.Stage.set_zspeed(F=int(self.ds102dialog.zspeed))
            self.spinBox_xmove.setValue(self.Stage.x)
            self.spinBox_ymove.setValue(self.Stage.y)
            self.spinBox_zmove.setValue(self.Stage.z)
            return
        if self.i == 0 and self.j == 0:
            sleep(0.1)
            self.Stage.goto_xyz(self.Stage.xarr[self.i],self.Stage.yarr[self.j],self.Stage.zarr[self.k])
            sleep(0.1)
            self.display_stagemove_msg()
            self.spinBox_zmove.setValue(self.Stage.z)
        if self.xstep.value() > 20 or self.ystep.value() > 20:
            while self.Stage.is_xmoving():
                while self.Stage.is_ｙmoving():
                    while self.Stage.is_zmoving():
                        pass
        self.Gal.counter.start()
        self.Gal.reference.start()
        self.timer.singleShot(self.tstep, QtCore.Qt.PreciseTimer, self.update_data40)
        
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
    
    def scan_method_change(self):
        if self.scan_method.currentIndex() == 0:
            self.srate_set.setEnabled(True)
            self.tperstep_set.setEnabled(False)
            self.xstep.setMinimum(0.0001)
            self.xstep.setDecimals(4)
            self.ystep.setMinimum(0.0001)
            self.ystep.setDecimals(4)
        elif self.scan_method.currentIndex() == 1:
            self.srate_set.setEnabled(False)
            self.tperstep_set.setEnabled(True)
        
    def scan_type_change(self):
        if self.scan_type.currentIndex() == 1:
            if self.scan_method.currentIndex() == 0:
                self.scan_method.setCurrentIndex(1)
            self.scan_method.model().item(0).setEnabled(False)
            self.xsize.setMaximum(self.ds102dialog.xmax-self.xpos.value())
            self.ysize.setMaximum(self.ds102dialog.ymax-self.ypos.value())
            self.xstep.setMinimum(1)
            self.xstep.setDecimals(0)
            self.ystep.setMinimum(1)
            self.ystep.setDecimals(0)
            self.xpos.setDecimals(0)
            self.ypos.setDecimals(0)
            self.xsize.setDecimals(0)
            self.ysize.setDecimals(0)
        else:
            self.scan_method.model().item(0).setEnabled(True)
            if self.scan_method.currentIndex() == 1:
                self.scan_method.setCurrentIndex(0)
            self.xpos.setMaximum(self.galvanodialog.xmax)
            self.xpos.setMinimum(self.galvanodialog.xmin)
            self.ypos.setMaximum(self.galvanodialog.ymax)
            self.ypos.setMinimum(self.galvanodialog.ymin)
            self.xsize.setMaximum(self.galvanodialog.xmax-self.xpos.value())
            self.ysize.setMaximum(self.galvanodialog.ymax-self.ypos.value())
            self.xstep.setMinimum(0.0001)
            self.xstep.setDecimals(4)
            self.ystep.setMinimum(0.0001)
            self.ystep.setDecimals(4)
            self.xpos.setDecimals(4)
            self.ypos.setDecimals(4)
            self.xsize.setDecimals(4)
            self.ysize.setDecimals(4)
            
    def stop_program(self):
        self.timer.stop()
        self.stopcall = True
        self.start_button.setEnabled(True)
        self.scan_type.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.pause_button.setEnabled(False)
        if self.scanNum == 29 or self.scanNum == 30 or self.scanNum == 37:
            self.Gal.stop_scanxy()
        else:
            self.Gal.counter.stop()
            self.Gal.reference.stop()
        
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
      


        
        
    

