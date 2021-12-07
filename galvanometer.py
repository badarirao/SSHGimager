# -*- coding: utf-8 -*-
"""
Created on Thu Jan 21 17:15:58 2021

Notes: 

"""

from numpy import ones, append, flip, shape, zeros, diff, linspace, array, divide
from nidaqmx.constants import Edge, READ_ALL_AVAILABLE, CountDirection, TimeUnits
from time import time,sleep
from nidaqmx import stream_writers, Task
from nidaqmx.constants import AcquisitionType, TerminalConfiguration
from nidaqmx.errors import DaqError
from nidaqmx.error_codes import DAQmxErrors

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
        return self._x*self.xscale
    
    @x.setter 
    def x(self,value):
        self._x = value/self.xscale
        try:
            self.taskxy.write([self._x,self._y])
        except DaqError as mes:
            if mes.error_code == DAQmxErrors.INVALID_TASK.value:
                self.create_taskxy()
            else:
                self.taskxy.close()
                self.create_taskxy()
            self.taskxy.write([self._x,self._y])
             
    @property 
    def y(self):
        return self._y*self.yscale
    
    @y.setter
    def y(self,value):
        self._y = value/self.yscale
        try:
            self.taskxy.write([self._x,self._y])
        except DaqError as mes:
            if mes.error_code == DAQmxErrors.INVALID_TASK.value:
                self.create_taskxy()
            else:
                self.taskxy.close()
                self.create_taskxy()
            self.taskxy.write([self._x,self._y])
        
    def gotoxy(self,x,y):
        self._x = x/self.xscale
        self._y = y/self.yscale
        try:
            self.taskxy.write([self._x,self._y])
        except DaqError as mes:
            if mes.error_code == DAQmxErrors.INVALID_Task.value:
                self.create_taskxy()
            else:
                self.taskxy.close()
                self.create_taskxy()
            self.taskxy.write([self._x,self._y])
        
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
            a1 = append(a1[:-1],flip(a1))
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
        a1_arr = append(a1_arr[0],a1_arr)
        a2_arr = append(a2_arr[0],a2_arr)
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
        self.xarr = xarr/self.xscale
        self.yarr = yarr/self.yscale
        self.xarr = self.xarr+self.xhome
        self.yarr = self.yarr+self.yhome
        t = 10 # default timeout = 10 seconds
        sample = self.getxyarray(self.xarr,self.yarr,retrace)
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
        self.shgData = zeros(self.sam_pc)
        self.refData = -ones(self.sam_pc,dtype=float)
        #self.processedData = zeros(self.sam_pc)
        self.counter.start()
        self.reference.start()
        self.taskxy.start()
        self.i = 0
        self.startscan = True

    def update_scanxy(self):
        if self.startscan == False:
            return False
        try:
            buffer_shg = array(self.counter.read(number_of_samples_per_channel=READ_ALL_AVAILABLE),dtype=float)
            number_of_SHG_samples = len(buffer_shg)
            buffer_ref = 1000000*array(self.reference.read(number_of_samples_per_channel=number_of_SHG_samples),dtype=float)
            buffer_ref[buffer_ref < 1000] = 1  # to avoid divide by zero error
        except DaqError:
            print("Daqerror encountered")
            self.startscan = False
            return False
        l = len(buffer_shg)
        self.shgData[self.i:self.i+l] = buffer_shg
        self.refData[self.i:self.i+l] = buffer_ref
        self.diff_data_shg = diff(self.shgData)
        self.diff_data_ref = self.refData[1:]
        self.processedData = self.diff_data_shg/self.diff_data_ref
        self.i = self.i+l
        try:
            self.diff_data_shg[self.i-1] = 0
            self.processedData[self.i-1] = 0
        except IndexError:
            pass
        self.rawimg_dataSHG = self.diff_data_shg.reshape(len(self.xarr),len(self.yarr),order='F') # some problem with this
        self.rawimg_dataRef = self.diff_data_ref.reshape(len(self.xarr),len(self.yarr),order='F')
        self.processed_img = self.processedData.reshape(len(self.xarr),len(self.yarr),order='F')
        self.img_dataSHG = []
        self.img_dataRef = []
        self.img_Processed = []
        for p,q in enumerate(self.rawimg_dataSHG.T):
            if p%2 == 0:
                self.img_dataSHG.append(q)
            else:
                self.img_dataSHG.append(flip(q))
        for p,q in enumerate(self.rawimg_dataRef.T):
            if p%2 == 0:
                self.img_dataRef.append(q)
            else:
                self.img_dataRef.append(flip(q))
        for p,q in enumerate(self.processed_img.T):
            if p%2 == 0:
                self.img_Processed.append(q)
            else:
                self.img_Processed.append(flip(q))
        self.img_dataSHG = array(self.img_dataSHG).T
        self.img_dataRef = array(self.img_dataRef).T
        self.img_Processed = array(self.img_Processed).T
        #return not self.taskxy.is_task_done()
        tj = self.taskxy.is_task_done()
        if tj or self.i >= self.sam_pc:
            return False
        return True
    
    def stop_scanxy(self):
        self.counter.stop()
        self.reference.stop()
        self.taskxy.stop()
        self.startscan = False
 
    def scanxy(self,xarr,yarr,retrace=2):
        xarr = xarr/self.xscale
        yarr = yarr/self.yscale
        xarr = xarr+self.xhome
        yarr = yarr+self.yhome
        t = 10 # default timeout = 10 seconds
        sample = self.getxyarray(xarr,yarr,retrace)
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
        data = zeros(self.sam_pc)
        self.counter.start()
        self.taskxy.start()
        i = 0
        while True:
            sleep(0.5)
            buffer = self.counter.read(number_of_samples_per_channel=READ_ALL_AVAILABLE)
            l = len(buffer)
            data[i:i+l] = buffer
            self.img_data = diff(data)
            i = i+l
            try:
                self.img_data[i-1] = 0
            except IndexError:
                pass
            #print(self.img_data)
            if self.taskxy.is_task_done() or i >= self.sam_pc:
                break
        self.counter.stop()
        self.taskxy.stop()
        return self.img_data
        
    def close_all_channels(self):
        self.taskxy.close()
        self.counter.close()
        self.reference.close()
        
    def get_tstep(self,t = 6.78):
        if self.srate <= 0:
            self.srate = 1
        self.time_per_step = 1000/self.srate # milliseconds
        
        # recalibrate this step after including the whole program
        if self.time_per_step > 10:
            return self.time_per_step - t
        elif self.time_per_step >= 6.4:
            return 9.299-58.99/self.time_per_step
        else:
            return 0
        
    def scanx2(self,xarr):
        xarr = xarr/self.xscale
        xarr = xarr+self.xhome
        tstep = self.get_tstep()
        for i in xarr:
            self.gotox(i)
            sleep(tstep)
        
    def scany2(self,yarr):
        yarr = yarr/self.yscale
        yarr = yarr+self.yhome
        tstep = self.get_tstep()
        for i in yarr:
            self.gotoy(i)
            sleep(tstep)
        
    def scanxy2(self,xarr,yarr):
        xarr = xarr/self.xscale
        yarr = yarr/self.yscale
        xarr = xarr+self.xhome
        yarr = yarr+self.yhome
        tstep = self.get_tstep(self.t)
        if self.fast_dir == 'x':
            stime = time()
            for j in yarr:
                for i in xarr:
                    self.gotoxy(i,j)
                    sleep(tstep/1000)
        elif self.fast_dir == 'y':
            stime = time()
            for i in xarr:
                for j in yarr:
                    self.gotoxy(i,j)
                    sleep(tstep/1000)
        etime = time()
        return len(xarr)*len(yarr)/(etime-stime)
        #print('Total scan time per line = {0}'.format((etime-stime)/len(yarr)))
        #print('Scan rate = {0}'.format(len(xarr)/((etime-stime)/len(yarr))))
        
    def optimize_srate(self):
        xarr = linspace(-3,3,50)
        yarr= linspace(-3,3,9)
        sr = [10,20,50]
        for s in sr:
            self.srate = s
            treq = 1000/s
            while True:
                sr1 = self.scanxy(xarr,yarr)
                tact = 1000/sr1
                if sr1 >= s+0.5 or sr1 <= s-0.5:
                    self.t = self.t - (treq-tact)/2
                    #print("Change tstep to {0}".format(self.t))
                else:
                    #print("optimum t = {0}".format(self.t))
                    #print("Set scan rate = {0}, actual = {1}".format(s,sr1))
                    break
    
    def optimize_srate2(self):
        xarr = linspace(-3,3,50)
        yarr= linspace(-3,3,9)
        sr = []
        tstep = linspace(0,3.11,21)
        for s in tstep:
            sr.append(self.scanxy(xarr,yarr,s))
        return sr
    
    def __del__(self):
        try:
            self.taskxy.close()
            self.counter.close()
            self.reference.close()
        except:
            pass
        
"""
img = Scan()
import numpy as np
xarr = np.linspace(-3,3,50)
yarr = np.linspace(-3,3,9)
"""
