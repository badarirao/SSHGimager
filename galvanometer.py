# -*- coding: utf-8 -*-
"""
Created on Thu Jan 21 17:15:58 2021

Notes: 

"""

from numpy import ones, append, flip, shape, zeros, diff, array, copy
from nidaqmx.constants import Edge, READ_ALL_AVAILABLE, CountDirection
from nidaqmx import stream_writers, Task, stream_readers
from nidaqmx.types import CtrTime
from nidaqmx.constants import AcquisitionType, TerminalConfiguration
from nidaqmx.errors import DaqError
from nidaqmx.error_codes import DAQmxErrors
from time import sleep
from PyQt5.QtCore import QTimer, QEventLoop
from PyQt5.QtCore import Qt

class Galvano():
    def __init__(self,daq='Dev1/',aochan='ao0:1'):
        self.daq = daq
        self.ao_chan = daq+aochan
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
        

    def create_taskxy(self):
        self.taskxy = Task()
        self.taskxy.ao_channels.add_ao_voltage_chan(self.ao_chan)
    
    def create_taskx(self):
        self.taskx = Task()
        self.taskx.ao_channels.add_ao_voltage_chan("Dev1/ao0")
        
    def set_xscan_param(self,nx=100,xmin=-10,xmax=10):
        self.nx = nx
        self.xVmax = xmax/self.xscale
        self.xVmin = xmin/self.xscale
    
    def set_yscan_param(self,ny=100,ymin=-10,ymax=10):
        self.ny = ny
        self.ymax = ymax/self.yscale
        self.ymin = ymin/self.yscale
        
    def set_scan_param(self,fast_dir='x',srate=100):
        self.fast_dir = fast_dir
        self.srate = srate
        
    @property
    def srate(self):
        return self._srate
    
    @srate.setter
    def srate(self,value):
        if self._srate != value:
            self._srate = value
        
    @property
    def fast_dir(self):
        return self._fast_dir
    
    @fast_dir.setter 
    def fast_dir(self,value):
        a = ['x','X','y','Y']
        if value in a:
            if self._fast_dir != value:
                self._fast_dir = value
        else:
            raise ValueError("Please specify only 'x' or 'y' ")
            
    @property 
    def xscale(self):
        return self._xscale
    
    @xscale.setter 
    def xscale(self,value):
        self._xscale = value
    
    @property 
    def yscale(self):
        return self._yscale
    
    @yscale.setter 
    def yscale(self,value):
        self._yscale = value
    
    @property 
    def x(self):
        return self._x/self.xscale
    
    @x.setter 
    def x(self,value):
        self._x = value*self.xscale
        try:
            self.taskxy.write([self._y,self._x])
        except DaqError as mes:
            if mes.error_code == DAQmxErrors.INVALID_TASK.value:
                self.create_taskxy()
            else:
                self.taskxy.close()
                self.create_taskxy()
            self.taskxy.write([self._y,self._x])
             
    @property 
    def y(self):
        return self._y/self.yscale
    
    @y.setter
    def y(self,value):
        self._y = value*self.yscale
        try:
            self.taskxy.write([self._y,self._x])
        except DaqError as mes:
            if mes.error_code == DAQmxErrors.INVALID_TASK.value:
                self.create_taskxy()
            else:
                self.taskxy.close()
                self.create_taskxy()
            self.taskxy.write([self._y,self._x])
        
    def gotoxy(self,x,y):
        self._x = x*self.xscale
        self._y = y*self.yscale
        try:
            self.taskxy.write([self._y,self._x])
        except DaqError as mes:
            if mes.error_code == DAQmxErrors.INVALID_Task.value:
                self.create_taskxy()
            else:
                self.taskxy.close()
                self.create_taskxy()
            self.taskxy.write([self._y,self._x])
        
    def getxyarray(self,xarr,yarr,retrace=2):
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
                a1_arr = append(a1_arr,a1)
                a2_arr = append(a2_arr,a2[i+1]*ones(len(a1)))
        elif retrace == -1: # scan each line only in opposite direction (only retrace)
            a1_arr = flip(a1)
            a2_arr = a2[0]*ones(len(a1))
            for i in range(len(a2)-1):
                a1_arr = append(a1_arr,flip(a1))
                a2_arr = append(a2_arr,a2[i+1]*ones(len(a1)))
        elif retrace == 0: # scan trace and retrace a line, then go to next line
            a1 = append(a1,flip(a1))
            a1_arr = a1
            a2_arr = a2[0]*ones(len(a1))
            for i in range(len(a2)-1):
                a1_arr = append(a1_arr,a1)
                a2_arr = append(a2_arr,a2[i+1]*ones(len(a1)))
        elif retrace == 2: # scan trace one line, retrace next line , and so on..
            a1_arr = a1
            a2_arr = a2[0]*ones(len(a1))
            flp = 1
            for i in range(len(a2)-1):
                flp = flp * -1
                if flp == -1:
                    a1_arr = append(a1_arr,flip(a1))
                else:
                    a1_arr = append(a1_arr,a1)
                a2_arr = append(a2_arr,a2[i+1]*ones(len(a1)))
        if self.fast_dir == 'x':
            a1_arr = append(a1_arr[0],a1_arr)
            a2_arr = append(a2_arr[0],a2_arr)
        else:
            temp = copy(a2_arr)
            a2_arr = append(a1_arr[0],a1_arr)
            a1_arr = append(temp[0],temp)
        return append(a1_arr,a2_arr).reshape(2,len(a1_arr))
                
class Scan(Galvano):
    def __init__(self,daq='Dev1/',aochan='ao0:1',ctr='ctr0',ctr_src='PFI0',s_clock='/ao/SampleClock'):
        super().__init__(daq,aochan)
        self.ctr_chan = daq + ctr
        self.ctr_src_chan = '/' + daq + ctr_src
        self.s_clock_chan = '/' + daq + s_clock
        self.create_ctr()
        self.create_ref()
        self.img_Processed = zeros(10)
        self.img_dataSHG = zeros(10)
        self.img_dataRef = zeros(10)
        self.scanning = True
        self.ID = 'NI6211'
    
    def create_ctr(self):
        try:
            self.counter.close()
        except (DaqError, AttributeError):
            pass
        finally:
            try:
                self.counter = Task('counter')
                self.counter.ci_channels.add_ci_count_edges_chan(self.ctr_chan,
                 initial_count=0,edge=Edge.RISING,count_direction=CountDirection.COUNT_UP)
                self.counter.channels.ci_count_edges_term = self.ctr_src_chan
            except Exception as e:
                print(e)
                raise DaqError
            
    def create_ref(self):
        try:
            self.reference.close()
        except (DaqError, AttributeError):
            pass
        finally:
            try:
                self.reference = Task()
                self.reference.ai_channels.add_ai_voltage_chan('Dev1/ai0',
                 terminal_config = TerminalConfiguration.RSE, min_val = 0, max_val = 2)
                self.reference.channels.ai_rng_high = 0.2
                self.reference.channels.ai_rng_low = -0.2
            except Exception as e:
                print(e)
                raise DaqError
            
    def start_scanxy(self,xarr,yarr,retrace=2):
        self.startscan = True
        self.retrace = retrace
        self.xarr = xarr*self.xscale + self.xhome
        self.yarr = yarr*self.yscale + self.yhome
        self.i = 0
        t = 10 # default timeout = 10 seconds
        sample = self.getxyarray(self.xarr,self.yarr,retrace)
        self.sampleIndex = self.getxyarray(range(len(self.xarr)),range(len(self.yarr)),retrace)
        self.sampleIndex = self.sampleIndex[:,1:].astype(int)
        self.sam_pc = shape(sample)[1]
        total_time = self.sam_pc*len(sample)/self.srate
        if t < total_time + 1:
            t = total_time + 2
        # configure the galvanometer    
        self.taskxy.timing.cfg_samp_clk_timing(rate = self.srate+1, \
                                               sample_mode = AcquisitionType.FINITE, \
                                                   samps_per_chan = self.sam_pc)
        self.taskxy.timing.cfg_samp_clk_timing(rate = self.srate, \
                                               sample_mode = AcquisitionType.FINITE, \
                                                   samps_per_chan = self.sam_pc)
        writer = stream_writers.AnalogMultiChannelWriter(self.taskxy.out_stream,auto_start=False)
        writer.write_many_sample(sample,timeout=t)
        # configure the photodetector (counter)
        self.counter.timing.cfg_samp_clk_timing(self.srate, source="/Dev1/ao/SampleClock",\
                                                sample_mode=AcquisitionType.FINITE,\
                                                    samps_per_chan=self.sam_pc)
        self.counter.in_stream.read_all_avail_samp = True
        self.reference.timing.cfg_samp_clk_timing(self.srate,source="/Dev1/ao/SampleClock",\
                                                  sample_mode=AcquisitionType.FINITE,\
                                                      samps_per_chan=self.sam_pc)
        self.reference.in_stream.read_all_avail_samp = True
        if retrace != 0:
            self.shgData = zeros(self.sam_pc)
            self.refData = -ones(self.sam_pc)
        else:
            self.shgData = zeros(self.sam_pc)
            self.refData = -ones(self.sam_pc)
            self.shgData2 = zeros(self.sam_pc)
            self.refData2 = -ones(self.sam_pc)
        self.counter.start()
        self.reference.start()
        self.taskxy.start()
    
    def update_scanxy(self):
        if self.startscan == False:
            return False
        try:
            buffer_shg = array(self.counter.read(number_of_samples_per_channel=READ_ALL_AVAILABLE),dtype=float)
            number_of_SHG_samples = len(buffer_shg)
            buffer_ref = 1000000*array(self.reference.read(number_of_samples_per_channel=number_of_SHG_samples),dtype=float)
            buffer_ref[buffer_ref < 1000] = 1  # to avoid divide by zero error
            self.shgData[self.i:self.i+number_of_SHG_samples] = buffer_shg
            self.refData[self.i:self.i+number_of_SHG_samples] = buffer_ref
            self.diff_data_shg = diff(self.shgData)
            self.i += number_of_SHG_samples
            try:
                self.diff_data_shg[self.i-1] = 0
            except IndexError:
                pass
            self.img_dataSHG = zeros((len(self.xarr),len(self.yarr)))
            self.img_dataRef = -ones((len(self.xarr),len(self.yarr)))
            if self.retrace == 0:
                self.img_dataSHG2 = zeros((len(self.xarr),len(self.yarr)))
                self.img_dataRef2 = -ones((len(self.xarr),len(self.yarr)))
            for pos in range(self.sam_pc-1):
                i = self.sampleIndex[0,pos]
                j = self.sampleIndex[1,pos]
                if self.retrace != 0:
                    self.img_dataSHG[i,j] = self.diff_data_shg[pos]
                    self.img_dataRef[i,j] = self.refData[pos+1]
                else:
                    if self.img_dataSHG[i,j] == 0:
                        self.img_dataSHG[i,j] = self.diff_data_shg[pos]
                        self.img_dataRef[i,j] = self.refData[pos+1]
                    else:
                        self.img_dataSHG2[i,j] = self.diff_data_shg[pos]
                        self.img_dataRef2[i,j] = self.refData[pos+1]
            self.img_Processed = self.img_dataSHG/self.img_dataRef
            if self.retrace == 0:
                self.img_Processed2 = self.img_dataSHG2/self.img_dataRef2
            tj = self.taskxy.is_task_done()
            if tj or self.i >= self.sam_pc:
                return False
            return True
        except DaqError:
            print("Daqerror encountered")
            self.startscan = False
            return False
    
    def stop_scanxy(self):
        self.counter.stop()
        self.reference.stop()
        self.create_ref()
        self.taskxy.stop()
        self.startscan = False
        print('Executed gal stop scanxy')
        
    def start_single_point_counter(self):
        try:
            self.taskxy.close()
        except:
            pass
        self.create_taskx()
        self.taskx.timing.cfg_samp_clk_timing(rate = self.srate+1, \
                                               sample_mode = AcquisitionType.FINITE, \
                                                   samps_per_chan = 2)
        self.taskx.timing.cfg_samp_clk_timing(rate = self.srate, \
                                               sample_mode = AcquisitionType.FINITE,\
                                                   samps_per_chan=2)
        self.counter.timing.cfg_samp_clk_timing(self.srate, source="/Dev1/ao/SampleClock",\
                                                sample_mode=AcquisitionType.FINITE,\
                                                    samps_per_chan=2)
        self.counter.in_stream.read_all_avail_samp = True
        writer = stream_writers.AnalogSingleChannelWriter(self.taskx.out_stream)
        data = array((self.x,self.x),dtype=float)
        writer.write_many_sample(data)
        self.reference.start()
        # first just try to see if the pulse generator works fine.
    
    def readCounts(self):
        # TODO check if counter works properly
        """
        counts = 0
        refV = 1
        self.counter.start()
        self.reference.start()
        loop = QEventLoop()
        QTimer.singleShot(1/self.srate, Qt.PreciseTimer, loop.quit)
        #sleep(1/self.srate)
        counts = self.counter.read()
        refV = self.reference.read()*1000000
        self.counter.stop()
        self.reference.stop()
        return counts,refV
        """
        counts = 0
        refV = 1
        self.counter.start()
        self.taskx.start()
        while not self.counter.is_task_done():
            pass
        counts = diff(array(self.counter.read(number_of_samples_per_channel = READ_ALL_AVAILABLE),dtype=float))
        refV = 1000000*self.reference.read()
        if refV < 1000:
            refV = 1
        self.counter.stop()
        self.taskx.stop()
        return counts[0],refV

    def stop_single_point_counter(self):
        self.counter.stop()
        self.reference.stop()
        self.create_ref()
        self.taskx.close()
        self.create_taskxy()
        
    def close_all_channels(self):
        self.taskxy.close()
        self.counter.close()
        self.reference.close()
                  
    """
    def __del__(self):
        try:
            self.taskxy.close()
            self.counter.close()
            self.reference.close()
            self.taskx.close()
        except:
            pass
    """
        
"""
img = Scan()
import numpy as np
xarr = np.linspace(-3,3,50)
yarr = np.linspace(-3,3,9)
"""
