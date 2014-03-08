# -*- coding: utf-8 -*-
"""
Created on 2014-03-08

@author: Hengkai Guo
"""

from MIRVAP.Core.WidgetViewBase import RegistrationDataView
import vtk
import itk

class ImageBlendView(RegistrationDataView):
    '''
        Press Up/Down Key: Increase/Decrease the number of checkerboard division
    '''
    def __init__(self, parent = None):
        super(ImageBlendView, self).__init__(parent)
    def setWidgetView(self, widget):
        self.initView(self.parent.getData('fix'), widget)
    def getName(self):
        return "Image Blend View"
        
    def initView(self, data, widget):
        image_type = data.getITKImageType()
        self.image = data.getITKImage()
        self.space = data.getResolution().tolist()
        
        if len(self.space) == 3:
            self.space = [float(x) / self.space[-1] for x in self.space]
        
        self.image.SetSpacing(self.space)
        
        self.itk_vtk_converter = itk.ImageToVTKImageFilter[image_type].New()
        self.itk_vtk_converter.SetInput(self.image)
        self.image_resample = vtk.vtkImageResample()
        self.image_resample.SetInput(self.itk_vtk_converter.GetOutput())
        
        data = self.parent.getData()
        image_type = data.getITKImageType()
        self.image2 = data.getITKImage()
        self.space2 = data.getResolution().tolist()
        
        if len(self.space2) == 3:
            self.space2 = [float(x) / self.space2[-1] for x in self.space2]
        self.image2.SetSpacing(self.space2)
        shapeList = data.getData().shape
        y, x = shapeList[-2], shapeList[-1]
        self.dimension = len(shapeList) == 2
        
        self.itk_vtk_converter2 = itk.ImageToVTKImageFilter[image_type].New()
        self.itk_vtk_converter2.SetInput(self.image2)
        self.image_resample2 = vtk.vtkImageResample()
        self.image_resample2.SetInput(self.itk_vtk_converter2.GetOutput())
        
        self.blend_filter = vtk.vtkImageBlend()
        self.blend_filter.AddInput(self.image_resample.GetOutput())
        self.blend_filter.AddInput(self.image_resample2.GetOutput())
        self.opacity = 0.5
        self.blend_filter.SetOpacity(0, 0.5)
        self.blend_filter.SetOpacity(1, 0.5)
        
        self.renderer = vtk.vtkRenderer()
        self.render_window = widget.GetRenderWindow()
        self.render_window.AddRenderer(self.renderer)
        
        self.reslice_mapper = vtk.vtkImageResliceMapper()
        self.reslice_mapper.SetInput(self.blend_filter.GetOutput())
        self.reslice_mapper.SliceFacesCameraOn()
        self.reslice_mapper.SliceAtFocalPointOn()
        self.reslice_mapper.JumpToNearestSliceOn()
        self.reslice_mapper.BorderOff()
        self.reslice_mapper.BackgroundOn()
        
        array = data.getData()
        self.minI = array.min()
        self.maxI = array.max()
        image_property = vtk.vtkImageProperty()
        image_property.SetColorWindow(self.maxI - self.minI)
        image_property.SetColorLevel((self.maxI + self.minI) / 2.0)
        image_property.SetAmbient(0.0)
        image_property.SetDiffuse(1.0)
        image_property.SetOpacity(1.0)
        image_property.SetInterpolationTypeToLinear()
        
        self.image_slice = vtk.vtkImageSlice()
        self.image_slice.SetMapper(self.reslice_mapper)
        self.image_slice.SetProperty(image_property)
        
        self.renderer.AddViewProp(self.image_slice)
        
        self.window_interactor = vtk.vtkRenderWindowInteractor()
        self.interactor_style = vtk.vtkInteractorStyleImage()
        self.interactor_style.SetInteractionModeToImage3D()
        self.window_interactor.SetInteractorStyle(self.interactor_style)
        self.render_window.SetInteractor(self.window_interactor)
        point_picker = vtk.vtkPointPicker()
        self.window_interactor.SetPicker(point_picker)
        
        self.render_window.GlobalWarningDisplayOff()
        self.render_window.Render()
        self.camera = self.renderer.GetActiveCamera()
        self.camera.ParallelProjectionOn()
        w, h = self.window_interactor.GetSize()
        if h * x * self.space[0] < w * y * self.space[1]:
            scale = y / 2.0 * self.space[1]
        else:
            scale = h * x  * self.space[0] / 2.0 / w
        self.camera.SetParallelScale(scale)
        point = self.camera.GetFocalPoint()
        dis = self.camera.GetDistance()
        self.camera.SetViewUp(0, -1, 0)
        self.camera.SetPosition(point[0], point[1], point[2] - dis)
        self.renderer.ResetCameraClippingRange()
        
        # View of image
        self.view = 2
                
        self.interactor_style.AddObserver("MouseMoveEvent", self.MouseMoveCallback)
        self.interactor_style.AddObserver("LeftButtonReleaseEvent", self.LeftButtonReleaseCallback)
        self.interactor_style.AddObserver("LeftButtonPressEvent", self.LeftButtonPressCallback)
        self.interactor_style.AddObserver("MiddleButtonPressEvent", self.MiddleButtonPressCallback)
        self.interactor_style.AddObserver("RightButtonPressEvent", self.RightButtonPressCallback)
        self.interactor_style.AddObserver("RightButtonReleaseEvent", self.RightButtonReleaseCallback)
        self.interactor_style.AddObserver("KeyPressEvent", self.KeyPressCallback)
        self.interactor_style.AddObserver("CharEvent", self.CharCallback)
        
        self.updateAfter()
        self.render_window.Render()
        
    def KeyPressCallback(self, obj, event):
        ch = self.window_interactor.GetKeySym()
        if ch == 'Up' or ch == 'Down':
            if ch == 'Up':
                d = 0.1
            else:
                d = -0.1
            self.opacity = min(max(0.0, self.opacity + d), 1.0)
            self.blend_filter.SetOpacity(1, self.opacity)
            self.render_window.Render()
            self.updateAfter()
            return
        super(ImageBlendView, self).KeyPressCallback(obj, event)
    def updateAfter(self, *arg):
        super(ImageBlendView, self).updateAfter(*arg)
        newMessage = "     Opacity: %0.1f" % self.opacity
        self.parent.gui.showMessageOnStatusBar(self.parent.gui.getMessageOnStatusBar() + newMessage)
