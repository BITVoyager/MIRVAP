# -*- coding: utf-8 -*-
"""
Created on 2014-03-02

@author: Hengkai Guo
"""

from MIRVAP.Core.WidgetViewBase import RegistrationDataView
from MIRVAP.GUI.Plugin.ContourViewPlugin import ContourViewPlugin
from MIRVAP.GUI.Plugin.CenterViewPlugin import CenterViewPlugin

class FixedImageView(RegistrationDataView):
    def setWidgetView(self, widget):
        self.initView(self.parent.getData('fix'), widget)
        self.plugin = [ContourViewPlugin(), CenterViewPlugin()]
        self.plugin[0].enable(parent = self, key = 'fix', show = False)
        self.plugin[1].enable(parent = self, key = 'fix', show = False)
    def getName(self):
        return "Fixed Image View"
