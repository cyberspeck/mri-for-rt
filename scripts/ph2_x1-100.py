#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Jul 17 15:17:57 2016
@author: davidblacher

plt.clf()

plt.xlim((0,1)
plt.yscale('log')

plt.legend(loc='center right')
plt.legend(loc='lower right')
plt.legend(loc='upper right')
plt.legend(loc='lower left')

plt.xlabel(u"guess [%]")  
plt.ylabel(u"DC")

plt.ylabel(u"warp [mm]")
plt.xlabel(u"slice")

plt.tight_layout()

# print entire array:
np.set_printoptions(threshold='nan')
"""

import FunITK as fun
from FunITK import Volume
import datetime
import numpy as np
import matplotlib.pyplot as plt
import os

idxSlice = 200
ph2_CT = Volume(path="../data/phantom2/CT_x1", method="CT",
                resample=1, ref=idxSlice)
ph2_CT_x4 = Volume(path="../data/phantom2/CT_x4", method="CT",
                   resample=4, ref=idxSlice)
ph2_CT_x9 = Volume(path="../data/phantom2/CT_x9", method="CT",
                   resample=9, ref=idxSlice)
ph2_CT_x25 = Volume(path="../data/phantom2/CT_x25", method="CT",
                    resample=25, ref=idxSlice)
ph2_CT_x100 = Volume(path="../data/phantom2/CT_x100", method="CT",
                     resample=100, ref=idxSlice)

ph2_MR = Volume(path="../data/phantom2/MR_x1", method="MR",
                resample=1, ref=idxSlice)
ph2_MR_x4 = Volume(path="../data/phantom2/MR_x4", method="MR",
                   resample=4, ref=idxSlice)
ph2_MR_x9 = Volume(path="../data/phantom2/MR_x9", method="MR",
                   resample=9, ref=idxSlice)
ph2_MR_x25 = Volume(path="../data/phantom2/MR_x25", method="MR",
                    resample=25, ref=idxSlice)
ph2_MR_x100 = Volume(path="../data/phantom2/MR_x100", method="MR",
                     resample=100, ref=idxSlice)

vol_list = [[ph2_CT, ph2_CT_x4, ph2_CT_x9, ph2_CT_x25, ph2_CT_x100],
            [ph2_MR, ph2_MR_x4, ph2_MR_x9, ph2_MR_x25, ph2_MR_x100]]
modality, sets = np.shape(vol_list)

length = ph2_CT_x100.zSize
spacing = ph2_CT_x100.zSpace
sliceNumbers = np.arange(length, dtype=int)

# for data centered around iso-centre, this is real x-axis:
iso = 183
dist = ( (sliceNumbers - iso ) ).round(2)


warp_simple = np.zeros((sets, length, 2))
warp_iter = np.zeros((sets, length, 2))
warpMagnitude_simple = np.zeros((sets, length, 1))
warpMagnitude_iter = np.zeros((sets, length, 1))
lows_CT = np.zeros((sets, 2))
radii_CT = np.zeros((sets, 2))
lows_MR = np.zeros((sets, 4))
radii_MR = np.zeros((sets, 4))

# 2 DC for CT, 3 DC for MR (2 using MR.centroid, 1 using CT.centroid!)
DC_CT = np.zeros((sets, length, 2))
DC_CT_average = np.zeros((sets, 2))
DC_MR = np.zeros((sets, length, 4))
DC_MR_average = np.zeros((sets, 4))

#fig = plt.figure()
#plt.ylim(ymin=0.35, ymax=.7)
#plt.xlim(xmin=(3.5-.1), xmax=(5.5+.1))
#plt.xlim(xmin=(1.5-.1), xmax=(4.5+.1))
#plt.ylabel(u"DC")
#plt.xlabel(u"radius [mm]")
#plt.legend(('x1', 'x4', 'x9', 'x25', 'x100'),loc=0)

for i in range(sets): 
    vol_list[0][i].getCentroid()
    CT_DC_simple = vol_list[0][i].getDice()
    CT_DC_simple_average = vol_list[0][i].diceAverage
    CT_lower_simple = vol_list[0][i].lower
    CT_radius_simple = vol_list[0][i].bestRadius
    
    vol_list[1][i].getCentroid()
    MR_DC_simple = vol_list[1][i].getDice()
    MR_DC_simple_average = vol_list[1][i].diceAverage
    MR_lower_simple = vol_list[1][i].lower
    MR_radius_simple = vol_list[1][i].bestRadius
    vol_list[1][i].getMask()
    MR_DC_simple_CT_COM = vol_list[1][i].getDice(centroid=vol_list[0][i].centroid)
    MR_DC_simple_CT_COM_average = vol_list[1][i].diceAverage
    MR_lower_simple_CT_COM = vol_list[1][i].lower
    MR_radius_simple_CT_COM = vol_list[1][i].bestRadius
    # this calculates the coordinate difference of MR.centroid relative to CT.centroid
    warp_simple[i] = fun.sitk_coordShift(vol_list[0][i].centroid, vol_list[1][i].centroid)
    # this calculates the norm (=absolute distance) between the centroids in each slice
    warpMagnitude_simple[i] = fun.sitk_coordDist(warp_simple[i])
    

    vol_list[0][i].getCentroid(percentLimit='auto', iterations=5, top=0.20)
    CT_DC_iter = vol_list[0][i].dice
    CT_DC_iter_average = vol_list[0][i].diceAverage
    CT_lower_iter = vol_list[0][i].lower
    CT_radius_iter = vol_list[0][i].bestRadius
    
    vol_list[1][i].getCentroid(percentLimit='auto', iterations=6, top=0.20)
    MR_DC_iter = vol_list[1][i].dice
    MR_DC_iter_average = vol_list[1][i].diceAverage
    MR_lower_iter = vol_list[1][i].lower
    MR_radius_iter = vol_list[1][i].bestRadius
    vol_list[1][i].getMask()
    MR_DC_iter_CT_COM = vol_list[1][i].getDice(centroid=vol_list[0][i].centroid)
    MR_DC_iter_CT_COM_average = vol_list[1][i].diceAverage
    MR_lower_iter_CT_COM = vol_list[1][i].lower
    MR_radius_iter_CT_COM = vol_list[1][i].bestRadius
    
    # this calculates the coordinate difference of MR.centroid relative to CT.centroid
    warp_iter[i] = fun.sitk_coordShift(vol_list[0][i].centroid, vol_list[1][i].centroid)
    # this calculates the norm (=absolute distance) between the centroids in each slice
    warpMagnitude_iter[i] = fun.sitk_coordDist(warp_iter[i])
    
    
    DC_CT[i] = np.column_stack((CT_DC_simple,CT_DC_iter))
    DC_CT_average[i] = CT_DC_simple_average,CT_DC_iter_average
    
    DC_MR[i] = np.column_stack((MR_DC_simple, MR_DC_iter,
                                MR_DC_simple_CT_COM, MR_DC_iter_CT_COM))
    DC_MR_average[i] = (MR_DC_simple_average, MR_DC_iter_average,
                        MR_DC_simple_CT_COM_average, MR_DC_iter_CT_COM_average)
    lows_CT[i] = CT_lower_simple, CT_lower_iter
    lows_MR[i] = MR_lower_simple, MR_lower_iter, MR_lower_simple_CT_COM, MR_lower_iter_CT_COM
    radii_CT[i] = CT_radius_simple, CT_radius_iter
    radii_MR[i] = MR_radius_simple, MR_radius_iter, MR_radius_simple_CT_COM, MR_radius_iter_CT_COM

#plt.legend(('x1','x4','x9','x25','x100'), loc='upper right')

'''
# brightness
fig = plt.figure()
#plt.ylim(ymin=-2.1, ymax=.5)
plt.xlim(xmin=dist[0], xmax=dist[-1])
plt.plot(dist, ph2_MR_x100.meanBrightness)
plt.plot(dist, ph2_MR_x100.maxBrightness)
plt.legend(('mean', 'max'),loc=0)
plt.ylabel(u"pixel value")
plt.xlabel(u"z-axis [mm]")
#plt.title('Economic Cost over Time')
#plt.show()

# brightness
fig = plt.figure()
#plt.ylim(ymin=-2.1, ymax=.5)
plt.xlim(xmin=dist[0], xmax=dist[-1])
plt.plot(dist, ph2_CT_x100.meanBrightness)
plt.plot(dist, ph2_CT_x100.maxBrightness)
plt.legend(('mean', 'max'),loc=0)
plt.ylabel(u"pixel value")
plt.xlabel(u"z-axis [mm]")
#plt.title('Economic Cost over Time')
#plt.show()

# COM iter
plt.ylim(ymin=0.3, ymax=1)
plt.ylim(ymin=0.85, ymax=1)
plt.xlim(xmin=0, xmax=100)
plt.xlim(xmin=0, xmax=26)
plt.ylabel(u"average DC")
plt.xlabel(u"used pixels [%]")

# x and y warp
fig = plt.figure()
#plt.ylim(ymin=-2.1, ymax=.5)
plt.ylim(ymin=warp_simple[i].min()-0.1, ymax=warp_simple[i].max()+0.1)
plt.xlim(xmin=dist[0], xmax=dist[-1])
plt.plot(dist, warp_simple[i])
plt.legend(('x-shift', 'y-shift'),loc=3)
plt.ylabel(u"warp [mm]")
plt.xlabel(u"z-axis [mm]")
#plt.title('Economic Cost over Time')
#plt.show()


# warpMagnitude simple
fig = plt.figure()
plt.ylim(ymin=warpMagnitude_simple[i].min()-0.1, ymax=warpMagnitude_simple[i].max()+0.1)
plt.xlim(xmin=dist[0], xmax=dist[-1])
plt.plot(dist, warpMagnitude_simple[i])
#plt.legend(('warpMagnitude'),loc=0)
plt.ylabel(u"warpMagnitude [mm]")
plt.xlabel(u"z-axis [mm]")
# warpMagnitude iter
fig = plt.figure()
plt.ylim(ymin=-1.1, ymax=warpMagnitude_iter[0].max()+0.1)
plt.xlim(xmin=dist[0], xmax=dist[-1])
plt.plot(dist, warpMagnitude_iter[0],'r')
plt.plot(dist, warpMagnitude_iter[4],'b')
plt.legend(('x1','x100'),loc=4)
plt.ylabel(u"warpMagnitude [mm]")
plt.xlabel(u"z-axis [mm]")



# DC for CT and MRI and MRI (CT COM) iter
fig = plt.figure()
plt.ylim(ymin=0.5, ymax=1.005)
plt.xlim(xmin=dist[0], xmax=dist[-1])
plt.plot(dist, DC_CT[i,:,1])
plt.plot(dist, DC_MR[i,:,1])
plt.plot(dist, DC_MR[i,:,3])
plt.legend(('CT', 'MR', 'MR (CT COM)'),loc=0)
plt.ylabel(u"DC")
plt.xlabel(u"z-axis [mm]")

'''



# http://stackoverflow.com/questions/16621351/how-to-use-python-numpy-savetxt-to-write-strings-and-float-number-to-an-ascii-fi
now = datetime.datetime.now()

COLUMNS  = ('sliceNo dist warp_x  warp_y  warpMagnitude  DC_CT  DC_MR '
            ' DC_MR_CT-COM  warp_x*  warp_y*  warpMagnitude*   DC_CT*'
            ' DC_MR*  DC_MR_CT-COM*')
for i in range(sets):
    DATA = np.column_stack((sliceNumbers.astype(str),
                            dist.astype(str),
                            
                            warp_simple[i].round(4).astype(str),
                            warpMagnitude_simple[i].round(4).astype(str),
                            DC_CT[i,:,0].round(4).astype(str),
                            DC_MR[i,:,0].round(4).astype(str),
                            DC_MR[i,:,2].round(4).astype(str),
                            
                            warp_iter[i].round(4).astype(str),
                            warpMagnitude_iter[i].round(4).astype(str),
                            DC_CT[i,:,1].round(4).astype(str),
                            DC_MR[i,:,1].round(4).astype(str),
                            DC_MR[i,:,3].round(4).astype(str)))
 #   text = np.row_stack((NAMES, DATA))
    head0 = ("{}_x{}\n path: {}\n thresholds:\n lower (simple): {},\n"
    " lower (iter): {}\n upper: {}\n DC-average (simple): {} (bestRadius: {})\n"
    " DC-average (iter): {} (bestRadius: {})\n".format(vol_list[0][i].method,
    vol_list[0][i].resample, vol_list[0][i].path, lows_CT[i][0], lows_CT[i][1],
    vol_list[0][i].upper, DC_CT_average[i][0], radii_CT[i][0],
    DC_CT_average[i][1], radii_CT[i][1]))
    
    head1 = ("{}_x{}\n path: {}\n thresholds:\n lower (simple): {},\n"
    " lower (iter): {}\n lower (simple_CT-COM): {}\n lower (iter_CT-COM): {}\n"
    " upper: {}\n DC-average (simple): {} (bestRadius: {})\n DC-average (iter): {}"
    " (bestRadius: {})\n DC-average (CT-COM, simple): {} (bestRadius: {})\n"
    " DC-average (CT-COM, iter): {} (bestRadius: {})".format(vol_list[1][i].method,
     vol_list[1][i].resample, vol_list[1][i].path, lows_MR[i][0], lows_MR[i][1],
     lows_MR[i][2], lows_MR[i][3], vol_list[1][i].upper, DC_MR_average[i][0],
     radii_MR[i][0], DC_MR_average[i][1], radii_MR[i][1], DC_MR_average[i][2],
     radii_MR[i][2], DC_MR_average[i][3], radii_MR[i][3]))

    head = str(now) + '\n'+ head0 + head1 + '\n' + COLUMNS
    np.savetxt('../data/output_txt/phantom2_out_txt/CT-MR_x{}_{}_{}.txt'
               .format(vol_list[0][i].resample, now.date(), now.time()), DATA,
               delimiter="   &  ", header=head, comments="# ", fmt='%3s')



for i in range(sets):

# creates mask (pixel values either 0 or 1)
#    vol_list[0][i].getMask()
# creates CT.masked using CT.mask,
# but assigns each slice the centroid distance*1000*spacing as pixel value
    vol_list[0][0].applyMask(replaceArray=warp_simple[i][:,0])
# exports 3D image as .mha file
    fun.sitk_write(vol_list[0][0].masked, "../data/output_img/ph2_out_img/mha_files",
                   "ph2_out_x{}_warpX_simple.mha".format(vol_list[0][i].resample))
    vol_list[0][0].applyMask(replaceArray=warp_simple[i][:,1])
    fun.sitk_write(vol_list[0][0].masked, "../data/output_img/ph2_out_img/mha_files",
                   "ph2_out_x{}_warpY_simple.mha".format(vol_list[0][i].resample))

    vol_list[0][0].applyMask(replaceArray=warp_iter[i][:,0])
    fun.sitk_write(vol_list[0][0].masked, "../data/output_img/ph2_out_img/mha_files",
                   "ph2_out_x{}_warpX_iter.mha".format(vol_list[0][i].resample))
    vol_list[0][0].applyMask(replaceArray=warp_iter[i][:,1])
    fun.sitk_write(vol_list[0][0].masked, "../data/output_img/ph2_out_img/mha_files",
                   "ph2_out_x{}_warpY_iter.mha".format(vol_list[0][i].resample))

    vol_list[0][0].applyMask(replaceArray=warpMagnitude_simple[i])
    fun.sitk_write(vol_list[0][0].masked, "../data/output_img/ph2_out_img/mha_files",
                   "ph2_out_x{}_warpMagnitude_simple.mha".format(vol_list[0][i].resample))

    vol_list[0][0].applyMask(replaceArray=warpMagnitude_iter[i])
    fun.sitk_write(vol_list[0][0].masked, "../data/output_img/ph2_out_img/mha_files",
                   "ph2_out_x{}_warpMagnitude_iter.mha".format(vol_list[0][i].resample))
    
    vol_list[0][0].applyMask(replaceArray=DC_MR[i,:,0])
    fun.sitk_write(vol_list[0][0].masked, "../data/output_img/ph2_out_img/mha_files",
                   "ph2_out_x{}_DC_MR_simple.mha".format(vol_list[0][i].resample))
    
    vol_list[0][0].applyMask(replaceArray=DC_MR[i,:,2])
    fun.sitk_write(vol_list[0][0].masked, "../data/output_img/ph2_out_img/mha_files",
                   "ph2_out_x{}_DC_MR_CT-COM_simple.mha".format(vol_list[0][i].resample))


    vol_list[0][0].applyMask(replaceArray=DC_MR[i,:,1])
    fun.sitk_write(vol_list[0][0].masked, "../data/output_img/ph2_out_img/mha_files",
                   "ph2_out_x{}_DC_MR_iter.mha".format(vol_list[0][i].resample))
    
    vol_list[0][0].applyMask(replaceArray=DC_MR[i,:,3])
    fun.sitk_write(vol_list[0][0].masked, "../data/output_img/ph2_out_img/mha_files",
                   "ph2_out_x{}_DC_MR_CT-COM_iter.mha".format(vol_list[0][i].resample))


# instead of opening the created file manually, you can use this lines in
# the IPython console to start 3D Slicer and open it automatically:
# %env SITK_SHOW_COMMAND /home/david/Downloads/Slicer-4.5.0-1-linux-amd64/Slicer
# sitk.Show(CT.masked)