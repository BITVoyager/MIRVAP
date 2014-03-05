# -*- coding: utf-8 -*-
"""
Created on 2014-03-02

@author: Hengkai Guo
"""

from MIRVAP.Core.WidgetViewBase import RegistrationDataView

class FixedImageView(RegistrationDataView):
    def setWidgetView(self, widget):
        self.initView(self.parent.getData('fix'), widget)
    def getName(self):
        return "Fixed Image View"
