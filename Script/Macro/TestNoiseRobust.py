# -*- coding: utf-8 -*-
"""
Created on 2014-06-05

@author: Hengkai Guo
"""

from MIRVAP.Script.MacroBase import MacroBase
import MIRVAP.Core.DataBase as db
from util.dict4ini import DictIni
from MIRVAP.Script.Registration.IcpPointsetRegistration import IcpPointsetRegistration
from MIRVAP.Script.Analysis.SurfaceErrorAnalysis import SurfaceErrorAnalysis
from MIRVAP.GUI.qvtk.Plugin.util.PluginUtil import calCenterlineFromContour
import xlwt
import MIRVAP.Script.Registration.util.RegistrationUtil as util
import numpy.matlib as ml
import os, sys
import numpy as npy

class TestNoiseRobust(MacroBase):
    def getName(self):
        return 'Test Noise Robustness'
    def run(self, window = None):
        self.path = sys.argv[0]
        if os.path.isfile(self.path):
            self.path = os.path.dirname(self.path)
        
        self.ini = DictIni(self.path + '/Script/Macro/test_merge_suc.ini')
        self.cnt = len(self.ini.file.name_fix)
        self.repeat = 3
        
        self.icp = IcpPointsetRegistration(None)
        self.surfaceerror = SurfaceErrorAnalysis(None)
        
        self.error = npy.zeros([4, 16, 4], dtype = npy.float32)
        
        for i in range(self.cnt):
            dataset = self.load(i)
            self.process(dataset, i)
            del dataset
            
        self.error /= self.cnt
        
        self.book = xlwt.Workbook()
        title = ['CCA', 'ECA', 'ICA', 'Overall']
        self.sheet = self.book.add_sheet('Noise Slice')
        
        self.sheet.write(1, 0, 'Cen-Label')
        self.sheet.write(5, 0, 'Con-Label')
        self.sheet.write(9, 0, 'Cen')
        self.sheet.write(13, 0, 'Con')
        for i in range(4):
            self.sheet.write(i + 1, 1, title[i])
            self.sheet.write(i + 5, 1, title[i])
            self.sheet.write(i + 9, 1, title[i])
            self.sheet.write(i + 13, 1, title[i])
        for i in range(0, 16):
            self.sheet.write(0, i + 2, float(i) / 5)
        for i in range(4):
            for j in range(0, 16):
                self.sheet.write(i + 1, j + 2, float(self.error[0, j, i]))
                self.sheet.write(i + 5, j + 2, float(self.error[1, j, i]))
                self.sheet.write(i + 9, j + 2, float(self.error[2, j, i]))
                self.sheet.write(i + 13, j + 2, float(self.error[3, j, i]))
        self.book.save('./Result/Robust_Noise_merge_suc.xls')
        
        if self.gui:
            self.gui.showErrorMessage('Success', 'Test sucessfully!')
        else:
            print 'Test sucessfully!'
            
    def load(self, i):
        dataset = {'mov': [], 'fix': []}
        
        data, info, point = db.loadMatData(self.path + self.ini.file.datadir + '/Contour/'
            + self.ini.file.name_fix[i] + '.mat', None)
        point['Centerline'] = calCenterlineFromContour(point)
        fileData = db.BasicData(data, info, point)
        dataset['fix'] = fileData
        
        data, info, point = db.loadMatData(self.path + self.ini.file.datadir + '/Contour/'
            + self.ini.file.name_mov[i] + '.mat', None)
        fileData = db.BasicData(data, info, point)
        dataset['mov'] = fileData
        print 'Data %s loaded!' % self.ini.file.name_result[i]
            
            
        return dataset
    def process(self, dataset, i):
        # ICP with centerline
        print 'Register Data %s with ICP...' % self.ini.file.name_result[i]
        tmp = dataset['mov'].pointSet.data['Contour'].copy()
        for sd in range(0, 16):
            mean_dis_all = npy.zeros([4, 3], dtype = npy.float32)
            mean_whole_all = npy.zeros([4, 1], dtype = npy.float32)
            if sd > 0:
                repeat = self.repeat
            else:
                repeat = 1
            for i in range(repeat):
                dataset['mov'].pointSet.data['Contour'] = AddNoise(tmp, float(sd) / 5)
                dataset['mov'].pointSet.data['Centerline'] = calCenterlineFromContour(dataset['mov'].pointSet.data)
                
                # Centerline label
                data, point, para = self.icp.register(dataset['fix'], dataset['mov'], 1)
                resultData = db.ResultData(data, db.ImageInfo(dataset['fix'].info.data), point)
                resultData.info.addData('fix', 1)
                resultData.info.addData('move', 2)
                resultData.info.addData('transform', para)
                
                mean_dis, mean_whole, max_dis, max_whole = self.surfaceerror.analysis(resultData, dataset['fix'].getPointSet('Contour').copy(), dataset['mov'].getPointSet('Contour').copy(), dataset['mov'].getPointSet('Mask').copy(), dataset['mov'].getResolution().tolist())
                mean_dis_all[0, :] += mean_dis
                mean_whole_all[0] += mean_whole
                del data, point, resultData, para
                
                # Contour label
                data, point, para = self.icp.register(dataset['fix'], dataset['mov'], 0, op = True) 
                resultData = db.ResultData(data, db.ImageInfo(dataset['fix'].info.data), point)
                resultData.info.addData('fix', 1)
                resultData.info.addData('move', 2)
                resultData.info.addData('transform', para)
                
                mean_dis, mean_whole, max_dis, max_whole = self.surfaceerror.analysis(resultData, dataset['fix'].getPointSet('Contour').copy(), dataset['mov'].getPointSet('Contour').copy(), dataset['mov'].getPointSet('Mask').copy(), dataset['mov'].getResolution().tolist())
                mean_dis_all[1, :] += mean_dis
                mean_whole_all[1] += mean_whole
                del data, point, resultData, para
                
                # Centerline no-label
                data, point, para = self.icp.register(dataset['fix'], dataset['mov'], 1, op = True)
                resultData = db.ResultData(data, db.ImageInfo(dataset['fix'].info.data), point)
                resultData.info.addData('fix', 1)
                resultData.info.addData('move', 2)
                resultData.info.addData('transform', para)
                
                mean_dis, mean_whole, max_dis, max_whole = self.surfaceerror.analysis(resultData, dataset['fix'].getPointSet('Contour').copy(), dataset['mov'].getPointSet('Contour').copy(), dataset['mov'].getPointSet('Mask').copy(), dataset['mov'].getResolution().tolist())
                mean_dis_all[2, :] += mean_dis
                mean_whole_all[2] += mean_whole
                del data, point, resultData, para
                
                # Contour no-label
                data, point, para = self.icp.register(dataset['fix'], dataset['mov'], 0) 
                resultData = db.ResultData(data, db.ImageInfo(dataset['fix'].info.data), point)
                resultData.info.addData('fix', 1)
                resultData.info.addData('move', 2)
                resultData.info.addData('transform', para)
                
                mean_dis, mean_whole, max_dis, max_whole = self.surfaceerror.analysis(resultData, dataset['fix'].getPointSet('Contour').copy(), dataset['mov'].getPointSet('Contour').copy(), dataset['mov'].getPointSet('Mask').copy(), dataset['mov'].getResolution().tolist())
                mean_dis_all[3, :] += mean_dis
                mean_whole_all[3] += mean_whole
                del data, point, resultData, para
                
                sys.stdout.write(str(i) + ',')
                sys.stdout.flush()
            
            mean_dis_all /= repeat
            mean_whole_all /= repeat
            print ' '
            print 'Noise level %fmm Done!' % (float(sd) / 5)
            print 'Contour Error Done! Whole mean is %0.2fmm vs %0.2fmm.' % (mean_whole_all[0], mean_whole_all[1])
            for i in range(4):
                self.error[i, sd, :3] += mean_dis_all[i, :]
                self.error[i, sd, 3] += mean_whole_all[i]

def AddNoise(points, sd):
    result_point = points.copy()
    if sd > 0:
        n = result_point.shape[0]
        
        #noise = npy.matlib.randn(n / 10, 2) * sd
        noise = npy.matlib.randn(result_point.shape[0], 2) * sd
        #result_point[ind[:noise.shape[0]], :2] += noise
        result_point[:, :2] += noise
    return result_point
