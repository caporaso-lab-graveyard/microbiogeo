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

    #def __init__(self, initialDistanceMatrix1, initialDistanceMatrix2, num_iterates):
        #self._num_iterations = num_iterates
        #self._dm1 = initialDistanceMatrix1
        #self._dm2 = initialDistanceMatrix2

    def __init__(self, initialDistanceMatrix1, initialDistanceMatrix2, num_iterates):
        self._num_iterations = num_iterates
        self._dm1 = initialDistanceMatrix1
        self._dm2 = initialDistanceMatrix2

    def runAnalysis(self, fp1, fp2, dm1_labels):
        resultsDict = {}

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
        
        p = better
        p_str = format_p_value_for_num_iters(p,self._num_iterations)
        output_str = ('%s\t%s\t%d\t%s\n' % (fp1, fp2, len(dm1_labels),p_str))
        #resultsDict['Results':('%s\t%s\t%d\t%s\n' % (fp1, fp2, len(dm1_labels),p_str))]
        resultsDict['Results'] = output_str

        return resultsDict

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

    def get_num_of_iterations(self):
        return self._num_iterations

    def set_num_of_iterations(self, new_num_of_iterations):
        self._num_iterations = new_num_of_iterations

    def get_distance_matrices(self):
        return [self._dm1, self._dm2]

    def set_distance_matrices(self, dm1, dm2):
        self._dm1 = dm1 
        self._dm2 = dm2 
