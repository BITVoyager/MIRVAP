# -*- coding: utf-8 -*-
"""
Created on 2014-06-06

@author: Hengkai Guo
"""

import numpy as npy
import scipy.interpolate as itp
from po_function import po_circle
from ac_function import ac_energy, ac_flattening, ac_normal, ac_amplitude, ac_deformation, ac_mask, ac_evolution, ac_mask_simple, ac_length, ac_area

def s_energy(acontour, image, flag = False):
    object_mask = ac_mask(acontour, image.shape)
    object_area = npy.sum(object_mask)
    if object_area == 0:
        object_mask = ac_mask_simple(acontour, image.shape)
        object_area = npy.sum(object_mask)
    
    object_mean = npy.sum(image[object_mask == 1]) / object_area
    backgnd_mean = npy.sum(image[object_mask == 0]) / (image.size - object_area)
    #print object_area, object_mean, backgnd_mean, image.size
    energy = npy.sum((image - backgnd_mean - (object_mean - backgnd_mean) * object_mask) ** 2)
    if not flag:
        return energy, object_mean, backgnd_mean
    else:
        return energy
def s_energy_area(acontour, image = None, flag = False):
    return ac_length(acontour)
def s_amplitude(vertices, image, object_mean, backgnd_mean):
    grid_x, grid_y = npy.mgrid[0:image.shape[0], 0:image.shape[1]]
    grid = npy.zeros([image.size, 2])
    grid[:, 0] = grid_x.flatten()
    grid[:, 1] = grid_y.flatten()
    image_at_vertices = itp.griddata(grid, image.flatten(), vertices.transpose())
    amplitude = (object_mean ** 2 - backgnd_mean ** 2) - (2 * (object_mean - backgnd_mean)) * image_at_vertices
    return amplitude
def s_amplitude_area(curvature, aclength, resolution):
    amplitude = -curvature + resolution * npy.sum(curvature) / aclength
    return amplitude
def ac_segmentation(center, frame, resolution = 4, amplitude_limit = 1, iteration_limit = 200, width_of_energy_window = 15, conv_slope = 5e-4):
    resolution = npy.floor(npy.mean(frame.shape) / 15)
    amplitude_limit = -npy.abs(resolution) / 2.5
    #amplitude_limit = 1.0
    #resolution = 10
    
    if center.ndim == 1:
        initial_acontour = po_circle(center, 3, 0, resolution)
    else:
        initial_acontour = center.transpose().copy()
        #print "Initial area: ", ac_area(initial_acontour, frame.shape)
        
    acontour = initial_acontour
    #direction = ac_normal(acontour)
    #amplitude = -npy.ones([2, acontour.shape[1] - 1], dtype = npy.float32)
    #acontour = ac_deformation(acontour, amplitude * direction, frame.shape, resolution)
    
    energy_class = ac_energy()
    evolution_class = ac_evolution()
    #while resolution > 1:
        #print "Resolution %d......" % resolution
    energy_class.start(width_of_energy_window, conv_slope)
    evolution_class.start(amplitude_limit)
    descending = True
    iteration = 1
    
    while descending and iteration <= iteration_limit and acontour.shape[1] > 0:
        energy, object_mean, backgnd_mean = s_energy(acontour, frame)
        #energy = s_energy_area(acontour)
        #print "   Iteration %d: energy %d, object_mean %d, backgnd_mean %d" % (iteration, energy, object_mean, backgnd_mean)
        print "   Iteration %d: energy %d" % (iteration, energy)
        #print "     Vertices: ", acontour
        if energy_class.store(energy):
            descending = False
        else:
            vertices = ac_flattening(acontour)
            direction = ac_normal(acontour)
            #direction, curvature = ac_normal(acontour, True)
            
            #print "     Direction: ", direction, "   Curvature: ", curvature
            amplitude = s_amplitude(vertices, frame, object_mean, backgnd_mean)
            #amplitude = s_amplitude_area(curvature, ac_length(acontour), resolution)
            #print "     Amplitude: ", amplitude
            if amplitude_limit > 0:
                amplitude, step = ac_amplitude(vertices, amplitude, amplitude_limit, frame.shape)
            else:
                amplitude, step = ac_amplitude(vertices, amplitude, amplitude_limit, frame.shape, acontour, direction, evolution_class.step(), energy, s_energy, resolution, frame)
                #amplitude, step = ac_amplitude(vertices, amplitude, amplitude_limit, frame.shape, acontour, direction, evolution_class.step(), energy, s_energy_area, resolution, frame)
            
            #print "     Delta: ", amplitude
            acontour = ac_deformation(acontour, amplitude * direction, frame.shape, resolution)
            evolution_class.store(amplitude, step)
            descending = (step > 0)
            iteration += 1
        
        #resolution -= 1
    #print "Final area: ", ac_area(acontour, frame.shape)
    return acontour
    
