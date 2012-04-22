#!/usr/bin/env python
# File created on 09 Feb 2010
from __future__ import division

__author__ = "Damien Coy"
__copyright__ = "Copyright 2011, The QIIME Project"
__credits__ = ["Damien Coy"]
__license__ = "GPL"
__version__ = "1.4.0"
__maintainer__ = "Damien Coy"
__email__ = "damien.coy@nau.edu"
__status__ = "Release"
 

from qiime.util import make_option
from os import makedirs, listdir
from os.path import join
from qiime.util import parse_command_line_parameters, get_options_lookup
from qiime.parse import parse_mapping_file
from python.qiime.r_executor import RExecutor
options_lookup = get_options_lookup()

import sys

script_info={}
script_info['brief_description']="""Run supervised classification using \
OTUs as predictors and a mapping file category as class labels."""
script_info['script_description']="""This script trains a supervised classifier using OTUs \
(or other continuous input sample x observation data) as predictors, and a \
mapping file column containing discrete values as the class labels.

Outputs:
    * cv_probabilities.txt: the label probabilities for each of the \
        given samples. (if available)
    * mislabeling.txt: A convenient presentation of cv_probabilities \
        for mislabeling detection.
    * confusion_matrix.txt: confusion matrix for hold-out predictions.
    * summary.txt: a summary of the results, including the expected \
        generalization error of the classifier
    * feature_importance_scores.txt: a list of discriminative OTUs with their \
        associated importance scores (if available)
    
It is recommended that you remove low-depth samples and rare OTUs \
before running this script. This can drastically reduce the run-time, and in \
many circumstances will not hurt performance. It is also recommended to perform \
rarefaction to control for sampling effort before running this \
script. For example, to rarefy at depth 200, then remove OTUs present in \
< 10 samples run:

single_rarefaction.py -i otu_table_filtered.txt -d 200 -o otu_table_rarefied200.txt
filter_otu_table.py -i otu_table_rarefied200.txt -s 10

For an overview of the application of supervised classification to microbiota, \
see PubMed ID 21039646.

This script requires that R be installed and in the search path. To install R \
visit: http://www.r-project.org/. Once R is installed, run R and excecute the \
command "install.packages("randomForest")", then type q() to exit."""

script_info['script_usage']=[]
script_info['script_usage'].append(("""Simple example of random forests classifier""","""""","""supervised_learning.py -i otutable.txt -m map.txt -c Individual -o ml"""))
script_info['script_usage'].append(("""Simple example, filter OTU table first""","""""","""
 single_rarefaction.py -i otu_table_filtered.txt -d 200 -o otu_table_rarefied200.txt
 filter_otu_table.py -i otu_table_rarefied200.txt -s 10
 supervised_learning.py -i otutable_filtered_rarefied200.txt -m map.txt -c 'Individual' -o ml"""))

script_info['script_usage'].append(("""Running with 10-fold cross-validation for improved estimates of generalization error and feature importances""","""""","""supervised_learning.py -i otutable.txt -m map.txt -c Individual -o ml -e cv10"""))
script_info['script_usage'].append(("""Running with 1,000 trees for improved generalization error""","""""","""supervised_learning.py -i otutable.txt -m map.txt -c Individual -o ml --ntree 1000"""))
script_info['output_description']="""Outputs a ranking of features (e.g. OTUs) by importance, an estimation of the generalization error of the classifier, and the predicted class labels and posterior class probabilities \
according to the classifier."""
script_info['required_options'] = [\
    make_option('-i', '--input_data', help='Input data file containing predictors (e.g. otu table)'),
    make_option('-m', '--mapping_file', help='File containing meta data (response variables)'),
    make_option('-c', '--category', help='Name of meta data category to predict'),
]

errortype_choices = ['oob','loo','cv5','cv10']

script_info['optional_options']=[\
    make_option('-o','--output_dir',default='.',\
            help='the output directory [deafult: %default]'),
    make_option('-f','--force',action='store_true',\
        dest='force',help='Force overwrite of existing output directory'+\
        ' (note: existing files in output_dir will not be removed)'+\
        ' [default: %default]'),
    make_option('--ntree',type='int',default=500,\
        help='Number of trees in forest (more is better but slower) [default: %default]'),
    make_option('-e', '--errortype',type='choice',default='oob',
        choices = errortype_choices,
        help='type of error estimation. Valid choices are: ' +\
            ', '.join(errortype_choices) + '. '+\
            'oob: out-of-bag, fastest, only builds one classifier, use for quick estimates; ' +\
            'cv5: 5-fold cross validation, provides mean and standard deviation of error, use for good estimates on very large data sets; ' +\
            'cv10: 10-fold cross validation, provides mean and standard deviation of error, use for best estimates; ' +\
            'loo: leave-one-out cross validation, use for small data sets (less than ~30-50 samples) ' +\
            '[default %default]')
]
script_info['version'] = __version__

def main():
    option_parser, opts, args = parse_command_line_parameters(**script_info)

    # create the output directories
    try:
        makedirs(opts.output_dir)
    except OSError:
        if opts.force:
            pass
        else:
            # This check helps users avoid overwriting previous output.
            print "Output directory already exists. Please choose "+\
             "a different directory, or force overwrite with -f."
            exit(1)

    # verify that category is in mapping file
    map_list = parse_mapping_file(open(opts.mapping_file,'U').readlines())
    if not opts.category in map_list[1][1:]:
        print "Category '%s' not found in mapping file columns:" %(opts.category)
        print map_list[1][1:]
        exit(1)

    distance_matrix = opts.input_data
    map_file = opts.mapping_file
    category = opts.category
    output = opts.output_dir

    # command_args = ["-i \"Documents/sim_data_glen_canyon/glen_canyon_.001/unweighted_unifrac_simsam_result.txt\" -m \"Documents/data_sets/map_25Jan2012.txt\" -c CurrentlyWet -o Documents/permdisp"]

    command_args = ["-i " + distance_matrix + " -m " + map_file + " -c " + category + " -o " + output]
    #sys.exit(command_args)

    rex = RExecutor()
    results = rex(command_args, "betadisper.r", output_dir=opts.output_dir, remove_tmp=True)
        
if __name__ == "__main__":
    main()
