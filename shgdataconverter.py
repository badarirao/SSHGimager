# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 18:07:20 2022

@author: Badari
"""

import os
from numpy import array, savetxt, column_stack
from SciFiReaders import NSIDReader
from sidpy.viz.dataset_viz import CurveVisualizer, ImageVisualizer
import sys

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
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith(".shg"):
                try:
                    dataSet = NSIDReader(file).read()
                except:
                    continue
                no_of_datasets = len(dataSet)
                for dset in dataSet:
                    if dset.modality == 'Scan Information':
                        info = dset.metadata['metadata']
                        with open(info['File Name']+'_info.txt','w') as f:
                            for key,value in info.items():
                                if key == 'Comments':
                                    f.write('{0}\n'.format(value))
                                else:
                                    f.write('{0}: {1}\n'.format(key,value))
                for dset in dataSet:
                    if dset.modality != 'Scan Information':
                        arr = array(dset)
                        filename = info['File Name'] + '_' + dset.title.split('/')[-1] + '.txt'
                        if info['Dimension'] == 1:
                            xarr = array(dset.aAxis)
                            whole_data = column_stack((xarr,arr))
                            savetxt(filename,whole_data,fmt='%g',delimiter='\t')
                            if 'processed' in dset.title:
                                try:
                                    CurveVisualizer(dataSet[0]).fig.savefig(filename[:-4]+'.png')
                                except:
                                    pass
                        elif info['Dimension'] == 2:
                            savetxt(filename, arr.T, fmt='%g',delimiter='\t')
                            if 'processed' in dset.title:
                                try:
                                    ImageVisualizer(dataSet[0]).fig.savefig(filename[:-4]+'.png')
                                except:
                                    pass
                        elif info['Dimension'] == 3:
                            for i in range(arr.shape[0]):
                                arr2D = arr[i,:,:]
                                savetxt(filename,arr2D.T,fmt='%g',delimiter='\t')
                                f.write(b'\n\n')

                            
            