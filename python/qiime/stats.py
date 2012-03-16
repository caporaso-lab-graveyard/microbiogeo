#!/usr/bin/env python
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

class GradientStats(object):
    """Top-level, abstract base class for gradient statistical analyses.
    
    It exists to allow for extension to non-matrix based analyses.
    """

    def __init__(self):
        pass

    def runAnalysis(self):
        raise NotImplementedError("Method not implemented by abstract base.")


class DistanceMatrixStats(GradientStats):
    """Base class for distance matrix-based statistical methods.
    
    It is the parent class of CorrelationStats and CategoryStats. Those classes
    extend from this class in order to provided consistent method use for
    similar classes. More specifically to provide the same runAnalysis method
    throughout.
    """

    def __init__(self, distmats):
        """Default constructor.

        Arguments:
          distmats - a list of DistanceMatrix objects
        """
        super(DistanceMatrixStats, self).__init__()
        self._distmats = distmats

    def getDistanceMatrices(self):
        """Returns the list of distance matrices."""
        return self._distmats
  
    def setDistanceMatrices(self, matrices):
        """Sets the list of distance matrices to the supplied list.

        Arguments:
          matrices - the new list of distance matrices being assigned
        """
        if not isinstance(matrices, types.ListType):
            raise TypeError("Invalid type: the item passed in as the new list "
                            "was not a list data type")
        self._distmats = matrices


class CorrelationStats(DistanceMatrixStats):
    """Base class for distance matrix correlation statistical methods.
    
    It is subclassed by correlation methods like Partial Mantel, Mantel, etc..
    """

    def __init__(self, distmats):
        """Default constructor.
        
        Arguments:
          distmats - a list of DistanceMatrix objects
        """
        super(CorrelationStats, self).__init__(distmats)


class CategoryStats(DistanceMatrixStats):
    """Base class for categorical statistical analyses."""

    def __init__(self, mdmap, dm, cats):
        """Default constructor."""
        super(CategoryStats, self).__init__([dm])
        self._metadata_map = mdmap
        self._categories = cats
    
    def setMetadataMap(self, new_map):
        """Sets the instance's metadata map to a new MetadataMap instance.
      
        Arguments:
          new_map - A MetadataMap object instance.
        """
        if not isinstance(new_map, self.__class__):
            raise TypeError('Invalid type: %s; not MetadataMap' %
                            new_map.__class__.__name__)
        self._metadata_map = new_map

    def getMetadataMap(self):
        """Returns the instance's metadata map.
    
        The metadata map is returned as a MetadataMap class instance.
        """
        return self._metadata_map

    def setDistanceMatrix(self, new_distmat):
        """Sets the instance's distance matrix.
    
        Arguments:
          new_distmat - A DistanceMatrix object instance.
        """
        if not isinstance(new_distmat, self.__class__):
            raise TypeError('Invalid type: %s; not DistanceMatrix' %
                            new_distmat.__class__.__name__)
        self.setDistanceMatrices([new_distmat])

    def getDistanceMatrix(self):
        """Gets the instance's distance matrix.
    
        The distance matrix is returned as a DistanceMatrix class instance.
        """
        return self.getDistanceMatrices()[0]

    def setCategories(self, new_categories):
        """Sets the instance's list of categories to a new list of strings
        representing categories in a QIIME mapping file.
    
        Arguments:
          new_categories - A list of category name strings.
        """
        for el in new_categories:
          if not isinstance(el, self.__class__):
            raise TypeError('Invalid category: not of type "string"')
        self._categories = new_categories

    def getCategories(self):
        """Gets the instance's categories.
        
        Returns a list of mapping file category name strings.
        """
        return self._categories
