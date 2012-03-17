#!/usr/bin/env python
from __future__ import division

__author__ = "Michael Dwan"
__copyright__ = "Copyright 2011, The QIIME project"
__credits__ = ["Michael Dwan", "Logan Knecht", "Jai Ram Rideout"]
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

from cogent.maths.stats.test import pearson, permute_2d
from math import ceil, log
from matplotlib import use
use('Agg', warn=False)
from matplotlib.pyplot import figure
from numpy import array, asarray, empty, ravel
from numpy.random import permutation
from types import ListType

from python.qiime.parse import DistanceMatrix

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
    
    It is the parent class of CorrelationStats and CategoryStats. They extend
    from this class in order to provided consistent method use for similar
    classes. More specifically to provide the same runAnalysis method
    throughout.
    """

    def __init__(self, distmats):
        """Default constructor.

        Arguments:
          distmats - a list of DistanceMatrix objects
        """
        super(DistanceMatrixStats, self).__init__()
        self.setDistanceMatrices(distmats)

    def getDistanceMatrices(self):
        """Returns the list of distance matrices."""
        return self._distmats
  
    def setDistanceMatrices(self, matrices):
        """Sets the list of distance matrices to the supplied list.

        Arguments:
          matrices - the new list of distance matrices being assigned
        """
        if not isinstance(matrices, ListType):
            raise TypeError("The item passed in as the new list was not a "
                            "list data type.")
        self._distmats = matrices


class CorrelationStats(DistanceMatrixStats):
    """Base class for distance matrix correlation statistical methods.
    
    It is subclassed by correlation methods like Partial Mantel and Mantel that
    compare two or more distance matrices. A valid instance of CorrelationStats
    must have at least one distance matrix, and all distance matrices must have
    matching dimensions and sample IDs (i.e. matching row/column labels).
    """

    def __init__(self, distmats):
        """Default constructor.
        
        Arguments:
          distmats - a list of DistanceMatrix objects
        """
        super(CorrelationStats, self).__init__(distmats)

    def setDistanceMatrices(self, matrices):
        if len(matrices) < 1:
            raise ValueError("Must provide at least one distance matrix.")

        size = matrices[0].getSize()
        sample_ids = matrices[0].SampleIds
        for dm in matrices:
            if dm.getSize() != size:
                raise ValueError("All distance matrices must have the same "
                                 "number of rows and columns.")
            if dm.SampleIds != sample_ids:
                raise ValueError("All distance matrices must have matching "
                                 "sample IDs.")
        super(CorrelationStats, self).setDistanceMatrices(matrices)


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


class MantelCorrelogram(CorrelationStats):
    def __init__(self, dm1, dm2, num_perms):
        super(MantelCorrelogram, self).__init__([dm1, dm2])
        self.setNumPermutations(num_perms)

    def getNumPermutations(self):
        return self._num_perms

    def setNumPermutations(self, num_perms):
        if num_perms >= 0:
            self._num_perms = num_perms
        else:
            raise ValueError("The number of permutations cannot be negative.")

    def setDistanceMatrices(self, matrices):
        if len(matrices) != 2:
            raise ValueError("Can only set exactly two distance matrices for "
                             "a Mantel correlogram analysis.")
        super(MantelCorrelogram, self).setDistanceMatrices(matrices)

    def runAnalysis(self):
        """Run a Mantel correlogram test over the current distance matrices.
        
        Note: This code is heavily based on the implementation of
        mantel.correlog in R's vegan package.
        """
        eco_dm = self.getDistanceMatrices()[0]
        geo_dm = self.getDistanceMatrices()[1]
        dm_size = eco_dm.getSize()

        # Find the number of lower/upper triangular elements (discounting the
        # diagonal).
        num_dists = dm_size * (dm_size - 1) // 2

        # Use Sturge's rule to determine the number of distance classes.
        num_classes = int(ceil(1 + log(num_dists, 2)))

        # Compute the breakpoints based on the number of distance classes.
        flattened_lower = geo_dm.flatten()
        start_point = min(flattened_lower)
        end_point = max(flattened_lower)
        width = (end_point - start_point) / num_classes
        break_points = []
        for class_num in range(num_classes):
            break_points.append(start_point + width * class_num)
        break_points.append(end_point)

        # Move the first breakpoint a little bit to the left. Machine epsilon
        # is take from:
        # http://en.wikipedia.org/wiki/Machine_epsilon#
        #     Approximation_using_Python
        epsilon = 2.2204460492503131e-16
        break_points[0] = break_points[0] - epsilon

        # Find the class indices (the midpoints between breakpoints).
        class_indices = []
        for bp_index, break_point in enumerate(break_points[0:num_classes]):
            next_bp = break_points[bp_index + 1]
            class_index = break_point + (0.5 * (next_bp - break_point))
            class_indices.append(class_index)

        # Create the matrix of distance classes.
        flattened_geo_dm = geo_dm.flatten(lower=False)
        dist_class_matrix = []
        for dm_ele in flattened_geo_dm:
            bps = [i for i, bp in enumerate(break_points) if bp >= dm_ele]
            dist_class_matrix.append(min(bps))

        # Start assembling the vectors of results.
        class_index = [None]
        num_dist = [None]
        mantel_r = [None]
        mantel_p = [None]

        # Create a model-matrix for each distance class, then compute a Mantel
        # test.
        for class_idx in range(num_classes):
            class_index.append(class_indices[class_idx])
            model_matrix_list = [0] * (dm_size ** 2)
            for ele_idx, ele in enumerate(dist_class_matrix):
                # Fix this hack so we don't need to add 1.
                if ele == (class_idx + 1):
                    model_matrix_list[ele_idx] = 1
            model_matrix = empty([dm_size, dm_size], dtype=int)
            # Convert vector into matrix, setting diagonal to zero.
            for idx, ele in enumerate(model_matrix_list):
                col_num = idx // dm_size
                row_num = idx % dm_size
                if row_num == col_num:
                    model_matrix[row_num][col_num] = 0
                else:
                    model_matrix[row_num][col_num] = ele
            model_matrix = DistanceMatrix(model_matrix, geo_dm.SampleIds,
                                          geo_dm.SampleIds)
            num_distances = int(model_matrix.sum())
            num_dist.append(num_distances)
            if num_distances == 0:
                mantel_r.append(None)
                mantel_p.append(None)
            else:
                row_sums = model_matrix.sum(axis='observation')
                row_sums = map(int, row_sums)
                # Fix this hack so we don't need to add 1.
                has_zero_sum = False
                for row_sum in row_sums:
                    if row_sum == 0:
                        has_zero_sum = True
                        break
                # Only stop running Mantel tests if we've gone through half of
                # the distance classes and at least one row has a sum of zero
                # (i.e. the sample doesn't have any distances that fall in the
                # current class).
                if not ((class_idx + 1) > (num_classes // 2) and has_zero_sum):
                    temp_p_val, orig_stat, perm_stats = self.mantel(
                        model_matrix._data, eco_dm._data,
                        self.getNumPermutations())
                    mantel_r.append(-orig_stat)

                    # The mantel() function produces a one-tailed p-value
                    # (H1: r>0). Here, compute a one-tailed p-value in the
                    # direction of the sign.
                    if orig_stat < 0:
                        perm_sum = sum([1 for ps in perm_stats \
                            if ps <= orig_stat]) + 1
                        temp_p_val = perm_sum / (self.getNumPermutations() + 1)
                    mantel_p.append(temp_p_val)
                else:
                    mantel_r.append(None)
                    mantel_p.append(None)

        results = {}
        results['method_name'] = 'Mantel Correlogram'
        results['class_index'] = class_index[1:]
        results['num_dist'] = num_dist[1:]
        results['mantel_r'] = mantel_r[1:]
        results['mantel_p'] = mantel_p[1:]
        
        # List mantel_p starts with a None value.
        mantel_p = mantel_p[1:]
        num_tests = len([p_val for p_val in mantel_p if p_val is not None])

        # Correct p-values for multiple testing using Bonferroni correction
        # (non-progressive).
        corrected_p_vals = [min(p * num_tests, 1) \
                            for p in mantel_p[0:num_tests]]
        corrected_p_vals.extend([None] * (num_classes - num_tests))
        results['mantel_p_corr'] = corrected_p_vals

        # Construct a matplotlib plot of distance class versus mantel
        # correlation statistic.
        fig = figure()
        ax = fig.add_subplot(111)
        ax.plot(results['class_index'], results['mantel_r'], 'ks-',
                mfc='white', mew=1)
        # Fill in each point that is significant (corrected p-value <= 0.05).
        signif_classes = []
        signif_stats = []
        for idx, p_val in enumerate(results['mantel_p_corr']):
            if p_val <= 0.05:
                signif_classes.append(results['class_index'][idx])
                signif_stats.append(results['mantel_r'][idx])
        ax.plot(signif_classes, signif_stats, 'ks', mfc='k')

        ax.set_title("Mantel Correlogram")
        ax.set_xlabel("Distance class index")
        ax.set_ylabel("Mantel correlation statistic")
        results['correlogram_plot'] = fig

        #fig.savefig('mantel_correlogram.png', format='png')

        return results
            
    def mantel(self, m1, m2, n):
        # This was ripped from pycogent and modified to provide the necessary
        # info. This will go away once the Mantel class is finished.
        m1, m2 = asarray(m1), asarray(m2)
        samp_ids = self.getDistanceMatrices()[0].SampleIds
        m1_dm = DistanceMatrix(m1, samp_ids, samp_ids)
        m2_dm = DistanceMatrix(m2, samp_ids, samp_ids)
        m1_flat = m1_dm.flatten()
        m2_flat = m2_dm.flatten()
        size = m1_dm.getSize()
        orig_stat = pearson(m1_flat, m2_flat)

        better = 0
        perm_stats = []
        for i in range(n):
            p2 = permute_2d(m2, permutation(size))
            p2_dm = DistanceMatrix(p2, samp_ids, samp_ids)
            p2_flat = p2_dm.flatten()
            r = pearson(m1_flat, p2_flat)
            perm_stats.append(r)
            if r >= orig_stat:
                better += 1
        return (better + 1) / (n + 1), orig_stat, perm_stats
