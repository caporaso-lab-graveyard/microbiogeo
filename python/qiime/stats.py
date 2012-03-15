#!/usr/bin/env python
# File created on 11 Mar 2012
from __future__ import division
import types

__author__ = "Michael Dwan"
__copyright__ = "Copyright 2011, The QIIME project"
__credits__ = ["Michael Dwan, Logan Knecht"]
__license__ = "GPL"
__version__ = "1.4.0-dev"
__maintainer__ = "Michael Dwan"
__email__ = "mgd25@nau.edu"
__status__ = "Development"
 
"""
This module provides functionality for the application of various statistical 
methods to QIIME formatted data sets.

The module provides classes, methods and functions that enable the user to
easily apply any number of statistical analyses and easily retrieve the 
results.
"""

# python.... AHHHHHHH!
class GradientStats(object):
    """ Top-level, abstract class; extensible for future, non-matrix based analyses """
    def __init__(self):
        pass

    def setMetadataMap(self, new_map):
        raise NotImplementedError("Method no implemented by abstract base.")

    def getMetadataMap(self):
        raise NotImplementedError("Method no implemented by abstract base.")

    def setDistanceMatrix(self, new_distmat):
        raise NotImplementedError("Method no implemented by abstract base.")

    def getDistanceMatrix(self):
        raise NotImplementedError("Method no implemented by abstract base.")

    def setCategories(self, new_categories):
        raise NotImplementedError("Method no implemented by abstract base.")

    def getCategories(self):
        raise NotImplementedError("Method no implemented by abstract base.")

    def runAnalysis(self):
        raise NotImplementedError("Method no implemented by abstract base.")

    def runAnalysis(self):
        raise NotImplementedError("Method no implemented by abstract base.")


class DistanceMatrixStats(GradientStats):
    """
    Author: Logan Knecht

    This class serves as a base class for the stats classes "CorrelationStats" and "CategoryStats". Those classes are extended from this class in order to provided consistent method use for similar classes. More specifically to provide the same runAnalysis method through out.

    Arguments:
    _distmat - this is an array used to store the distance matrix information being used with the methods that extend this bas class
    """
    _distmat = []

    def __init__(self):
        """
        Default constructor
        """
        super(DistanceMatrixStats, self).__init__()

    def runAnalysis(self):
        """ 
        This is the method that's extended to its children so that that there is a common point of entry for running each statistical method.
        """
        raise NotImplementedError("Should have implemented this")

class CorrelationStats(DistanceMatrixStats):
    """
    Author: Logan Knecht
  
    This is the CorrelationStats class. It's used in order to provide a base template for the correlation methods like Partial Mantel, Mantel, etc.
    """
    def __init__(self):
        """
        Default constructor
        """
        super(CorrelationStats, self).__init__()

    def getDistanceMatrices(self):
        """
        Returns the _distmat variable
        """
        return self._distmat
  
    def setDistanceMatrices(self, matrices):
        """
        Sets the _distmat object to be the new array matrices
  
        matrices - the new distance matrix being assigned to _distmat list 
        """
        #test case from michael used to verify type error
        if not isinstance(matrices, types.ListType):
            raise TypeError('Invalid type: the item passed in as the new list was not a list data type')

        self._distmat = matrices
  
    def runAnalysis(self):
        """ 
        This is the method that's extended to its children so that that there is a common point of entry for running each statistical method.
        """
        #TO DO: I guess there's supposed to be some sort of call to the parent to run this analysis
        raise NotImplementedError( "Method not implemented by abstract base" )

class CategoryStats(DistanceMatrixStats):
    """ Classes/Methods for categorical statistical analyses """

    _categories = []
    _metadata_map = None
  
    def __init__(self, mdmap, dm, cats):
        """ Called by a statistical method initializer when instanstiated. """ 
        self._distmat = dm
        self._metadata_map = mdmap
        self._categories = cats
    
    def setMetadataMap(self, new_map):
        """ Sets the instance's _metadata_map field to a new MetadataMap instance 
      
        Arguments:
          new_map - A MetadataMap object instance.
        """

        if not isinstance(new_map, self.__class__):
            raise TypeError('Invalid type: %s; not MetadataMap' % new_map.__class__.__name__)

        self._metadata_map = new_map

    def getMetadataMap(self):
        """ Gets the instance's _metadata_map field to a new, valid MetadataMap 
    
        The _metadata_map is returned as a MetadataMap class instance
        """
        return self._metadata_map

    def setDistanceMatrix(self, new_distmat):
        """ Sets the instance's _distmat field to a new DistanceMatrix instance 
    
        Arguments:
        new_distmat - A DistanceMatrix object instance.
        """

        if not isinstance(new_distmat, self.__class__):
            raise TypeError('Invalid type: %s; not DistanceMatrix' % new_distmat.__class__.__name__)

        self._distmat = new_distmat

    def getDistanceMatrix(self):
        """ Gets the instance's _distmat field to a new, valid DistanceMatrix 
    
        The _distmat is returned as a DistanceMatrix class instance
        """
        return self._distmat

    def setCategories(self, new_categories):
        """ Sets the instance's _categories field to a new list of strings representing
        categories in a QIIME mapping file.
    
        Arguments:
        new_categories - A list of category name strings.
        """
    
        for el in new_categories:
          if not isinstance(el, self.__class__):
            raise TypeError('Invalid category: not of type "string"')

        self._categories = new_categories

    def getCategories(self):
        """ Gets the instance's _categories field, a list of mapping file, category name strings """
        return self._categories

    def runAnalysis(self):
        raise NotImplementedError("Method no implemented by abstract base.")

