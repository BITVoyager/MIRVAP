# -*- coding: utf-8 -*-
"""
Created on 2014-08-10

@author: Hengkai Guo
"""

from MIRVAP.Script.MacroBase import MacroBase
import MIRVAP.Core.DataBase as db
from util.dict4ini import DictIni
from MIRVAP.Script.Registration.NonrigidHybridRegistration import NonrigidHybridRegistration
from MIRVAP.GUI.qvtk.Plugin.util.PluginUtil import calCenterlineFromContour
import xlwt
import os, sys

class TestNonrigidRegistration(MacroBase):
    def getName(self):
        return 'Test Different Parameters of Non-rigid Registration'
    def run(self, window = None):
        self.path = sys.argv[0]
        if os.path.isfile(self.path):
            self.path = os.path.dirname(self.path)
        
        self.ini = DictIni(self.path + '/Script/Macro/test.ini')
        self.cnt = len(self.ini.file.name_fix)
        
        self.spacing = [-1.0, 40.0, 32.0, 16.0, 8.0, 4.0]
        self.w1 = [-1.0, 0.0, 1.0, 10.0, 100.0, 1000.0, 10000.0]
        self.type = ['SSD', 'MI', 'CR']
        n = len(self.w1) * len(self.spacing)
        
        self.savepath = self.path + self.ini.file.savedir
        self.book = xlwt.Workbook()
        
        self.sheet1 = self.book.add_sheet('DSC')
        p = 1
        for k in range(len(self.type)):
            self.sheet1.write(p, 0, self.type[k])
            for i in range(len(self.spacing)):
                for j in range(len(self.w1)):
                    self.sheet1.write(p, 1, "beta = %fmm, w1 = %f" % (self.spacing[i], self.w1[j]))
                    p += 1
        
        self.sheet2 = self.book.add_sheet('MSD')
        p = 1
        for k in range(len(self.type)):
            self.sheet2.write(p, 0, self.type[k])
            for i in range(len(self.spacing)):
                for j in range(len(self.w1)):
                    self.sheet2.write(p, 1, "beta = %fmm, w1 = %f" % (self.spacing[i], self.w1[j]))
                    p += 1
                    
        for i in range(2, self.cnt):
            dataset = self.load(i)
            self.process(dataset, i)
            del dataset
            
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
        point['Centerline'] = calCenterlineFromContour(point)
        fileData = db.BasicData(data, info, point)
        dataset['mov'] = fileData
        print 'Data %s loaded!' % self.ini.file.name_result[i]
            
        return dataset
    def process(self, dataset, i):
        hybrid = NonrigidHybridRegistration(None)
        print 'Register Data %s with Hybrid Method...' % (self.ini.file.name_result[i])
        data, point, para = hybrid.register(dataset['fix'], dataset['mov'], spacing = self.spacing, w1 = self.w1, type = self.type)
        print 'Done!'
        
        p = 1
        for k in range(len(self.type)):
            for q in range(len(self.spacing)):
                for j in range(len(self.w1)):
                    self.sheet1.write(p, i + 2, float(para[q, j, k, 0]))
                    self.sheet2.write(p, i + 2, float(para[q, j, k, 1]))
                    p += 1
        
        self.sheet1.write(0, i + 2, self.ini.file.name_result[i])
        self.sheet2.write(0, i + 2, self.ini.file.name_result[i])
        self.book.save(self.path + self.ini.file.savedir + self.ini.file.name + '.xls')
        del para
        del hybrid
