# -*- coding: utf-8 -*-
"""
Created on 2014-02-01

@author: Hengkai Guo
"""

class DataBase(object):
    def getData(self):
        raise NotImplementedError('Method "getArrayData" Not Impletemented!')

import numpy as npy
import SimpleITK as sitk
import itk
import scipy.io as sio
        
class ImageInfo(DataBase):
    def __init__(self, data = {}):
        self.data = data
        
    def getData(self, key = None):
        if key is not None:
            return self.data.get(key)
        else:
            return self.data
    def getResolution(self):
        return self.getData('resolution')
    def getModality(self):
        return self.getData('modality')
    def getView(self):
        return self.getData('view')
    def getFlip(self):
        return self.getData('flip')
    def getName(self):
        return self.getData('name')
    def setName(self, name):
        self.data['name'] = name
        
    def setData(self, data):
        self.data = data
    def addData(self, key, value):
        self.data[key] = value
        
class ImageData(DataBase):
    def __init__(self, data = None, info = None):
        if data != None:
            data = data.astype(dtype = npy.float32)
        self.data = data
        self.info = info
        
    def getData(self):
        temp = self.getFlip()
        if len(temp) == 3:
            return self.data[::temp[0], ::temp[1], ::temp[2]].transpose(self.getView())
        else:
            return self.data[::temp[0], ::temp[1]].transpose(self.getView())
    def getITKImage(self, imageType = None):
        if imageType == None:
            imageType = self.getITKImageType()
        image = itk.PyBuffer[imageType].GetImageFromArray(self.getData())
        image.SetSpacing(self.getResolution())
        return image
    def getSimpleITKImage(self):
        image = sitk.GetImageFromArray(self.getData())
        image.SetSpacing(self.getResolution())
        return image
    def getDimension(self):
        return self.data.ndim
    def getITKImageType(self):
        return itk.Image[itk.F, len(self.data.shape)]
        
    def setDataFromArray(self, data):
        self.data = data
    def setDataFromITKImage(self, data, imageType):
        self.data = itk.PyBuffer[imageType].GetArrayFromImage(data)
    def setDataFromSimpleITKImage(self, data):
        self.data = sitk.GetArrayFromImage(data)
    def setData(self, data, imageType = None):
        if isinstance(data, npy.ndarray):
            self.setDataFromArray(data)
        elif isinstance(data, sitk.Image):
            self.setDataFromSimpleITKImage(data)
        elif imageType is not None:
            self.setDataFromITKImage(data, imageType)
            
    def getInfo(self):
        return self.info
    def setInfo(self, info):
        self.info = info
    # Resolution: x(col), y(row), z(slice)
    def getResolution(self):
        if self.getDimension() == 3:
            return self.info.getResolution()[self.getView()[::-1]]
        else:
            return self.info.getResolution()
    def getModality(self):
        return self.info.getModality()
    def getView(self):
        return self.info.getView()
    def getFlip(self):
        return self.info.getFlip()
    def getName(self):
        return self.info.getName()
    def setName(self, name):
        self.info.setName(name)

class PointSetData(DataBase):
    def __init__(self, data = {}):
        self.data = data
    def getData(self, key):
        if key not in self.data:
            self.data[key] = npy.array([[-1, -1, -1, -1]])
        return self.data[key]
    def getSlicePoint(self, key, axis, pos):
        data = self.getData(key)
        data = data[npy.where(data[:, axis] == pos)]
        result = [npy.array([]), npy.array([]), npy.array([])]
        for cnt in range(3):
            result[cnt] = data[npy.where(data[:, -1] == cnt)]
            if result[cnt].any:
                result[cnt] = result[cnt][:, :-1]
        return result
    def setSlicePoint(self, key, data, axis, pos, cnt):
        data = npy.insert(data, [data.shape[1]], npy.ones((data.shape[0], 1), int) * cnt, axis = 1)
        self.getData(key)
        self.data[key] = npy.delete(self.data[key], npy.where(npy.logical_and(self.data[key][:, axis] == pos, self.data[key][:, -1] == cnt)), axis = 0)
        self.data[key] = npy.append(self.data[key], data, axis = 0)

class BasicData(ImageData):
    def __init__(self, data = None, info = None, pointSet = {}):
        super(BasicData, self).__init__(data, info)
        
        self.pointSet = PointSetData(pointSet)
        self.result = False
    def getPointSet(self, key = None):
        if key:
            return self.pointSet.getData(key)
        else:
            return self.pointSet.data
        
class ResultData(ImageData):        
    def __init__(self, data = None, detail = {}):
        super(ResultData, self).__init__(data)
        self.result = True
        self.detail = detail
    def getFixedIndex(self):
        return self.detail.get('fix', None)
    def getMovingIndex(self):
        return self.detail.get('move', None)
    def addDetail(self, key, value):
        self.detail[key] = value

def loadDicomArray(dir):
    # When the amount of files exceeds 80+, the GetArrayFromImage function may crash, because of the memory limit of array in numpy
    if len(dir) == 1:
        imageReader = sitk.ImageFileReader()
        imageReader.SetFileName(dir[0])
    else:
        imageReader = sitk.ImageSeriesReader()
        imageReader.SetFileNames(dir)
    
    image = imageReader.Execute()
    del imageReader
    if len(dir) < 80:
        array = sitk.GetArrayFromImage(image)
    else:
        imSize = image.GetSize()[-1]
        cropSize = imSize / 2
        cropFilter = sitk.CropImageFilter()
        cropFilter.SetLowerBoundaryCropSize([0, 0, 0])
        cropFilter.SetUpperBoundaryCropSize([0, 0, cropSize])
        array1 = sitk.GetArrayFromImage(cropFilter.Execute(image))
        cropFilter.SetLowerBoundaryCropSize([0, 0, imSize - cropSize])
        cropFilter.SetUpperBoundaryCropSize([0, 0, 0])
        array = sitk.GetArrayFromImage(cropFilter.Execute(image))
        
        array = (array1, array)
        del array1, image
        array = npy.concatenate((array[0], array[1]), axis = 0)
    return array

def loadMatData(dir):
    data = sio.loadmat(dir)
    
    image = data['image']
    point = data.get('point')
    if point is not None:
        name = point.dtype.names
        pointSet = dict(zip(name, [point[key][0][0] for key in name]))
    else:
        pointSet = None
    
    header = data['header']
    resolution = header['resolution'][0][0][0]
    orientation = header['orientation'][0][0][0]
    modality = str(header['modality'][0][0][0])
    name = str(header['name'][0][0][0])
    info = ImageInfo({'modality': modality, 'resolution': resolution, 'orientation': orientation, 'name': name})
    
    view, flip = getViewAndFlipFromOrientation(orientation, resolution.shape[0])
    info.addData('view', view)
    info.addData('flip', flip)
        
    return image, info, pointSet

def saveMatData(dir, data):
    image = data.data
    point = data.getPointSet()
    
    resolution = data.info.getResolution()
    orientation = data.info.getData('orientation')
    modality = npy.array([data.getModality()])
    name = npy.array([data.getName()])
    header = npy.array([(resolution, orientation, modality, name)], 
        dtype = [('resolution', 'O'), ('orientation', 'O'), ('modality', 'O'), ('name', 'O')] )
    if point:
        pointSet = npy.array([tuple(point.values())], 
            dtype = [(key, 'O') for key in point.keys()])
        dict = {'image': image, 'point': pointSet, 'header': header}
    else:
        dict = {'image': image, 'header': header}
    
    sio.savemat(dir, dict)

def getViewAndFlipFromOrientation(orientation, dimension):
    '''
        Orientation: the direction cosines of the first row and the first
    column with respect to the patient. The direction of the axes are defined
    by the patients orientation to ensure LPS(Left, Posterior, Superior) system.
    ----------------------------------------------------------------------------
        1 0 0 0 1 0
        x: Sagittal slice * row
        y: Coronal  slice * col
        z: Axial    row * col
    ----------------------------------------------------------------------------
        1 0 0 0 0 -1
        x: Sagittal row * slice
        y: Coronal  row * col
        z: Axial    slice * col
    ----------------------------------------------------------------------------
        0 1 0 0 0 -1
        x: Sagittal row * slice
        y: Coronal  row * col
        z: Axial    slice * col
    ----------------------------------------------------------------------------
    '''
    ori = npy.round(orientation)
    col = npy.where(ori[0:3])[0][0]
    row = npy.where(ori[3:6])[0][0]
    
    if dimension == 3:
        view = npy.array([row - 1, 2 - row + col * 2, 2 - col * 2])
        flip = [1, ori[3 + row], ori[col]]
    else:
        view = npy.array([0, 1])
        flip = [1, 1]
        
    return (view, flip)
    
if __name__ == "__main__":
    basic = BasicData()
