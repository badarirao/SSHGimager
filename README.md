# SSHGimager

SSHGimager is a pyqt5 based gui program for scanning SHG microscopy of ferroelectric single crystals and thin films. It is designed to work with a custom built instrument by Prof. Hiroko Yokota. The python code to control the instrument and plot the images was written by Dr. Badari Narayana Rao.
If you are interested in running the program, and need help, feel free to email me at badari.rao@gmail.com.

## Software appearance
![SHG demo](https://user-images.githubusercontent.com/47620203/234454770-8aed39e0-49dd-44ce-891b-bc1049558ce2.jpg)

## About the instrument

The instrument uses a tunable laser and can measure in both transmission and reflection geometry. The sample can be moved in x, y and z direction using stepper motors. The laser position can also be adjusted using x & y galvanomirrors, but only for the transmission mode. There is a CCD camera to see and adjust the sample position. The instrument also has options for controlling the sample temperature, and applying electric field in-situ.

## About the software

The software allows for individual controlling of the x,y,and z stages needed during initial positioning. There are two modes of scanning for transmission mode: 

- Fast scanning using galvanomirrors, but limited to smaller area.
- Slow scanning using stepper motors (larger area can be scanned).

For reflection mode, only slow scanning using stepper motors is available (mainly due to hardware constraints).

The stepper motors are controlled using serial ports, whereas the galvanomirrors are controlled by applying the necessary voltage through an NI DAQ (NI USB 6211 OEM).

The SHG signal is detected using a photodetector, whose signals are measured as counts using the counter of the DAQ. A reference detector is also used to monitor the incident intensity of the laser.

## Software capabilities

The software has the following capabilities:

### Scan modes

The user can scan in transmission and reflection geometry. Transmission mode is used for single crystals whereas reflection mode is used for thin films.

The user can also choose four types of scans namely, trace, retrace, trace & retrace, alternate trace and retrace. The trace & retrace option saves two images corresponding to the trace and retrace images collected simultaneously. These four modes were mainly provided to study the effect of image shift due to backlash error of the stepper motors and galvanomirror, and the user can choose the mode that best suits him.

### Scan types

The software can perform 1-D scan in x, y, and z directions, 2-D scan in xy, xz, and yz directions, and also 3-D scan in the x,y,z direction using the stepper motors.

The software can also perform 2-D scan in xy direction using galvanomirror, and a hybrid 3-D scan involving xy scans with galvanomirror and z movement with stepper motor. A slider is provided to view the 3D data as different 2D slices.

### Scan settings and image scaling

The user can set scan speed by controlling the setting parameters of stepper motor and the galvanomirror, which can be modified by the user.

The user can also calibrate the image using a known reference and set the calibration values in the setting so that the new images of unknown images will be shown in correct scale.

The scan settings can be saved, and loaded. Another option to set default scan settings is also provided.

In addition, the image scanning parameters of the sample is stored as .prm file, which stores the x,y,z position and scan area of the sample being scanned. This is useful if the user has to switch off the instrument, and resume his scans the next day, with the sample not removed from the instrument.

### Image settings

User can modify the color codes of the active image being displayed by right clicking on the right side of the plot. You can also select and zoom a particular region of interest. In addition, in the right side, where saved images can be loaded, you can use the roi tool to plot the 1-D profile of the selected area.

### Data storage

The software stores the collected images in a HDF5 format. The information about scan conditions etc. that is written in the comments section is stored as metadata. The files have different extensions depending on the scan type: .shg1D for 1D scans, .shg2D for 2D scans and .shg3D for 3D scans. Each scan stores three sets of data, corresponding to the raw signal from photodetector, the reference signal, and the processed signal which normalizes the raw signal with the reference signal. Each of these can be viewed separately in the software. The shgdataconverter.py program can convert all the files in the specified folder into text format for further analysis. However, currently, this conversion program has to be run separately from command line, and no gui is available. The software can also open old HDF5 files for later viewing. The software can also run in PC where instruments are not connected, to view the collected SHG data.

## Software installation

Currently, the program is just written as a project, and has not been packaged. Anyone is free to clone the project and run the program.

There are some things to be considered to successfully be able to run the software in a new PC. A detailed information will be updated later.
Following is a brief information that gives a rough idea on what is needed to run the software.

- Install the required python packages and NI drivers. (requirements.txt will be uploaded later. If you need help right now, contact the author).
- The software searches for an `address.txt` file that needs to be located in the same folder as the python program, which stores the location of the instrument setting files, and the path of last used directory to save images.
- The software also needs the galvanomirror and stage settings file containing the necessary instrument parameters, and named as `SHG_default_Settings.txt`.

To run the program, simply execute the `scan.py` file with python.
