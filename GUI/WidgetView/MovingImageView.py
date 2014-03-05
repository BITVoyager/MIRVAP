# -*- coding: utf-8 -*-
"""
Created on 2014-03-02

@author: Hengkai Guo
"""

from MIRVAP.Core.WidgetViewBase import RegistrationDataView

class MovingImageView(RegistrationDataView):
    def setWidgetView(self, widget):
        self.initView(self.parent.getData('move'), widget)
    def getName(self):
        return "Moving Image View"
