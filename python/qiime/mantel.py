#!/usr/bin/env python
# File created on 17 Mar 2011
# Modified by Logan Knecht on 03/13/2012 (Converted from script to Mantel class)
from __future__ import division

import sys
sys.path.append("/home/ubuntu/")
sys.path.append("/home/ubuntu/biom-format-0.9.1/biom-format-0.9.1/python-code/biom/")


__author__ = "Greg Caporaso"
__copyright__ = "Copyright 2010, The QIIME project"
__credits__ = ["Greg Caporaso, Logan Knecht"]
__license__ = "GPL"
__version__ = "1.4.0"
__maintainer__ = "Greg Caporaso"
__email__ = "gregcaporaso@gmail.com"
__status__ = "Release"
 
from stats import CorrelationStats
from qiime.util import make_option
from qiime.parse import parse_distmat
from qiime.format import format_p_value_for_num_iters
from qiime.util import (parse_command_line_parameters, 
                        get_options_lookup,
                        make_compatible_distance_matrices)

from numpy import array, asarray, ravel, sqrt
from numpy.random import permutation

class Mantel(CorrelationStats):
    def __init__(self, initialDistanceMatrix1, initialDistanceMatrix2, num_iterates):
        self._num_iterations = num_iterates

        self._dm1 = initialDistanceMatrix1
        self._dm2 = initialDistanceMatrix2

        parameterMatrices = [self._dm1, self._dm2]
        super(MantelCorrelogram, self).setDistanceMatrices(parameterMatrices)

    def runAnalysis(self):
        m1, m2 = asarray(self._dm1), asarray(self._dm2)
        m1_flat = ravel(m1)
        size = len(m1)
        orig_stat = abs(self.pearson(m1_flat, ravel(m2)))
        better = 0
        for i in range(self._num_iterations):
            p2 = self.permute_2d(m2, permutation(size))
            r = abs(self.pearson(m1_flat, ravel(p2)))
            if r >= orig_stat:
                better += 1
        
        return better

    #This is a method was retrieved from the QIIME 1.4.0 release version, using amazon web services
    #Grabbed from the dir: /software/pycogent-1.5.1-release/lib/python2.7/site-packages/cogent/maths/stats
    #More specifically it was grabbed from the file called "test.py" 
    def pearson(self, x_items, y_items):
        """Returns Pearson correlation coefficient between x and y."""
        x_items, y_items = array(x_items), array(y_items)
        sum_x = sum(x_items)
        sum_y = sum(y_items)
        sum_x_sq = sum(x_items*x_items)
        sum_y_sq = sum(y_items*y_items)
        sum_xy = sum(x_items*y_items)
        n = len(x_items)
        try:
            r = 1.0 * ((n * sum_xy) - (sum_x * sum_y)) / \
               (sqrt((n * sum_x_sq)-(sum_x*sum_x))*sqrt((n*sum_y_sq)-(sum_y*sum_y)))
        except (ZeroDivisionError, ValueError, FloatingPointError): #no variation
            r = 0.0
        #check we didn't get a naughty value for r due to rounding error
        if r > 1.0:
            r = 1.0
        elif r < -1.0:
            r = -1.0
        return r
      
    #This is a method was retrieved from the QIIME 1.4.0 release version, using amazon web services
    #Grabbed from the dir: /software/pycogent-1.5.1-release/lib/python2.7/site-packages/cogent/maths/stats
    #More specifically it was grabbed from the file called "test.py"
    def permute_2d(self, m, p):
        """Performs 2D permutation of matrix m according to p."""
        return m[p][:, p]

    def getNumOfIterations(self):
        return self._num_iterations

    def setNumOfIterations(self, new_num_of_iterations):
        self._num_iterations = new_num_of_iterations

    def getDistanceMatrices(self):
        return [self._dm1, self._dm2]

    #Grabbed from mantel correlelogram, alt signature to use for the setter
    def setDistanceMatrices(self, matrices):
        if len(matrices) != 2:
            raise ValueError("Can only set exactly two distance matrices for a Mantel analysis.")
        super(Mantel, self).setDistanceMatrices(matrices)
