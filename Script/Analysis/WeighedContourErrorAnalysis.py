# -*- coding: utf-8 -*-
"""
Created on 2014-04-28

@author: Hengkai Guo
"""

from MIRVAP.Script.AnalysisBase import AnalysisBase
from MIRVAP.GUI.qvtk.Plugin.util.PluginUtil import calCentroidFromContour
from MIRVAP.Script.Registration.util.RegistrationUtil import getPointsOntheSpline
import numpy as npy
import scipy.interpolate as itp
import vtk

class WeighedContourErrorAnalysis(AnalysisBase):
    def __init__(self, gui):
        super(WeighedContourErrorAnalysis, self).__init__(gui)
    def getName(self):
        return 'Weighed Contour Registration Error'
    def analysis(self, data, point_data_fix = None):
        if point_data_fix is None:
            point_data_fix = self.gui.dataModel[data.getFixedIndex()].getPointSet('Contour').copy()
        point_data_result = data.getPointSet('Contour').copy()
        self.spacing = data.getResolution().tolist()
        self.spacing[2] = 1.0 # The resolution of z axis is nothing to do with the analysis
        point_data_fix[:, :3] *= self.spacing[:3]
        point_data_result[:, :3] *= self.spacing[:3]
        
        cnt_num = npy.array([0, 0, 0])
        mean_dis = npy.array([0.0, 0.0, 0.0])
        max_dis = npy.array([0.0, 0.0, 0.0])
        square_sum_dis = npy.array([0.0, 0.0, 0.0])
        
        #s = itp.InterpolatedUnivariateSpline(x, y)
        #s.derivatives(1)[1]
        for cnt in range(3):
            temp_result = point_data_result[npy.where(npy.round(point_data_result[:, -1]) == cnt)]
            temp_fix = point_data_fix[npy.where(npy.round(point_data_fix[:, -1]) == cnt)]
            if not temp_result.shape[0] or not temp_fix.shape[0]:
                continue
            zmin = int(npy.max([npy.min(temp_result[:, 2]), npy.min(temp_fix[:, 2])]) + 0.5)
            zmax = int(npy.min([npy.max(temp_result[:, 2]), npy.max(temp_fix[:, 2])]) + 0.5)
            
            for z in range(zmin, zmax + 1):
                data_fix = temp_fix[npy.where(npy.round(temp_fix[:, 2]) == z)]
                data_result = temp_result[npy.where(npy.round(temp_result[:, 2]) == z)]
                if data_fix is not None and data_result is not None:
                    if data_fix.shape[0] == 0 or data_result.shape[0] == 0:
                        continue
                    cnt_num[cnt] += 1
                    #center_fix = npy.mean(data_fix[:, :2], axis = 0)
                    center_fix = calCentroidFromContour(data_fix[:, :2])[0]
                    #center_result = npy.mean(data_result[:, :2], axis = 0)
                    center_result = calCentroidFromContour(data_result[:, :2])[0]
                    points_fix = getPointsOntheSpline(data_fix, center_fix, 900)
                    points_result = getPointsOntheSpline(data_result, center_result, 900)
                    
                    i = j = 0
                    for k in range(-44, 46):
                        angle = k * 4 / 180.0 * npy.pi
                        while i < 900 and points_fix[i, 2] < angle:
                            i += 1
                        if i == 900 or (i > 0 and angle - points_fix[i - 1, 2] < points_fix[i, 2] - angle):
                            ind_fix = i - 1
                        else:
                            ind_fix = i
                        while j < 900 and points_result[j, 2] < angle:
                            j += 1
                        if j == 900 or (j > 0 and angle - points_result[j - 1, 2] < points_result[j, 2] - angle):
                            ind_result = j - 1
                        else:
                            ind_result = j
                        temp_dis = npy.hypot(points_fix[ind_fix, 0] - points_result[ind_result, 0], points_fix[ind_fix, 1] - points_result[ind_result, 1])
                        max_dis[cnt] = npy.max([max_dis[cnt], temp_dis])
                        mean_dis[cnt] += temp_dis
        
        cnt_total = npy.sum(cnt_num)
        
        mean_dis /= 90
        mean_whole = npy.sum(mean_dis)
        mean_dis /= cnt_num
        mean_dis[mean_dis != mean_dis] = 0 # Replace the NAN in the mean distance
        
        if self.gui is not None:
            message = "Error on Vessel 0: %0.2fmm (Total %d slices)\nError on Vessel 1: %0.2fmm (Total %d slices)\nError on Vessel 2: %0.2fmm (Total %d slices)\nWhole Error: %0.2fmm (Total %d slices)\n" \
                % (mean_dis[0], cnt_num[0], mean_dis[1], cnt_num[1], mean_dis[2], cnt_num[2], mean_whole / cnt_total, cnt_total) + \
                "-----------------------------------------------------------------------------\n" + \
                "Max Error on Vessel 0: %0.2fmm\nMax Error on Vessel 1: %0.2fmm\nMax Error on Vessel 2: %0.2fmm\nTotal Max Error: %0.2fmm" \
                % (max_dis[0], max_dis[1], max_dis[2], npy.max(max_dis));
            self.gui.showErrorMessage("Weighed Contour Registration Error", message)
        return mean_dis, mean_whole / cnt_total, max_dis, npy.max(max_dis)
        
