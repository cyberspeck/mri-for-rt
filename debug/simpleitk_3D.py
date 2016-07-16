# -*- coding: utf-8 -*-
"""
Created on Fri Jul 15 10:22:52 2016

@author: david
based on:
https://pyscience.wordpress.com/2014/10/19/image-segmentation-with-python-and-sitk/
"""

import os
import numpy as np
import SimpleITK as sitk
import matplotlib.pyplot as plt
get_ipython().magic('pylab inline')



def sitk_show(img, title=None, margin=0.05, dpi=40, scale=2,
              interpolation='nearest'):
    """
    scale is a scaling factor for the shown image
    """
    nda = sitk.GetArrayFromImage(img)
    spacing = img.GetSpacing()
    figsize = (scale + margin) * nda.shape[0] / dpi, (scale + margin) * nda.shape[1] / dpi
    extent = (0, nda.shape[1]*spacing[1], nda.shape[0]*spacing[0], 0)
    fig = plt.figure(figsize=figsize, dpi=dpi)
    ax = fig.add_axes([margin, margin, scale - 2*margin, scale - 2*margin])

    plt.set_cmap("gray")
    ax.imshow(nda,extent=extent,interpolation=interpolation)
    
    if title:
        plt.title(title)
    
    plt.show()

def sitk_mask(img0, mask):
    img0A = sitk.GetArrayFromImage(img0)
    maskA = sitk.GetArrayFromImage(mask)

    imgMaskedA= img0A*maskA
    
    return sitk.GetImageFromArray(imgMaskedA)

pathCT = "../data/cropped_CT/"
pathMR = "../data/cropped_MR-d/"

idxSlice = 20

labelPlastic = 2
labelFilling = 1


reader = sitk.ImageSeriesReader()
filenamesCT = reader.GetGDCMSeriesFileNames(pathCT)
reader.SetFileNames(filenamesCT)
imgOriginalCT = reader.Execute()

filenamesMR = reader.GetGDCMSeriesFileNames(pathMR)
reader.SetFileNames(filenamesMR)
imgOriginalMR = reader.Execute()


# imgOriginal_slice = imgOriginal[:,:,idxSlice]


sitk_show(imgOriginalCT[:,:,idxSlice], title="CT, original")
sitk_show(imgOriginalMR[:,:,idxSlice], title="MR, original")

imgSmoothCT = sitk.CurvatureFlow(image1=imgOriginalCT,
                                    timeStep=0.125,
                                    numberOfIterations=5)

imgSmoothMR = sitk.CurvatureFlow(image1=imgOriginalMR,
                                    timeStep=0.125,
                                    numberOfIterations=5)
                                    
sitk_show(imgSmoothCT[:,:,idxSlice], title="CT, denoised")
sitk_show(imgSmoothMR[:,:,idxSlice], title="MR, denoised")



seedFillingCT = [(14,14,idxSlice)]

# https://itk.org/SimpleITKDoxygen/html/classitk_1_1simple_1_1ConnectedThresholdImageFilter.html
'''
imgFillingCT = sitk.ConnectedThreshold(image1=imgSmoothCT, 
                                              seedList=seedFillingCT, 
                                              lower=00, 
                                              upper=110,
                                              replaceValue=labelFilling)
'''

# https://itk.org/SimpleITKDoxygen/html/classitk_1_1simple_1_1NeighborhoodConnectedImageFilter.html
maskFillingCT = sitk.ConfidenceConnected(image1=imgSmoothCT, 
                                              seedList=seedFillingCT,
                                              multiplier=2.5,
                                              numberOfIterations=10,
                                              initialNeighborhoodRadius=2,
                                              #lower=00, 
                                              #upper=110,
                                              replaceValue=labelFilling)

sitk_show(imgSmoothCT[:,:,idxSlice], title="CT, denoised")
sitk_show(maskFillingCT[:,:,idxSlice], title="CT, denoised, filling mask")

imgFillingCT = sitk_mask(imgSmoothCT, maskFillingCT)

sitk_show(imgFillingCT[:,:,idxSlice], title="CT, denoised, filling")


# for shift in range(-10,10):
#    sitk_show(imgFillingCT[:,:,idxSlice+shift])
# for tiled view??:
# sitk_show(sitk.Tile(imgFillingCT[:,:,idxSlice],
#                    imgSmoothCT[:,:,idxSlice], (2,1,0)))

