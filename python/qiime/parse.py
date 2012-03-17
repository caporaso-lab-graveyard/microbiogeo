#!/usr/bin/env python
from __future__ import division

__author__ = "Jai Ram Rideout"
__copyright__ = "Copyright 2011, The QIIME project"
__credits__ = ["Jai Ram Rideout", "Logan Knecht"]
__license__ = "GPL"
__version__ = "1.4.0-dev"
__maintainer__ = "Jai Ram Rideout"
__email__ = "jr378@nau.edu"
__status__ = "Development"

"""Provides functionality for parsing and manipulating QIIME data files.

This module provides functions and classes that allow one to easily parse
native QIIME data files into in-memory data structures that allow access to and
manipulation of the data.
"""

from biom.table import DenseTable
from qiime.parse import parse_distmat, parse_mapping_file_to_dict

class DistanceMatrix(DenseTable):
    """This class represents a QIIME distance matrix."""
    _biom_type = "Distance matrix"

    @staticmethod
    def parseDistanceMatrix(lines):
        """Parses a QIIME distance matrix file into a DistanceMatrix object.
        
        This static method is basically a factory that reads in the given
        distance matrix file contents and returns a DistanceMatrix instance.
        This method is provided for convenience.

        Arguments:
            lines - a list of strings representing the file contents of a QIIME
                distance matrix.
        """
        sample_ids, matrix_data = parse_distmat(lines)
        return DistanceMatrix(matrix_data, sample_ids, sample_ids)

    def __init__(self, *args, **kwargs):
        """Instantiates a DistanceMatrix object.

        A distance matrix must be square and its sample IDs are exactly the
        same as its observation IDs (a biom table has sample IDs for column
        labels and observation IDs for row labels). A distance matrix must be
        at least 1x1 in size.

        Please refer to the biom.table.Table class documentation for a list of
        acceptable arguments to the constructor. The data matrix argument (the
        first argument) is expected to be a numpy array.
        
        We have to match the parent class constructor exactly in this case due
        to how many of the parent class methods are implemented (they assume
        all subclasses have the same constructor signature). Otherwise, I would
        have just made a simple constructor that took the matrix data and a
        single list of sample IDs (because the row/col IDs are the same for a
        distance matrix). As there is no easy way around this at the moment,
        users of this class must pass the same list of sample IDs as the
        observation IDs parameter as well.
        """
        super(DistanceMatrix, self).__init__(*args, **kwargs)

        # Make sure the matrix isn't empty, is square, and our sample IDs match
        # the observation IDs.
        data_matrix = args[0]
        if 0 in data_matrix.shape:
            raise ValueError("The input data matrix must be at least 1x1 in "
                             "size.")
        if data_matrix.shape[0] != data_matrix.shape[1]:
            raise ValueError("The input distance matrix must be square.")
        if self.SampleIds != self.ObservationIds:
            raise ValueError("The sample IDs must match the observation IDs.")

        self._size = data_matrix.shape[0]

    def getSize(self):
        """Returns the number of rows/columns in the matrix as an integer.

        Since all distance matrices are square, only a single number needs to
        be returned.
        """
        return self._size

    def flatten(self, lower=True):
        """Returns a list containing the flattened distance matrix.

        The returned list will contain the elements in column-major order
        (i.e. from leftmost to rightmost column, starting from the first row).
        Only the lower triangular elements will be included if lower is True
        (the diagonal will not be included). If lower is False, all elements
        (including the diagonal) will be included.
        """
        flattened = []
        for col_num in range(self.getSize()):
            for row_num in range(self.getSize()):
                if lower:
                    if col_num < row_num:
                        flattened.append(self[row_num][col_num])
                else:
                    flattened.append(self[row_num][col_num])
        return flattened
        

class MetadataMap():
    """This class represents a QIIME metadata mapping file."""

    @staticmethod
    def parseMetadataMap(lines):
        """Parses a QIIME metadata mapping file into a MetadataMap object.
        
        This static method is basically a factory that reads in the given
        metadata mapping file contents and returns a MetadataMap instance. This
        method is provided for convenience.

        Arguments:
            lines - a list of strings representing the file contents of a QIIME
                metadata mapping file.
        """
        return MetadataMap(*parse_mapping_file_to_dict(lines))

    def __init__(self, sample_metadata, comments):
        """Instantiates a MetadataMap object.
        
        Arguments:
            sample_metadata - the output of parse_mapping_file_to_dict(). It
                expects a python dict of dicts, where the top-level key is
                sample ID, and the inner dict maps category name to category
                value. This can be an empty dict altogether or the inner dict
                can be empty.
            comments - the output of parse_mapping_file_to_dict(). It expects a
                list of strings for the comments in the mapping file. Can be an
                empty list.
        """
        self._metadata = sample_metadata
        self._comments = comments

    def __eq__(self, other):
        """Test this instance for equality with another.

        Note: This code was taken from http://stackoverflow.com/questions/
            390250/elegant-ways-to-support-equivalence-equality-in-python-
            classes.
        """
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        """Test this instance for inequality with another.

        Note: This code was taken from http://stackoverflow.com/questions/
            390250/elegant-ways-to-support-equivalence-equality-in-python-
            classes.
        """
        return not self.__eq__(other)

    def getComments(self):
        """Returns the comments associated with this metadata map.

        The comments are returned as a list of strings, or an empty list if
        there are no comments.
        """
        return self._comments

    def getSampleMetadata(self, sampleId):
        """Returns the metadata associated with a particular sample.

        The metadata will be returned as a dict mapping category name to
        category value.

        Arguments:
            sampleId - the sample ID (string) to retrieve metadata for.
        """
        return self._metadata[sampleId]

    def getCategoryValue(self, sampleId, category):
        """Returns the category value associated with a sample's category.

        The returned category value will be a string.

        Arguments:
            sampleId - the sample ID (string) to retrieve category information
                for.
            category - the category name whose value will be returned.
        """
        return self._metadata[sampleId][category]
