# -*- coding: utf-8 -*-
"""
Created on 2014-03-06

@author: Hengkai Guo
"""

from MIRVAP.Core.WidgetViewBase import WidgetViewBase
import vtk
import numpy as npy

class SurfaceView(WidgetViewBase):
    def __init__(self, parent = None):
        super(SurfaceView, self).__init__(parent)
        self.datatype = (3, )
    def getName(self):
        return "Surface View"
    def setWidgetView(self, widget):
        # The pointset need to be interpolated into spline
        point_array = self.parent.getData().pointSet
        point_data = point_array.getData('Contour')
        if point_data is None or not point_data.shape[0]:
            return
        zmin = int(npy.min(point_data[:, 2]) + 0.5)
        zmax = int(npy.max(point_data[:, 2]) + 0.5)
        #self.spacing = [1, 1, 1]
        self.spacing = self.parent.getData().getResolution().tolist()[::-1]
        self.spacing = [float(x) / self.spacing[-1] for x in self.spacing]
        
        self.renderer = vtk.vtkRenderer()
        self.render_window = widget.GetRenderWindow()
        self.render_window.AddRenderer(self.renderer)
        self.window_interactor = vtk.vtkRenderWindowInteractor()
        self.render_window.SetInteractor(self.window_interactor)
        
        self.contours = []
        self.contour_mapper = []
        self.contours_actor = []
        self.contour_to_surface = []
        self.surface_mapper = []
        self.surface_actor = []
        
        for cnt in range(3):
            self.contours.append(vtk.vtkPolyData())
            self.contour_mapper.append(vtk.vtkPolyDataMapper())
            self.contours_actor.append(vtk.vtkActor())
            self.contour_to_surface.append(vtk.vtkVoxelContoursToSurfaceFilter())
            self.surface_mapper.append(vtk.vtkPolyDataMapper())
            self.surface_actor.append(vtk.vtkActor())
            point = point_data[npy.where(npy.round(point_data[:, -1]) == cnt)]
            if not point.shape[0]:
                continue
            k = 0
            self.cells = vtk.vtkCellArray()
            self.points = vtk.vtkPoints()
            
            for i in range(zmin, zmax + 1):
                data = point[npy.where(npy.round(point[:, 2]) == i)]
                if data is not None:
                    if data.shape[0] == 0:
                        continue
                    data = npy.round(data)
                    count = data.shape[0]
                    self.cells.InsertNextCell(count)
                    for j in range(count):
                        self.points.InsertPoint(k, data[j, 0], data[j, 1], data[j, 2])
                        self.cells.InsertCellPoint(k)
                        k += 1
                    
            self.contours[cnt].SetPoints(self.points)
            self.contours[cnt].SetPolys(self.cells)
            
            self.contour_mapper[cnt].SetInput(self.contours[cnt])
            self.contour_mapper[cnt].ScalarVisibilityOff()
            
            self.contours_actor[cnt].SetMapper(self.contour_mapper[cnt])
            self.contours_actor[cnt].GetProperty().SetRepresentationToWireframe()
            self.renderer.AddViewProp(self.contours_actor[cnt])
            
            self.contour_to_surface[cnt].SetInput(self.contours[cnt])
            self.contour_to_surface[cnt].SetSpacing(self.spacing[0], self.spacing[1], self.spacing[2])
            self.contour_to_surface[cnt].SetMemoryLimitInBytes(100000)
            self.contour_to_surface[cnt].Update()
            
            self.surface_mapper[cnt].SetInputConnection(self.contour_to_surface[cnt].GetOutputPort())
            self.surface_mapper[cnt].ScalarVisibilityOff()
            self.surface_mapper[cnt].ImmediateModeRenderingOn()
            
            self.surface_actor[cnt].SetMapper(self.surface_mapper[cnt])
            color = [0, 0, 0]
            color[cnt] = 1
            self.surface_actor[cnt].GetProperty().SetDiffuseColor(color[0], color[1], color[2])
            self.surface_actor[cnt].GetProperty().SetSpecularColor(1, 1, 1)
            self.surface_actor[cnt].GetProperty().SetSpecular(0.4)
            self.surface_actor[cnt].GetProperty().SetSpecularPower(50)
            
            self.renderer.AddViewProp(self.surface_actor[cnt])
            self.contours_actor[cnt].VisibilityOff()
        
        self.renderer.ResetCamera()
        point = self.renderer.GetActiveCamera().GetFocalPoint()
        dis = self.renderer.GetActiveCamera().GetDistance()
        self.renderer.GetActiveCamera().SetViewUp(0, 0, 1)
        self.renderer.GetActiveCamera().SetPosition(point[0], point[1] - dis, point[2])
        self.renderer.ResetCameraClippingRange()
        self.render_window.Render()
        
        # Manually set to trackball style
        self.window_interactor.SetKeyCode('t')
        self.window_interactor.CharEvent()
        self.window_interactor.GetInteractorStyle().AddObserver("KeyPressEvent", self.KeyPressCallback)
        self.window_interactor.GetInteractorStyle().AddObserver("CharEvent", self.KeyPressCallback)
        
    def KeyPressCallback(self, obj, event):
        pass
        
