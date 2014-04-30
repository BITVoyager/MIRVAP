# -*- coding: utf-8 -*-
"""
Created on 2014-04-24

@author: Hengkai Guo
"""

from MIRVAP.Script.RegistrationBase import RegistrationBase
from MIRVAP.GUI.qvtk.Plugin.util.PluginUtil import calCentroidFromContour
import MIRVAP.Core.DataBase as db
import numpy as npy
import numpy.matlib as ml
from scipy import interpolate
import itk, vtk
import SimpleITK as sitk
import util.RegistrationUtil as util
import sys, os

class IcpPointsetRegistration(RegistrationBase):
    def __init__(self, gui):
        super(IcpPointsetRegistration, self).__init__(gui)
    def getName(self):
        return 'ICP Pointset Registration For Vessel'
                                 
    def register(self, fixedData, movingData, index = -1):
        if index == -1:
            index = self.gui.getDataIndex({'Contour': 0, 'Centerline': 1}, 'Select the object')
        if index is None:
            return None, None, None
        if index == 0:
            fixed_points = fixedData.getPointSet('Contour')
            moving_points = movingData.getPointSet('Contour')
        else:
            fixed_points = fixedData.getPointSet('Centerline')
            moving_points = movingData.getPointSet('Centerline')
        
        fixed_res = fixedData.getResolution().tolist()
        moving_res = movingData.getResolution().tolist()
        fixed_points = fixed_points.copy()[npy.where(fixed_points[:, 0] >= 0)]
        moving_points = moving_points.copy()[npy.where(moving_points[:, 0] >= 0)]
        
        # Use the bifurcation as the initial position
        fixed_bif = db.getBifurcation(fixed_points)
        moving_bif = db.getBifurcation(moving_points)
        if (fixed_bif < 0) or (moving_bif < 0):
            fixed_min = 0
        else:
            temp = moving_points[:, 2:]
            moving_delta = moving_bif - npy.min(temp[npy.where(npy.round(temp[:, 1]) == 0), 0])
            fixed_min = fixed_bif - moving_delta * moving_res[-1] / fixed_res[-1]
        #print moving_res
        #print fixed_res
        
        # Augmentation of pointset
        fixed = fixed_points[npy.where(fixed_points[:, 2] >= fixed_min)]
        moving = moving_points.copy()
        if index == 0:
            fixed = util.augmentPointset(fixed, int(fixed_res[-1] / moving_res[-1] + 0.5), moving.shape[0], fixed_bif)
            moving = util.augmentPointset(moving, int(moving_res[-1] / fixed_res[-1] + 0.5), fixed.shape[0], moving_bif)
        
        #fixed = fixed[:, :3]
        #moving = moving[:, :3]
        fixed[:, :3] *= fixed_res[:3]
        moving[:, :3] *= moving_res[:3]
        if (fixed_bif >= 0) and (moving_bif >= 0):
            fixed[:, 2] -= (fixed_bif * fixed_res[2] - moving_bif * moving_res[2])
        #print fixed.shape[0], moving.shape[0]
        #return None, None, None
        
        # Prepare for ICP
        LandmarkTransform = vtk.vtkLandmarkTransform()
        LandmarkTransform.SetModeToRigidBody()
        MaxIterNum = 50
        MaxNum = 200
        
        targetPoints = [vtk.vtkPoints(), vtk.vtkPoints(), vtk.vtkPoints()]
        targetVertices = [vtk.vtkCellArray(), vtk.vtkCellArray(), vtk.vtkCellArray()]
        target = [vtk.vtkPolyData(), vtk.vtkPolyData(), vtk.vtkPolyData()]
        Locator = [vtk.vtkCellLocator(), vtk.vtkCellLocator(), vtk.vtkCellLocator()]
        if index == 0:
            label_dis = [3, 3, 3]
            #label_dis = [3, 2, 1]
        else:
            label_dis = [3, 2, 1]
        
        for i in range(3):
            for x in fixed[npy.round(fixed[:, 3]) != label_dis[i]]:
                id = targetPoints[i].InsertNextPoint(x[0], x[1], x[2])
                targetVertices[i].InsertNextCell(1)
                targetVertices[i].InsertCellPoint(id)
            target[i].SetPoints(targetPoints[i])
            target[i].SetVerts(targetVertices[i])
            
            Locator[i].SetDataSet(target[i])
            Locator[i].SetNumberOfCellsPerBucket(1)
            Locator[i].BuildLocator()
        
        step = 1
        if moving.shape[0] > MaxNum:
            step = moving.shape[0] / MaxNum
        nb_points = moving.shape[0] / step
        
        accumulate = vtk.vtkTransform()
        accumulate.PostMultiply()
        
        points1 = vtk.vtkPoints()
        points1.SetNumberOfPoints(nb_points)
        closestp = vtk.vtkPoints()
        closestp.SetNumberOfPoints(nb_points)
        points2 = vtk.vtkPoints()
        points2.SetNumberOfPoints(nb_points)
        
        label = npy.zeros([nb_points], dtype = npy.int8)
        j = 0
        for i in range(nb_points):
            points1.SetPoint(i, moving[j][0], moving[j][1], moving[j][2])
            label[i] = moving[j][3]
            j += step
        
        id1 = id2 = vtk.mutable(0)
        dist = vtk.mutable(0.0)
        outPoint = [0.0, 0.0, 0.0]
        p1 = [0.0, 0.0, 0.0]
        p2 = [0.0, 0.0, 0.0]
        iternum = 0
        a = points1
        b = points2
        
        '''
        path = sys.argv[0]
        if os.path.isfile(path):
            path = os.path.dirname(path)
        path += '/Data/Transform'
        wfile = open("%s/transform.txt" % path, 'w')
        '''
        
        matrix = accumulate.GetMatrix()
        T = ml.mat([matrix.GetElement(0, 3), matrix.GetElement(1, 3), matrix.GetElement(2, 3)]).T;
        R = ml.mat([[matrix.GetElement(0, 0), matrix.GetElement(0, 1), matrix.GetElement(0, 2)], 
                    [matrix.GetElement(1, 0), matrix.GetElement(1, 1), matrix.GetElement(1, 2)], 
                    [matrix.GetElement(2, 0), matrix.GetElement(2, 1), matrix.GetElement(2, 2)]]).I;
        if (fixed_bif >= 0) and (moving_bif >= 0):
            T[2] += (fixed_bif * fixed_res[2] - moving_bif * moving_res[2])
        #saveTransform(wfile, T, R)
        
        while True:
            for i in range(nb_points):
                Locator[label[i]].FindClosestPoint(a.GetPoint(i), outPoint, id1, id2, dist)
                closestp.SetPoint(i, outPoint)
                
            LandmarkTransform.SetSourceLandmarks(a)
            LandmarkTransform.SetTargetLandmarks(closestp)
            LandmarkTransform.Update()
            
            accumulate.Concatenate(LandmarkTransform.GetMatrix())
            
            iternum += 1
            if iternum >= MaxIterNum:
                break
            
            for i in range(nb_points):
                a.GetPoint(i, p1)
                LandmarkTransform.InternalTransformPoint(p1, p2)
                b.SetPoint(i, p2)
            
            matrix = accumulate.GetMatrix()
            T = ml.mat([matrix.GetElement(0, 3), matrix.GetElement(1, 3), matrix.GetElement(2, 3)]).T;
            R = ml.mat([[matrix.GetElement(0, 0), matrix.GetElement(0, 1), matrix.GetElement(0, 2)], 
                        [matrix.GetElement(1, 0), matrix.GetElement(1, 1), matrix.GetElement(1, 2)], 
                        [matrix.GetElement(2, 0), matrix.GetElement(2, 1), matrix.GetElement(2, 2)]]).I;
            if (fixed_bif >= 0) and (moving_bif >= 0):
                T[2] += (fixed_bif * fixed_res[2] - moving_bif * moving_res[2])
            #saveTransform(wfile, T, R)
            b, a = a, b
            
        #wfile.close()
        # Get the result transformation parameters
        matrix = accumulate.GetMatrix()
        T = ml.mat([matrix.GetElement(0, 3), matrix.GetElement(1, 3), matrix.GetElement(2, 3)]).T;
        R = ml.mat([[matrix.GetElement(0, 0), matrix.GetElement(0, 1), matrix.GetElement(0, 2)], 
                    [matrix.GetElement(1, 0), matrix.GetElement(1, 1), matrix.GetElement(1, 2)], 
                    [matrix.GetElement(2, 0), matrix.GetElement(2, 1), matrix.GetElement(2, 2)]]).I;
        if (fixed_bif >= 0) and (moving_bif >= 0):
            T[2] += (fixed_bif * fixed_res[2] - moving_bif * moving_res[2])
        
        # Resample the moving contour
        resampled_points = [None, None, None]
        moving_points = movingData.getPointSet('Contour').copy()
        nn = 20
        nearbif_points = [None, None, None]
        nearbif_center = [None, None]
        bif_slice = 0
        
        for cnt in range(3):
            temp_result = moving_points[npy.where(npy.round(moving_points[:, -1]) == cnt)]
            if not temp_result.shape[0]:
                continue
            zmin = int(npy.min(temp_result[:, 2]) + 0.5)
            zmax = int(npy.max(temp_result[:, 2]) + 0.5)
            
            resampled_points[cnt] = npy.zeros([(zmax - zmin + 1) * nn, 4], dtype = npy.float32)
            resampled_index = 0
            
            for z in range(zmin, zmax + 1):
                data_result = temp_result[npy.where(npy.round(temp_result[:, 2]) == z)]
                if data_result is not None:
                    if data_result.shape[0] == 0:
                        continue
                    
                    #center_result = npy.mean(data_result[:, :2], axis = 0)
                    center_result = calCentroidFromContour(data_result[:, :2])[0]
                    points_result = util.getPointsOntheSpline(data_result, center_result, 900)
                    if cnt > 0 and z == zmin:
                        nearbif_points[cnt] = points_result
                        nearbif_center[cnt - 1] = center_result
                        bif_slice = z
                    elif cnt == 0 and z == zmax - 1:
                        nearbif_points[cnt] = points_result
                        
                    i = 0
                    for k in range(- nn / 2 + 1, nn / 2 + 1):
                        angle = k * 360 / nn / 180.0 * npy.pi
                        
                        while i < 900 and points_result[i, 2] < angle:
                            i += 1
                        if i == 900 or (i > 0 and angle - points_result[i - 1, 2] < points_result[i, 2] - angle):
                            ind_result = i - 1
                        else:
                            ind_result = i
                        
                        resampled_points[cnt][resampled_index, :2] = points_result[ind_result, :2]
                        resampled_points[cnt][resampled_index, 2] = z
                        resampled_points[cnt][resampled_index, 3] = k + nn / 2 - 1
                        resampled_index += 1
        
        nearbif_angle = [npy.arctan2(nearbif_center[1][1] - nearbif_center[0][1], nearbif_center[1][0] - nearbif_center[0][0]), 
                         npy.arctan2(nearbif_center[0][1] - nearbif_center[1][1], nearbif_center[0][0] - nearbif_center[1][0])]
        point_near_bif = npy.zeros([2, 2], dtype = npy.float32)
        for cnt in range(2):
            ind = npy.argmin(npy.abs(nearbif_points[cnt + 1][:, 2] - nearbif_angle[cnt]))
            point_near_bif[cnt, :] = nearbif_points[cnt + 1][ind, :2]
        bif_points = npy.zeros([3, 3], dtype = npy.float32)
        bif_points[0, :2] = npy.mean(point_near_bif, axis = 0)
        bif_points[0, 2] = bif_slice
        nearbif_angle = [npy.arctan2(nearbif_center[1][0] - nearbif_center[0][0], nearbif_center[0][1] - nearbif_center[1][1]), 
                         npy.arctan2(nearbif_center[0][0] - nearbif_center[1][0], nearbif_center[1][1] - nearbif_center[0][1])]
        nearbif_points[0][:, 2] = npy.arctan2(nearbif_points[0][:, 1] - bif_points[0, 1], nearbif_points[0][:, 0] - bif_points[0, 0])
        for cnt in range(1, 3):
            ind = npy.argmin(npy.abs(nearbif_points[0][:, 2] - nearbif_angle[cnt - 1]))
            bif_points[cnt, :2] = nearbif_points[0][ind, :2]
        bif_points[1:, 2] = bif_slice - 1
        
        # Apply the transformation on the resampled points
        for cnt in range(3):
            resampled_points[cnt][:, :3] = applyTransformForPoints(resampled_points[cnt][:, :3], moving_res, fixed_res, R, T)
        bif_points = applyTransformForPoints(bif_points, moving_res, fixed_res, R, T)

        # Resample the points near the bifurcation
        points = vtk.vtkPoints()
        points.InsertPoint(0, bif_points[1, 0], bif_points[1, 1], bif_points[1, 2])
        points.InsertPoint(1, bif_points[0, 0], bif_points[0, 1], bif_points[0, 2])
        points.InsertPoint(2, bif_points[2, 0], bif_points[2, 1], bif_points[2, 2])

        para_spline = vtk.vtkParametricSpline()
        para_spline.SetPoints(points)
        para_spline.ClosedOff()
        
        numberOfOutputPoints = 6
        new_bif_points = npy.zeros([numberOfOutputPoints + 1, 4], dtype = npy.float32)
        
        for i in range(0, numberOfOutputPoints + 1):
            t = i * 1.0 / numberOfOutputPoints
            pt = [0.0, 0.0, 0.0]
            para_spline.Evaluate([t, t, t], pt, [0] * 9)
            new_bif_points[i, :3] = pt
        new_bif_points[:, 3] = 0
        
        # Reslice the result points
        trans_points = npy.array([[-1, -1, -1, -1]], dtype = npy.float32)
        bif_slice = int(npy.ceil(bif_points[0, 2]))
        
        for cnt in range(3):
            zmin = int(npy.ceil(npy.max(resampled_points[cnt][:nn, 2])))
            zmax = int(npy.min(resampled_points[cnt][-nn:, 2]))
            if cnt == 0:
                zmax = bif_slice
            else:
                zmin = bif_slice
            
            for k in range(0, nn):
                data = resampled_points[cnt][npy.where(npy.round(resampled_points[cnt][:, -1]) == k)]
                if cnt == 0:
                    dis1 = npy.hypot(data[-1, 0] - resampled_points[1][nn:nn * 2, 0], data[-1, 1] - resampled_points[1][nn:nn * 2, 1])
                    ind1 = npy.argmin(dis1)
                    dis2 = npy.hypot(data[-1, 0] - resampled_points[2][nn:nn * 2, 0], data[-1, 1] - resampled_points[2][nn:nn * 2, 1])
                    ind2 = npy.argmin(dis2)
                    if dis1[ind1] < dis2[ind2]:
                        data_add = resampled_points[1][npy.where((npy.round(resampled_points[1][:, -1]) == ind1) & (resampled_points[1][:, 2] <= zmax + 1))]
                    else:
                        data_add = resampled_points[2][npy.where((npy.round(resampled_points[2][:, -1]) == ind2) & (resampled_points[2][:, 2] <= zmax + 1))]
                    data = npy.append(data, data_add[1:, :], axis = 0)
                else:
                    # TO BE DONE
                    dis1 = npy.hypot(data[0, 0] - resampled_points[0][-nn * 2:-nn, 0], data[0, 1] - resampled_points[0][-nn * 2:-nn, 1])
                    ind1 = npy.argmin(dis1)
                    dis2 = npy.sqrt(npy.sum((new_bif_points[:, :3] - data[0, :3]) ** 2, axis = 1))
                    ind2 = npy.argmin(dis2)
                    if dis1[ind1] < dis2[ind2]:
                        data_add = resampled_points[0][npy.where((npy.round(resampled_points[0][:, -1]) == ind1) & (resampled_points[0][:, 2] >= zmin - 1))]
                    else:
                        data_add = new_bif_points[ind2, :].reshape(1, -1)
                    data = npy.append(data_add[:-1, :], data, axis = 0)
                    
                count = data.shape[0]
                if count == 0:
                    continue
                points = vtk.vtkPoints()
                for i in range(count):
                    points.InsertPoint(i, data[i, 0], data[i, 1], data[i, 2])
        
                para_spline = vtk.vtkParametricSpline()
                para_spline.SetPoints(points)
                para_spline.ClosedOff()
                
                znow = zmin
                old_pt = [0.0, 0.0, 0.0]
                numberOfOutputPoints = int((zmax - zmin + 3) * nn)
                
                for i in range(0, numberOfOutputPoints):
                    t = i * 1.0 / numberOfOutputPoints
                    pt = [0.0, 0.0, 0.0]
                    para_spline.Evaluate([t, t, t], pt, [0] * 9)
                    if pt[2] >= znow:
                        if pt[2] - znow < znow - old_pt[2]:
                            new_point = pt
                        else:
                            new_point = old_pt
                        trans_points = npy.append(trans_points, [[new_point[0], new_point[1], znow, cnt]], axis = 0)
                        znow += 1
                        if znow > zmax:
                            break
                    old_pt = pt
        
        '''
        # Reslice the result points(Discard the points near the bifurcation)
        for cnt in range(3):
            zmin = int(npy.ceil(npy.max(resampled_points[cnt][:nn, 2])))
            zmax = int(npy.min(resampled_points[cnt][-nn:, 2]))
            
            for k in range(0, nn):
                data = resampled_points[cnt][npy.where(npy.round(resampled_points[cnt][:, -1]) == k)]
                count = data.shape[0]
                if count == 0:
                    continue
                points = vtk.vtkPoints()
                for i in range(count):
                    points.InsertPoint(i, data[i, 0], data[i, 1], data[i, 2])
        
                para_spline = vtk.vtkParametricSpline()
                para_spline.SetPoints(points)
                para_spline.ClosedOff()
                
                znow = zmin
                old_pt = [0.0, 0.0, 0.0]
                numberOfOutputPoints = int((zmax - zmin + 1) * nn)
                
                for i in range(0, numberOfOutputPoints):
                    t = i * 1.0 / numberOfOutputPoints
                    pt = [0.0, 0.0, 0.0]
                    para_spline.Evaluate([t, t, t], pt, [0] * 9)
                    if pt[2] >= znow:
                        if pt[2] - znow < znow - old_pt[2]:
                            new_point = pt
                        else:
                            new_point = old_pt
                        trans_points = npy.append(trans_points, [[new_point[0], new_point[1], znow, cnt]], axis = 0)
                        znow += 1
                        if znow > zmax:
                            break
                    old_pt = pt
        '''
        
        moving_center = movingData.getPointSet('Centerline').copy()
        result_center_points = npy.array([[-1, -1, -1, -1]], dtype = npy.float32)
        if moving_center.shape[0] > 1:
            result_center = moving_center[npy.where(moving_center[:, 0] >= 0)]
            result_center[:, :3] *= moving_res[:3]
            temp = ml.mat(result_center[:, :3]) * R + ml.ones((result_center.shape[0], 1)) * T.T
            result_center[:, :3] = temp
            result_center[:, :3] /= fixed_res[:3]
            ind = result_center[:, 2].argsort()
            result_center = result_center[ind]
            
            result_center_points = npy.array([[-1, -1, -1, -1]], dtype = npy.float32)
            for cnt in range(3):
                resampled_points = result_center[npy.where(npy.round(result_center[:, -1]) == cnt)]
                zmin = int(npy.ceil(resampled_points[0, 2]))
                zmax = int(resampled_points[-1, 2])
                
                count = resampled_points.shape[0]
                points = vtk.vtkPoints()
                for i in range(count):
                    points.InsertPoint(i, resampled_points[i, 0], resampled_points[i, 1], resampled_points[i, 2])
        
                para_spline = vtk.vtkParametricSpline()
                para_spline.SetPoints(points)
                para_spline.ClosedOff()
                
                znow = zmin
                old_pt = [0.0, 0.0, 0.0]
                numberOfOutputPoints = int((zmax - zmin + 1) * 10)
                
                for i in range(0, numberOfOutputPoints):
                    t = i * 1.0 / numberOfOutputPoints
                    pt = [0.0, 0.0, 0.0]
                    para_spline.Evaluate([t, t, t], pt, [0] * 9)
                    if pt[2] >= znow:
                        if pt[2] - znow < znow - old_pt[2]:
                            new_point = pt
                        else:
                            new_point = old_pt
                        result_center_points = npy.append(result_center_points, [[new_point[0], new_point[1], znow, cnt]], axis = 0)
                        znow += 1
                        if znow > zmax:
                            break
                    old_pt = pt
        
        T = -T
        T = R * T
        
        transform = sitk.Transform(3, sitk.sitkAffine)
        para = R.reshape(1, -1).tolist()[0] + T.T.tolist()[0]
        transform.SetParameters(para)
        
        movingImage = movingData.getSimpleITKImage()
        fixedImage = fixedData.getSimpleITKImage()
        resultImage = sitk.Resample(movingImage, fixedImage, transform, sitk.sitkLinear, 0, sitk.sitkFloat32)
        
        return sitk.GetArrayFromImage(resultImage), {'Contour': trans_points, 'Centerline': result_center_points}, para + [0, 0, 0]
            
def saveTransform(wfile, T, R):
    for i in range(3):
        wfile.write("%f " % T[i, 0])
    for i in range(3):
        for j in range(3):
            wfile.write("%f " % R[i, j])
    wfile.write("\n")
def applyTransformForPoints(points, moving_res, fixed_res, R, T):
    points *= moving_res[:3]
    temp = ml.mat(points) * R + ml.ones((points.shape[0], 1)) * T.T
    points = temp
    points /= fixed_res[:3]
    return points
