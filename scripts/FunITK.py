# -*- coding: utf-8 -*-
"""
Created on Sat Jul 16 22:45:11 2016

Volume class
custom FUNcitons using SimpleITK

@author: david

works best with cropped CT and MRI images (showing only one rod),
both Volumes should have the same PixelSpacing
 and x and y PixelSpacing shoult be equal
All diagrams are in pixels, not in real length units,
 only sitk_write() creates .mha file with pixel values corresponding
 to distortion in pixel distance * PixelSpacing

based on:
https://pyscience.wordpress.com/2014/10/19/image-segmentation-with-python-and-SimpleITK/
http://insightsoftwareconsortium.github.io/SimpleITK-Notebooks/03_Image_Details.html
http://stackoverflow.com/questions/18435003/ndimages-center-of-mass-to-calculate-the-position-of-a-gaussian-peak
http://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.ndimage.measurements.center_of_mass.html

install SimpleITK
https://itk.org/Wiki/SimpleITK/GettingStarted#Generic_Distribution
"""

# important to remember:
# sitk.Image saves Volume like this (x,y,z)
# array returned by sitk.GetArrayFromImage(Image)
# is transposed: (z,y,x)

import numpy as np
from scipy import ndimage
import SimpleITK as sitk
import matplotlib.pyplot as plt
import os
from skimage.draw import circle


class Volume:
    '''
    Create a Volume (SimpleITK.Image with convenient properties and functions)
    recommended use:
    create new Volume (optional use denoise=True)
    Volume.getThresholds()

    Parameters
    ----------
    path : string_like
        directory containing DICOM data
    method : string_like, recommended
        either "CT or "MR", used to make correct calculations
    radius: double, optional
        overrides radius value (default CT:4mm, MR:2mm)
    denoise : bool, optional
        If true, the imported data will be denoised using
        SimpleITK.CurvatureFlow(image1=self.img,
                                timeStep=0.125,
                                numberOfIterations=5)
    ref : int, optional
        slice used to make calculations (idealy isocenter) and plotted
    info : string, optional
        additional information about imported data, becomes part of title
    seeds : array_like (int,int,int), optional
        array that describes point inside rod, used for segmentation
    spacing: double, optional
        by default SitpleITK.img.GetSpacing is used to find relation of pixels
        to real length (in mm)
    '''
    def __init__(self, path=None, method=None, denoise=False, ref=0,
                 info=False, seeds=None, radius=0, spacing=0):
        if(path is None):
            print("Error: no path given!")
        else:
            self.path = path
            self.method = method
            self.denoise = denoise
            self.ref = ref
            self.info = info
            self.seeds = seeds
            self.centroid = False
            self.mask = False
            self.masked = False
            self.title = method
            self.radius = radius
            self.lower = False
            self.upper = False

            print("\n Import DICOM Files from: ", path)
            self.img = sitk_read(path, self.denoise)

            if (self.img and self.denoise):
                a = self.title
                self.title = a + " denoised"

            if info is True:
                a = self.title
                self.title = a + ", " + info

            self.xSize, self.ySize, self.zSize = self.img.GetSize()

            if spacing == 0:
                self.xSpace, self.ySpace, self.zSpace = self.img.GetSpacing()

    def show(self, pixel=False, interpolation=None, ref=None):
        '''
        plots ref slice of Volume

        Parameters
        ----------
        pixel: bool, optional
            if True, changes axis from mm to pixels
        interpolation: "string", optional, default: 'nearest'
            using build-in interpolation of matplotlib.pyplot.imshow
            Acceptable values are 'none', 'nearest', 'bilinear', 'bicubic',
            'spline16', 'spline36', 'hanning', 'hamming', 'hermite', 'kaiser',
            'quadric', 'catrom', 'gaussian', 'bessel', 'mitchell', 'sinc',
            'lanczos'
        ref: int, optional
            slice to be plotted instead of self.ref (default: 0)
        '''

        if ref is None:
            ref = self.ref

        if interpolation is None:
            a = 'nearest'

        if pixel is False:
            extent = (-self.xSpace/2, self.xSize*self.xSpace + self.xSpace/2, self.ySize*self.ySpace + self.ySpace/2, -self.ySpace/2)
# The location, in data-coordinates, of the lower-left and upper-right corners
# (left, right, bottom, top)
        else:
            extent = None

        sitk_show(img=self.img, ref=ref, extent=extent, title=self.title, interpolation=a)

    def showSeed(self, title=None, pixel=False, interpolation='nearest'):
        '''
        plots slice conataining seed
        '''
        if self.seeds is False:
            print("Volume has no seeds yet.")
            return None

        extent = None

        if pixel is False:
            extent = (-self.xSpace/2, self.xSize*self.xSpace + self.xSpace/2, self.ySize*self.ySpace + self.ySpace/2, -self.ySpace/2)

        x, y, z = self.seeds[0]
        arr = sitk.GetArrayFromImage(self.img)
        plt.set_cmap("gray")
        if title is None:
            plt.title(self.title + ", seed")

        plt.imshow(arr[z, :, :], extent=extent, interpolation=interpolation)
        plt.scatter(x, y)
        plt.show()
        
    def getThresholds(self, pixelNumber=0, scale=1):
        '''
        calculates threshold based on number of pixels representing rod
        if no pixelNumber is given, self.radius is used to get estimated
        pixelNumber

        approx. number of pixels being part of rod:
        pn = realRadius^2 * pi / pixelSpacing^2

        Parameters
        ----------
        pixelNumber: int, optional
            if 0, uses self.radis to calculate pixelnumber
            if self.radius also 0, uses self.method instead (CT: 4mm, MR: 2mm)
        scale: double, optional
            factor altering pixelNumber

        Returns
        -------
        Lower and upper threshold value: (double, double)
        '''

        if pixelNumber == 0:
            if self.radius != 0:
                realRadius = self.radius
            else:
                if self.method == "CT":
                    realRadius = 4
                if self.method == "MR":
                    realRadius = 2
                if self.method != "MR" and self.method != "CT":
                    print("method is unknown, please set pixelNumber!")
                    return None
            pixelNumber = np.power(realRadius, 2)*np.pi/np.power(self.xSpace, 2)*scale

        pn = pixelNumber
        arr = sitk.GetArrayFromImage(self.img)
        self.upper = np.double(arr.max())

        hist, bins = np.histogram(arr[self.ref, :, :].ravel(), bins=100)
        self.lower = np.double(bins[np.argmax((np.cumsum(hist[::-1]) < pn)[::-1])])
        print("number of pixels (pn): {}\n lower: {}\n upper: {}".format(pn, self.lower, self.upper))

        return (self.lower, self.upper)

    def getCentroid(self, show=False, percentLimit=False, threshold=False,
                    pixelNumber=0, scale=1):
        '''
        Either used with percentLimit = within (0,1) or "auto"
        or with threshold = number or "auto"
        '''

        if (threshold is False and percentLimit is False) or (threshold is True and percentLimit is True):
            print("Please use either percentLimit or threshold!")
            return None

        if percentLimit == "auto" and threshold is False:
#            if self.mask is False:
#                print("For this method a mask is required! Use Volume.applyMask() first!")
#                return None
            # calculates 13 centroids with different percentLimits
            # gets dice coefficient for each centroid percentLimit combination
            # returns best result
            limits = np.linspace(0.65, 0.95, num=13)
            centroidScore = np.zeros(len(limits))
            centroids = np.zeros((len(limits), self.zSize, 2))
            for index, p in enumerate(limits, start=0):
                centroids[index] = sitk_centroid(self.img, ref=self.ref, show=show,
                                                 percentLimit=limits[index],
                                                 title=self.title)
                                                 
                centroidScore[index] = self.getDice(centroid=centroids[index])

            print("max dice-coefficient obtained using {} % of all pixels".format(
            limits[centroidScore.argmax()]*100))
            self.centroid = self.xSpace * centroids[centroidScore.argmax()]
            return self.centroid

        if percentLimit != "auto" and percentLimit is True:
            self.centroid = self.xSpace * sitk_centroid(self.img, ref=self.ref, show=show,
                                                        percentLimit=percentLimit,
                                                        title=self.title)
            return self.centroid

        if threshold == 'auto':
            self.getThresholds(pixelNumber=pixelNumber, scale=scale)
            self.centroid = self.xSpace * sitk_centroid(self.img, ref=self.ref,
                                                        show=show, 
                                                        threshold=self.lower,
                                                        title=self.title)
            return self.centroid

        if threshold != "auto" and threshold is True:
            self.centroid = self.xSpace * sitk_centroid(self.img, ref=self.ref, show=show,
                                                        threshold=threshold,
                                                        title=self.title)
            return self.centroid

    def showCentroid(self, title=None, pixel=False, interpolation='nearest',
                     ref=None):
        if self.centroid is False:
            print("Volume has no centroid yet. use Volume.getCentroid() first!")
            return None

        if title is None:
            title = self.title
        if ref is None:
            ref = self.ref
            
        if pixel is False:
            extent = (-self.xSpace/2, self.xSize*self.xSpace + self.xSpace/2, self.ySize*self.ySpace + self.ySpace/2, -self.ySpace/2)
            centroid_show(img=self.img, com=self.centroid, extent=extent,
                          title=title, interpolation=interpolation, ref=ref)
        else:
            centroid_show(img=self.img, com=self.centroid/self.xSpace, title=title,
                          interpolation=interpolation, ref=ref)

    def getMask(self, lower=False, upper=False):

        if self.seeds is False:
            print("no seeds given!")
            return None

        if lower is False and self.lower is not False:
            lower = self.lower
        if upper is False and self.upper is not False:
            upper = self.upper

        if lower is False:
            print("Lower threshold missing!")
            return None
        if upper is False:
            print("Upper threshold missing!")
            return None

        self.mask = sitk.ConnectedThreshold(image1=self.img, seedList=self.seeds,                                   
                                   lower=lower, upper=upper,
                                   replaceValue=1)
        return self.mask

    def applyMask(self, mask=None, replaceArray=False, spacing=1):
        if (mask is None):
            if self.mask:
                mask = self.mask
            else:
                print("Volume has no mask yet. use Volume.getMask() first!")
                return None

        self.masked = sitk_applyMask(self.img, mask, replaceArray=replaceArray,
                                     spacing=spacing)

        return self.masked

    def showMask(self, interpolation=None, ref=None):
        if self.mask is False:
            print("Volume has no mask yet. use Volume.getMask() first!")
            return None

        if ref is None:
            ref = self.ref

        if interpolation is None:
            interpolation = 'nearest'

        title = self.title + ", mask"

        sitk_show(img=self.mask, ref=ref, title=title,
                  interpolation=interpolation)

    def showMasked(self, interpolation=None, ref=None):
        if self.masked is False:
            print("Volume has not been masked yet. use Volume.applyMask() first!")
            return None
        if ref is None:
            ref = self.ref

        if interpolation is None:
            interpolation = 'nearest'

        title = self.title + ", mask"

        sitk_show(img=self.masked, ref=ref, title=title,
                  interpolation=interpolation)

    def getDice(self, centroid="no", show=False, showAll=False):
        '''
        calculates average dice coefficient ('dc') of the rod by trying
        different radii, and sets self.radius to the value yielding best result
        returns max obtained average dc after trying different radii

        uses xSpace (should be same as ySpace) to be used with any resolution
        calculating dc for rods with 1.5mm < r < 4mm
        '''
#        radii = np.array([2, 2.1, 2.3, 2.9, 3.1, 3.2, 3.7, 4.1, 4.2])

        if centroid == "no":
            centroid = self.centroid

        if self.radius is False:
            radii = np.linspace(1.5, 4, num = 11)*self.xSpace 
            dcs = np.zeros(len(radii))
            for index, r in enumerate(radii, start=0):
                dcs[index] = np.average(dice_circle(self.mask, centroid,
                                        radius=r, show=showAll))
                                        
            self.dice = dice_circle(self.mask, self.centroid,
                                radius=radii[dcs.argmax()], show=show)
            print("max dice-coefficient obtained for {} when compared to circle with radius = {}".format(
            self.method, radii[dcs.argmax()]))

        else:    
            self.dice = dice_circle(self.mask, self.centroid,
                                radius=self.raduis, show=show)
        print("max dice-coefficient average for the whole volume is: {}".format(dcs.max()))
        self.raduis = radii[dcs.argmax()]
        return dsc.max()


def sitk_read(directory, denoise=False):
    '''
    returns DICOM files as "SimpleITK.Image" data type (3D)
    if denoise is True: uses SimpleITK to denoise data
    '''
    reader = sitk.ImageSeriesReader()
    filenames = reader.GetGDCMSeriesFileNames(directory)
    reader.SetFileNames(filenames)
    if denoise:
        print("\n...denoising...")
        imgOriginal = reader.Execute()
        return sitk.CurvatureFlow(image1=imgOriginal,
                                  timeStep=0.125,
                                  numberOfIterations=5)
    else:
        return reader.Execute()


def sitk_write(image, output_dir='', filename='3DImage.mha'):
    '''
    saves image as .mha file
    '''
    output_file_name_3D = os.path.join(output_dir, filename)
    sitk.WriteImage(image, output_file_name_3D)


def sitk_show(img, ref=0, extent=None, title=None, interpolation='nearest'):
    """
    shows plot of img at z=ref
    """
    arr = sitk.GetArrayFromImage(img[:, :, ref])
    plt.set_cmap("gray")

    if title:
        plt.title(title)

    plt.imshow(arr, extent=extent, interpolation=interpolation)
    plt.show()


def sitk_centroid(img, show=False, ref=False, percentLimit=False,
                  threshold=False, interpolation='nearest', title=None):
    '''
    returns array with y&x coordinate of centroid for every slice of img
    centroid[slice, y&x-coordinate]
    '''
    if (threshold is False and percentLimit is False) or (threshold is True and percentLimit is True):
        print("Please set either percentLimit or threshold!")
        return None

    arr = sitk.GetArrayFromImage(img)
    z, y, x = np.shape(arr)
    # create array with centroid coordinates of rod in each slice
    com = np.zeros((z, 2))

    if ref is False:
        ref = int(z/2)

    if threshold is False:
        hist, bins = np.histogram(arr[ref, :, :].ravel(),
                                  density=True, bins=100)
        threshold = bins[np.concatenate((np.array([0]), np.cumsum(hist))) *
                         (bins[1] - bins[0]) > percentLimit][0]

    for slice in range(z):
        # structuring_element=[[1,1,1],[1,1,1],[1,1,1]]
        segmentation, segments = ndimage.label(arr[slice] > threshold)
        # print("segments: {}".format(segments))
        # add ', structuring_element' to label() for recognising
        # diagonal pixels as part of object
        com[slice, ::-1] = ndimage.center_of_mass(arr[slice, :, :]-threshold,
                                                  segmentation)
        # add ', range(1,segments)' to center_of_mass for list of centroids
        # in each slice (multiple rods!)

    if show:
        if type(show) == bool:
            show == ref
            centroid_show(img, com=com, title=title,
                          interpolation=interpolation, ref=show)

    return com


def centroid_show(img, com, extent=None, title=None, interpolation='nearest', ref=1):
        arr = sitk.GetArrayFromImage(img)
        plt.set_cmap("gray")
        if title:
            plt.title(title + ", centroid")

        plt.imshow(arr[ref, :, :], extent=extent, interpolation=interpolation)
        plt.scatter(*com[ref, :])
        plt.show()


def coordShift(first, second):
    '''
    returns array with difference of y&x coordinates for every
    centroid[slice, y&x-coordinate]
    '''
    if (np.shape(first) == np.shape(second) and
            np.shape((np.shape(first))) == (2,)):
        z, xy = np.shape(first)
        diff = np.zeros((z, 2))
        for slice in range(z):
            diff[slice, 0] = first[slice, 0] - second[slice, 0]
            diff[slice, 1] = first[slice, 1] - second[slice, 1]
        return diff
    else:
        print("Wrong shape! coordShift returned 'False'")
        return False


def coordDist(shift):
    '''
    calculates norm for each entry of array
    returns array with list of calculated values
    '''
    if np.shape(shift)[1] != 2:
        print("shift has wrong shape!")
        return False

    dist = np.zeros((len(shift), 1))
    for slice in range(len(shift)):
        dist[slice, :] = np.linalg.norm(shift[slice, :])
    return dist


def sitk_getMask(img, seedList, upper, lower):

    return sitk.ConnectedThreshold(image1=img, seedList=seedList,
                                   lower=lower, upper=upper,
                                   replaceValue=1)


def sitk_applyMask(img, mask, replaceArray=False, spacing=1):
    '''
    masks img (SimpleITK.Image) using mask (SimpleITK.Image)
    if a replaceArray is given, the spacing*values*1000 of the array will be used
    as pixel intensity for an entire slice each
    '''
    if img.GetSize() != mask.GetSize():
        print(mask.GetSize())
        print(img.GetSize())

        print("mask and image are not the same size!")
        return False

    arr = sitk.GetArrayFromImage(img)
    maskA = sitk.GetArrayFromImage(mask)
    xSize, ySize, zSize = img.GetSize()

    imgMaskedA = arr*maskA

    if (np.shape(replaceArray) == (img.GetDepth(), 1) and
            replaceArray):
        for slice in range(zSize):
            for x in range(xSize):
                for y in range(ySize):
                    if maskA[slice, y, x] == 1:
                        imgMaskedA[slice, y, x] = 1000*replaceArray[slice]*spacing

    return sitk.GetImageFromArray(imgMaskedA)


def dice_circle(input_img, centroid, radius=2.1, show=False,
                interpolation='nearest'):
    """
    Dice coefficient, inspired by
     Medpy (http://pythonhosted.org/MedPy/_modules/medpy/metric/binary.html)

    Computes the Dice coefficient (akas Sorensen index) between a binary
    object in an image and a circle.

    The metric is defined as:

        DC=\frac{2|A\cap B|}{|A|+|B|}

    where A is the first and B the second set of samples (here: binary objects)
    sys.argv[2]
    Parameters
    ----------
    input_umg : SimpleITK.Image
        Input data containing objects. Can be any type but will be converted
        into binary: background where 0, object everywhere else.
    centroid : array_like
        array with coordinates for circle centre
    radius : float
        radius for creating reference circles

    Returns
    -------
    dc : array_like
        The Dice coefficient between the object(s) in ```input``` and the
        created cirles. It ranges from 0 (no overlap) to 1 (perfect overlap).
    """

    xSize, ySize, zSize = input_img.GetSize()
    profile = np.zeros((zSize, ySize, xSize), dtype=np.uint8)
    centres = centroid.astype(int)
    for slice in range(zSize):
        rr, cc = circle(centres[slice, 0], centres[slice, 1], radius)
        profile[slice, cc, rr] = 1

    input = sitk.GetArrayFromImage(input_img)

    input = np.atleast_1d(input.astype(np.bool))
    reference = np.atleast_1d(profile.astype(np.bool))

    intersection = np.zeros((zSize, 1))
    size_input = np.zeros((zSize, 1))
    size_reference = np.zeros((zSize, 1))
    dc = np.zeros((zSize, 1))
    for slice in range(zSize):
        intersection[slice] = np.count_nonzero(input[slice, :, :] & reference[slice, :, :])
        size_input[slice] = np.count_nonzero(input[slice, :, :])
        size_reference[slice] = np.count_nonzero(reference[slice, :, :])
#        print("\n intersection[slice, :]: {}".format(intersection[slice, :]))
#        print("size_input[slice]: {}".format(size_input[slice]))
#        print("size_reference[slice]: {}".format(size_reference[slice]))
        try:
            dc[slice] = 2. * intersection[slice] / float(size_input[slice] + size_reference[slice])
        except ZeroDivisionError:
            dc[slice] = 0.0

    if show:
        plt.set_cmap("gray")
        plt.title("profile, radius: {}".format(radius))

        plt.imshow(profile[show, :, :], interpolation=interpolation)
        plt.scatter(*centres[show, :])
        plt.show()

    return dc


# to view in 3D Slicer, type this in IPython console or in jupyter notebook:
# %env SITK_SHOW_COMMAND /home/david/Downloads/Slicer-4.5.0-1-linux-amd64/Slicer
# sitk.Show(imgFillingCT)
