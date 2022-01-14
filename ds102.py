# -*- coding: utf-8 -*-
"""
Created on Mon Jan 18 10:20:06 2021

@author: badari
"""

from serial import Serial
from time import sleep

Resol = { 1:0, 2:1, 2.5:2, 4:3, 5:4, 8:5, 
          10:6,20:7, 25:8, 40:9, 50:10, 80:11,
          100:12, 125:13, 200:14, 250:15 }

iResol = { 0:1, 1:2, 2:2.5, 3:4, 4:5, 5:8, 
          6:10, 7:20, 8:25, 9:40, 10:50, 11:80,
          12:100, 13:125, 14:200, 15:250 }

def get_valid_drive(param):
    if param in Resol:
        return param
    elif param < 1.5:
        return 1
    elif param < 2.25:
        return 2
    elif param < 3.25:
        return 2.5
    elif param < 4.5:
        return 4
    elif param < 6.5:
        return 5
    elif param < 9:
        return 8
    elif param < 15:
        return 10
    elif param < 22.5:
        return 20
    elif param < 32.5:
        return 25
    elif param < 45:
        return 40
    elif param < 65:
        return 50
    elif param < 90:
        return 80
    elif param < 112.5:
        return 100
    elif param < 162.5:
        return 125
    elif param < 225:
        return 200
    else:
        return 250
    
    
class DS102(Serial):
        def __init__(self,port=None,**kwargs):
            super().__init__(port,**kwargs)
            # set default values of serial communication for DS102 xyz stage
            self.baudrate = kwargs.get('baudrate',19200)
            self.bytesize = kwargs.get('bytesize',8)
            self.stopbits = kwargs.get('stopbits',1)
            self.parity = kwargs.get('parity','N')
            self.timeout = kwargs.get('timeout',0.15)
            self.write_timeout = kwargs.get('write_timeout', 0.15)
            self._expect_len = 120
            self.write_param("AXIsX:CWSoftLimitEnable 1:CCWSoftLimitEnable 1")
            self.write_param("AXIsY:CWSoftLimitEnable 1:CCWSoftLimitEnable 1")
            self.write_param("AXIsZ:CWSoftLimitEnable 1:CCWSoftLimitEnable 1")
            self.write_param("AXIsX:SELectSPeed 0")
            self.write_param("AXIsY:SELectSPeed 1")
            self.write_param("AXIsZ:SELectSPeed 2")
            self.set_unit(1) # set unit as micrometer
            self.set_xspeed(F=1000)
            self.set_yspeed(F=1000)
            self.set_zspeed(F=1000)
            if self.read_param('AXIsX:MEMorySwitch0?') == '0':
                self.initialize_x()
            if self.read_param('AXIsY:MEMorySwitch0?') == '0':
                self.initialize_y()
            if self.read_param('AXIsZ:MEMorySwitch0?') == '0':
                self.initialize_z()
            self.xscale = 1
            self.yscale = 1
            self.zscale = 1
            self.xhome = 0
            self.yhome = 0
            self.zhome = 0
            self._x = int(self.xpos())
            self._y = int(self.ypos())
            self._z = int(self.zpos())
            self.ID = 'DS102'
        
        def read_param(self,param):
            self.write(bytes(param+'\r','UTF-8'))
            #sleep(0.05)
            return self.read(100).decode('ascii')[:-1]
        
        def write_param(self,param):
            self.write(bytes(param+'\r','UTF-8'))
            #sleep(0.1)
            
        def zpos(self):
            return -int(self.read_param("AXIsZ:Position?"))
        
        def xpos(self):
            return int(self.read_param("AXIsX:Position?"))
        
        def ypos(self):
            return int(self.read_param("AXIsY:Position?"))
            
        def initialize_x(self):
            self.write_param('AXIsX:MEMorySwitch0 9')
            self.write_param('AXIsX:GO 2')
            #print('initialized x')
        
        def initialize_y(self):
            self.write_param('AXIsY:MEMorySwitch0 9')
            self.write_param('AXIsY:GO 2')
            #print('initialized y')
        
        def initialize_z(self):
            self.write_param('AXIsZ:MEMorySwitch0 9')
            self.write_param('AXIsZ:GO 2')
            #print('initialized z')
            
        @property 
        def x(self):
            return self._x
        
        @x.setter 
        def x(self,value):
            if self._x == value:
                return
            self._x = int(value)
            self.write_param("AXIX:GOABS {0}".format(-self._x))
                       
        @property 
        def y(self):
            return self._y
        
        @y.setter 
        def y(self,value):
            if self._y == int(value):
                return
            self._y = value
            self.write_param("AXIY:GOABS {0}".format(self._y))
        
        @property 
        def z(self):
            return self._z
        
        @z.setter 
        def z(self,value):
            if self._z == int(value):
                return
            self._z = value
            self.write_param("AXIZ:GOABS {0}".format(-self._z))
        
        def goto_x(self,x):
            self.x = x
            #while self.is_xmoving():
            #    pass
        
        def goto_y(self,y):
            self.y = y
            #while self.is_ymoving():
            #    pass
        
        def goto_z(self,z):
            self.z = z
            #while self.is_zmoving():
            #    pass

        def goto_xy(self,x,y):
            if self._x == x and self._y == y:
                return
            self.write_param("GOLA X{0} Y{1}".format(-x,y))
            self._x = int(x)
            self._y = int(y)
            #while self.is_xmoving() or self.is_ymoving():
            #    pass
        
        def goto_xz(self,x,z):
            if self._x == x and self._z == z:
                return
            self.write_param("GOLineA X{0} Z{1}".format(-x,-z))
            self._x = int(x)
            self._z = int(z)
            #while self.is_xmoving() or self.is_zmoving():
            #    pass
        
        def goto_yz(self,y,z):
            if self._y == y and self._z == z:
                return
            self.write_param("GOLineA Y{0} Z{1}".format(y,-1*z))
            self._y = int(y)
            self._z = int(z)
            #while self.is_ymoving() or self.is_zmoving():
            #    pass
        
        def goto_xyz(self,x,y,z):
            if self._x == x and self._y == y and self._z == z:
                return
            self.write_param("GOLineA X{0} Y{1} Z{2}".format(-x,y,-z))
            self._x = int(x)
            self._y = int(y)
            self._z = int(z)
            #while self.is_xmoving() or self.is_ymoving() or self.is_zmoving():
            #    pass
        
        def gorel_xy(self,x,y):
            if x==0 and y == 0:
                return
            self.write_param("AXIsX:PULSe {0}:AXIsY:PULSe {1}".format(-x,y))

        def gorel_xz(self,x,z):
            if x == 0 and z == 0:
                return
            self.write_param("AXIsX:PULSe {0}:AXIsZ:PULSe {1}".format(-x,-z))
            
        def gorel_yz(self,y,z):
            if y == 0 and z == 0:
                return
            self.write_param("AXIsY:PULSe {0}:AXIsZ:PULSe {1}".format(y,-z))
        
        def gorel_xyz(self,x,y,z):
            if x == 0 and y == 0 and z == 0:
                return
            self.write_param("AXIsX:PULSe {0}:AXIsY:PULSe {1}:AXIsZ:PULSe {2}".format(-x,y,-z))
            
        def axis(self,data):
            self.write_param("AXIs{0}".format(data))
            sleep(0.1)
        
        def set_xlimits(self, west, east):
            self.write_param("AXIsX:CCWSoftLimitPoint {0}:CWSoftLimitPoint {1}".format(west,east))
            sleep(0.1)
        
        def set_ylimits(self, south, north):
            self.write_param("AXIsY:CCWSoftLimitPoint {0}:CWSoftLimitPoint {1}".format(south,north))
            sleep(0.1)
        
        def set_zlimits(self, bottom, top):
            self.write_param("AXIsZ:CCWSoftLimitPoint {0}:CWSoftLimitPoint {1}".format(bottom,top))
            sleep(0.1)
        
        def set_xdist_per_pulse(self,dist = 1):  # dist in micrometer
            self.write_param("AXIsX:STANDARDresolution {0}".format(dist))
            sleep(0.1)
        
        def set_ydist_per_pulse(self,dist = 1):  # dist in micrometer
            self.write_param("AXIsY:STANDARDresolution {0}".format(dist))
            sleep(0.1)
        
        def set_zdist_per_pulse(self,dist = 1):  # dist in micrometer
            self.write_param("AXIsZ:STANDARDresolution {0}".format(dist))
            sleep(0.1)
        
        def set_unit(self,unit):
            self.write_param("AXIsX:UNIT {0}".format(unit))
            sleep(0.1)
            self.write_param("AXIsY:UNIT {0}".format(unit))
            sleep(0.1)
            self.write_param("AXIsZ:UNIT {0}".format(unit))
            sleep(0.1)
        
        def set_driver_division(self, xres=1, yres=1, zres=1):
            xres = get_valid_drive(xres)
            yres = get_valid_drive(yres)
            zres = get_valid_drive(zres)
            self.write_param("AXIsX:DriverDIVsion {0}: \
                              AXIsY:DriverDivision {1}; \
                              AxisZ:DirverDIVision {2}".format(xres,yres,zres))
            sleep(0.1)
        
        
        
        def set_xspeed(self,L=10,F=100,R=10,S=100):
            self.write_param("Lspeed0 {0}:Fspeed0 {1}: Rate0 {2}: Srate0{3}".format(L,F,R,S))
            sleep(0.2)
        
        def get_xspeed(self):
            return int(self.read_param('Fspeed0?'))
        
        def get_yspeed(self):
            return int(self.read_param('Fspeed1?'))
        
        def get_zspeed(self):
            return int(self.read_param('Fspeed2?'))
        
        def set_yspeed(self,L=10,F=100,R=10,S=100):
            self.write_param("Lspeed1 {0}:Fspeed1 {1}: Rate1 {2}: Srate1{3}".format(L,F,R,S))
            sleep(0.2)
        
        def set_zspeed(self,L=10,F=100,R=10,S=100):
            self.write_param("Lspeed2 {0}:Fspeed2 {1}: Rate2 {2}: Srate2{3}".format(L,F,R,S))
            sleep(0.2)
        
        def stop_xstage(self):
            self.write_param("AXIsX:STOP 1")
            self._x = int(self.xpos())
        
        def stop_ystage(self):
            self.write_param("AXIsY:STOP 1")
            self._y = int(self.ypos())
        
        def stop_zstage(self):
            self.write_param("AXIsZ:STOP 1")
            self._z = int(self.zpos())
        
        def stop_allstage(self):
            self.write_param("AXIsX:STOP 1:AXIsY:STOP 1:AXIsZ:STOP 1")
            self._x = int(self.xpos())
            self._y = int(self.ypos())
            self._z = int(self.zpos())
        
        def emergency_stop(self):
            self.write_param("AXIsX:STOP 0:AXIsY:STOP 0:AXIsZ:STOP 0")
            self._x = int(self.xpos())
            self._y = int(self.ypos())
            self._z = int(self.zpos())
        
        def get_xlimits(self):
            east = self.read_param("AXIsX:CWSoftLimitPoint?")
            west = self.read_param("AXIsX:CCWSoftLimitPoint?")
            return west,east
        
        def get_ylimits(self):
            north = self.read_param("AXIsY:CWSoftLimitPoint?")
            south = self.read_param("AXIsY:CCWSoftLimitPoint?")
            return south,north
        
        def get_zlimits(self):
            top = self.read_param("AXIsZ:CWSoftLimitPoint?")
            bottom = self.read_param("AXIsZ:CCWSoftLimitPoint?")
            return bottom,top
        
        def get_driver_division(self):
            xres = self.read_param("AXIsX:DRiverDIVision?")
            yres = self.read_param("AXIsY:DRiverDIVision?")
            zres = self.read_param("AXIsZ:DRiverDIVision?")
            #return iResol[xres],iResol[yres],iResol[zres]
            return xres,yres,zres
        
        def get_xdata(self):
            return self.read_param("AXIsX:DATA?")
    
        def get_ydata(self):
            return self.read_param("AXIsY:DATA?")
        
        def get_zdata(self):
            return self.read_param("AXIsZ:DATA?")
    
        def get_home_pos(self):
            hx = self.read_param("AXIsX:HOMEPosition?")
            hy = self.read_param("AXIsY:HOMEPosition?")
            hz = self.read_param("AXIsZ:HOMEPosition?")
            return hx,hy,hz
        
        def get_pos(self):
            return self.xpos(),self.ypos(),self.zpos()
            self._x = int(self.xpos())
            self._y = int(self.ypos())
            self._z = int(self.zpos())
        
        def get_dist_per_pulse(self):
            xres = self.read_param("AXIsX:RESOLUTion?")
            yres = self.read_param("AXIsY:RESOLUTion?")
            zres = self.read_param("AXIsZ:RESOLUTion?")
            return xres,yres,zres
        
        def get_dist_per_step(self):
            xres = self.read_param("AXIsX:STANDARDresolution?")
            yres = self.read_param("AXIsY:STANDARDresolution?")
            zres = self.read_param("AXIsZ:STANDARDresolution?")
            return xres,yres,zres
        
        def get_unit(self):
            ux = self.read_param("AXIsX:UNIT?")
            uy = self.read_param("AXIsY:UNIT?")
            uz = self.read_param("AXIsZ:UNIT?")
            return ux,uy,uz
        
        def get_xdir(self):
            return self.read_param("AXIsX:COURSE?")
        
        def get_ydir(self):
            return self.read_param("AXIsY:COURSE?")
        
        def get_zdir(self):
            return self.read_param("AXIsZ:COURSE?")
        
        def is_xdstop(self):
            return self.read_param("AXIsX:DISCONtinue?")
        
        def is_ydstop(self):
            return self.read_param("AXIsY:DISCONtinue?")
    
        def is_zdstop(self):
            return self.read_param("AXIsZ:DISCONtinue?")
        
        def xdriver_type(self):
            return self.read_param("AXIsX:DRiverTYPE?")
        
        def ydriver_type(self):
            return self.read_param("AXIsY:DRiverTYPE?")
        
        def zdriver_type(self):
            return self.read_param("AXIsZ:DRiverTYPE?")
        
        def know_xhome(self):
            return self.read_param("AXIsX:HOME?")
        
        def know_yhome(self):
            return self.read_param("AXIsY:HOME?")
        
        def know_zhome(self):
            return self.read_param("AXIsZ:HOME?")
        
        def mech_xlimit(self):
            return self.read_param("AXIsX:LIMIT?")
        
        def mech_ylimit(self):
            return self.read_param("AXIsY:LIMIT?")
        
        def mech_zlimit(self):
            return self.read_param("AXIsZ:LIMIT?")
        
        def is_xmoving(self):
            return int(self.read_param("AXIsX:MOTION?"))
        
        def is_ymoving(self):
            return int(self.read_param("AXIsY:MOTION?"))
        
        def is_zmoving(self):
            return int(self.read_param("AXIsZ:MOTION?"))
        
        def is_xready(self):
            return self.read_param("AXIsX:READY?")
        
        def is_yready(self):
            return self.read_param("AXIsY:READY?")
        
        def is_zready(self):
            return self.read_param("AXIsZ:READY?")
        
        def get_xsoftlimit(self):
            return self.read_param("AXIsX:SoftLIMIT?")
        
        def get_ysoftlimit(self):
            return self.read_param("AXIsY:SoftLIMIT?")
        
        def get_zsoftlimit(self):
            return self.read_param("AXIsZ:SoftLIMIT?")
        
        def get_inst_ID(self):
            return self.read_param("*IDN?")
        
"""
You can store 64 points and 8 program in the flash memory of the controller
Advantage of this is that the driving of the stage will be faster as the data transfer distance is small.
If there are any particular scan sequences that will be performed very often, those can be stored in the flash memory
"""
"""
Set 7th DIP switch of SW1 as ON to get error messages
E00 --> Stage not connected to command
E01 --> In motion, wait for the current operation to finish
E02 --> Stage is already at the limit at the beginning
E03 --> Emergency signal detected
E20 --> error in command syntax
E21 --> Error in sending delimiter (either not present, or wrong type)
E22 --> Parameter outside range
E40 --> Communication error
E41 --> Error writing in flash memory
"""
"""
Writing an example program into flash memory
DELPRG0  # Delete program number 0
wait 500 ms (check for '>' return which signals operation is complete)
SETPRG0,0,AXI1:PULS 1000 # step 0, program no 0
wait 30 ms (check for '>' return which signals operation is complete)
SETPRG0,1,LoopS 10 # step 1, program no 0
wait 30 ms (check for '>' return which signals operation is complete)
SETPRG0,2,AXI1:GO CW:DW #STEP 2 program no 0
wait 30 ms (check for '>' return which signals operation is complete)
SETPRG0,3,LoopE #  STEP 3 program no 0
wait 30 ms (check for '>' return which signals operation is complete)
SETPRG0,4,END # STEP 4 program no 0, as soon as END is detected, the whole program is written in flash memory
wait 500 ms(check for '>' return which signals operation is complete)
# NOTE: you cannot modify part of a program

# To start running a program
SELPRG <prg. no.>
PRG 0  # , sequentially run whole program,
PRG 1  # will start the next line of the program?
SELPRG? # request program number that is currently selected
PRG? # request statu of program driving, 0 --> program is driving in sequence
                                       # 1 --> Program is driving in step
                                       # 2 --> program has stopped
STOP # stop the driving program
"""