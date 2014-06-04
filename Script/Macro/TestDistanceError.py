# -*- coding: utf-8 -*-
"""
Created on 2014-06-04

@author: Hengkai Guo
"""

from MIRVAP.Script.MacroBase import MacroBase
import MIRVAP.Core.DataBase as db
from util.dict4ini import DictIni
from MIRVAP.Script.Analysis.ContourErrorAnalysis import ContourErrorAnalysis
from MIRVAP.Script.Analysis.ContourErrorWithAreaAnalysis import ContourErrorWithAreaAnalysis
from MIRVAP.Script.Analysis.AreaIndexAnalysis import AreaIndexAnalysis
from MIRVAP.Script.Analysis.CenterlineErrorAnalysis import CenterlineErrorAnalysis
from MIRVAP.GUI.qvtk.Plugin.util.PluginUtil import calCenterlineFromContour
import xlwt
import os, sys

class TestDistanceError(MacroBase):
    def getName(self):
        return 'Test Distance Error'
    def run(self, window = None):
        self.path = sys.argv[0]
        if os.path.isfile(self.path):
            self.path = os.path.dirname(self.path)
        
        self.ini = DictIni(self.path + '/Script/Macro/test.ini')
        self.cnt = len(self.ini.file.name_fix)
        
        self.contourerror = ContourErrorAnalysis(None)
        self.contourareaerror = ContourErrorWithAreaAnalysis(None)
        self.result = [{}, {}, {}]
        self.resultCnt = [{}, {}, {}]
        
        for i in range(self.cnt):
            dataset = self.load(i)
            self.process(dataset, i)
            del dataset
        
        for cnt in range(3):
            for x in self.result[cnt].keys():
                self.result[cnt][x] /= self.resultCnt[cnt][x]
        
        self.savepath = self.path + self.ini.file.savedir
        self.book = xlwt.Workbook()
        title = ['CCA', 'ECA', 'ICA']
        
        self.sheet = self.book.add_sheet('Distance_error')
        for i in range(3):
            self.sheet.write(i + 1, 0, title[i])
        zmin = [0, 0, 0]
        zmax = [0, 0, 0]
        for cnt in range(3):
            zmin[cnt] = min(self.result[cnt].keys())
            zmax[cnt] = max(self.result[cnt].keys())
        z1 = int(min(zmin))
        z2 = int(max(zmax))
        for z in range(z1, z2 + 1):
            self.sheet.write(0, z - z1 + 1, z * 0.34722220897674)
        for cnt in range(3):
            for x in self.result[cnt].keys():
                self.sheet.write(cnt + 1, int(x) - z1 + 1, self.result[cnt][x])
        for cnt in range(3):
            for x in self.result[cnt].keys():
                self.sheet.write(cnt + 4, int(x) - z1 + 1, self.resultCnt[cnt][x])
        self.book.save(self.path + self.ini.file.savedir + 'Distance_error_withArea.xls')
        
        if self.gui:
            self.gui.showErrorMessage('Success', 'Test sucessfully!')
        else:
            print 'Test sucessfully!'
            
    def load(self, i):
        dataset = {'result': [], 'fix': []}
        data, info, point = db.loadMatData(self.path + self.ini.file.datadir
            + self.ini.file.name_result[i] + '_icp_cen.mat', None)
        dataset['result'] = db.BasicData(data, info, point)
        
        data, info, point = db.loadMatData(self.path + self.ini.file.datadir + '/Contour/'
            + self.ini.file.name_fix[i] + '.mat', None)
        dataset['fix'] = db.BasicData(data, info, point)
        
        print 'Data %s loaded!' % self.ini.file.name_result[i]
            
        return dataset
    def process(self, dataset, i):
        print 'Evaluation Data %s...' % self.ini.file.name_result[i]
        mean_dis, mean_whole, max_dis, max_whole, result = self.contourareaerror.analysis(dataset['result'], dataset['fix'].getPointSet('Contour').copy(), True)
        print 'Contour Error Done! Whole mean is %0.2fmm.' % mean_whole
        print result
        for cnt in range(3):
            for x in result[cnt].keys():
                self.result[cnt][x] = self.result[cnt].get(x, 0) + result[cnt][x]
                self.resultCnt[cnt][x] = self.resultCnt[cnt].get(x, 0) + 1
         
if __name__ == "__main__":
    test = TestAllRegistration(None)
    test.run()
