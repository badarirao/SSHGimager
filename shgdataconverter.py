# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 18:07:20 2022

@author: Badari
"""

import os
from numpy import array, savetxt, column_stack, ones
from SciFiReaders import NSIDReader
from sidpy.viz.dataset_viz import CurveVisualizer, ImageVisualizer
import sys

def Rotate180(arr):
    try:
        rows, columns = arr.shape
        Rarray = ones((rows,columns))
        for i in range(rows):
            for j in range(columns):
                Rarray[i,j] = arr[rows-i-1,columns-j-1]
        return Rarray
    except AttributeError:
        print("Invalid Array")
    except ValueError:
        print("Invalid Array shape")

if __name__ == "__main__":
    ispath = True
    argslist = sys.argv
    if ".py" in argslist[0]:
        argslist.pop(0)
    while True:
        if argslist == [] or ispath == False:
            pathname = input("Enter path:")
            pathname = os.path.normpath(pathname)
        else:
            pathname = argslist[0]
            pathname = os.path.normpath(pathname)
        if os.path.isdir(pathname):
            break
        elif pathname == "exit":
            sys.exit()
        else:
            ispath = False
    os.chdir(pathname)
    converted_path = ".\Converted"
    if not os.path.isdir(converted_path):
        os.mkdir(converted_path)
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith(".shg") or file.endswith(".shg1D") or file.endswith(".shg2D") or file.endswith(".shg3D"):
                try:
                    dataSet = NSIDReader(file).read()
                    dataSet[0].h5_dataset.file.close()
                    print("opened {}".format(file))
                except:
                    continue
                no_of_datasets = len(dataSet)
                for dset in dataSet:
                    if 'scan information' in dset.modality.lower():
                        info = dset.metadata['metadata']
                        if file.endswith(".shg"):
                            fname = file[:-4]
                        else:
                            fname = file[:-6]
                        with open('.\Converted\\'+fname+'_info.txt', 'w') as f:
                            for key, value in info.items():
                                if 'comment' in key.lower():
                                    f.write('{0}\n'.format(value))
                                else:
                                    f.write('{0}: {1}\n'.format(key, value))
                for dset in dataSet:
                    if 'scan information' not in dset.modality.lower():
                        arr = array(dset)
                        filename = '.\Converted\\' + \
                            fname + '_' + \
                            dset.title.split('/')[-1] + '.txt'
                        rfilename = '.\Converted\\' + \
                            "Rotated_" + fname + '_' + \
                            dset.title.split('/')[-1] + '.txt'
                        if info['Dimension'] == 1:
                            xarr = array(dset.aAxis)
                            whole_data = column_stack((xarr, arr))
                            savetxt(filename, whole_data,
                                    fmt='%g', delimiter='\t')
                            if 'shg' in dset.title.lower():
                                try:
                                    CurveVisualizer(dset).fig.savefig(
                                        filename[:-4]+'.png')
                                except:
                                    pass
                        elif info['Dimension'] == 2:
                            savetxt(filename, arr.T, fmt='%g', delimiter='\t')
                            savetxt(rfilename,Rotate180(arr.T),fmt='%g', delimiter='\t')
                            if 'shg' in dset.title.lower():
                                try:
                                    ImageVisualizer(dset).fig.savefig(
                                        filename[:-4]+'.png')
                                except:
                                    pass
                        elif info['Dimension'] == 3:
                            with open(filename, 'w') as f:
                                for i in range(arr.shape[0]):
                                    arr2D = arr[i, :, :]
                                    savetxt(f, arr2D.T,
                                            fmt='%g', delimiter='\t')
                                    f.write('\n\n')
                            with open(rfilename, 'w') as f:
                                for i in range(arr.shape[0]):
                                    arr2D = arr[i, :, :]
                                    savetxt(f, Rotate180(arr2D.T),
                                            fmt='%g', delimiter='\t')
                                    f.write('\n\n')
