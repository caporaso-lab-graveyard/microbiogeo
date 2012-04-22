#!/usr/bin/env python
# File created on 17 Mar 2011
from __future__ import division

__author__ = "Greg Caporaso"
__copyright__ = "Copyright 2010, The QIIME project"
__credits__ = ["Greg Caporaso"]
__license__ = "GPL"
__version__ = "1.4.0-dev"
__maintainer__ = "Greg Caporaso"
__email__ = "gregcaporaso@gmail.com"
__status__ = "Development"
 

from qiime.util import make_option
from qiime.parse import parse_distmat, fields_to_dict
from qiime.format import format_p_value_for_num_iters
from qiime.util import (parse_command_line_parameters, 
                        get_options_lookup,
                        make_compatible_distance_matrices)

from python.qiime.parse import DistanceMatrix
from python.qiime.stats import Mantel, MantelCorrelogram, \
                              PartialMantel
from python.qiime.r_executor import RExecutor                              

options_lookup = get_options_lookup()

script_info = {}
script_info['brief_description'] = "Script for computing Mantel correlations between sets of distance matrices"
script_info['script_description'] = ""
script_info['script_usage'] = [("","Perform Mantel test on all pairs of four distance matrices, including 1000 Monte Carlo iterations. Write the output to mantel_out.txt.","%prog --method mantel -i weighted_unifrac_dm.txt,unweighted_unifrac_dm.txt,weighted_unifrac_even100_dm.txt,unweighted_unifrac_even100_dm.txt -o mantel_out.txt -n 1000")]
script_info['output_description']= ""
script_info['required_options'] = [\
 # Example required option
make_option('--method', help='Matrix Correletion method to be executed. Valid options: [mantel, partial_mantel, mantel_corr]'),
 make_option('-i','--input_dms',help='the input distance matrices, comma-separated'),\
 make_option('-o','--output_fp',help='the output filepath'),\
]
script_info['optional_options'] = [
 make_option('-n','--num_iterations',help='the number of iterations to perform',default=100,type='int'),
 make_option('-s','--sample_id_map_fp',
    help='Map of original sample ids to new sample ids [default: %default]',
    default=None),
make_option('-t','--tail_type',help='the type of tailed test to perform(1 or 2 tailed [default:%default]', default='two sided')
]
script_info['version'] = __version__

comment = """# Number of entries refers to the number of rows (or cols) 
# retained in each distance matrix after filtering the distance matrices 
# to include only those samples that were in both distance matrices. 
# p-value contains the correct number of significant digits.
"""

def main():
    option_parser, opts, args =\
       parse_command_line_parameters(**script_info)

    if opts.method == 'mantel':
        sample_id_map_fp = opts.sample_id_map_fp
        if sample_id_map_fp:
            sample_id_map = dict([(k,v[0]) \
            for k,v in fields_to_dict(open(sample_id_map_fp, "U")).items()])
        else:
            sample_id_map = None

        input_dm_fps = opts.input_dms.split(',')

        output_f = open(opts.output_fp,'w')

        #this is where the heading information is added, it accounts for the spacing between file names for the first two elements DM1 and DM2, but it doesn't fix the spacing between the actual number values
        output_f.write(comment)
        output_f.write('DM1')

        num_of_first_spaces = len(input_dm_fps[0])
        first_space_string = ""
        while(num_of_first_spaces > 0):
            first_space_string = first_space_string + " "
            num_of_first_spaces = num_of_first_spaces - 1
        output_f.write(first_space_string)

        output_f.write('\tDM2')

        num_of_second_spaces = len(input_dm_fps[1])
        second_space_string = ""
        while(num_of_second_spaces > 0):
            second_space_string = second_space_string + " "
            num_of_second_spaces = num_of_second_spaces - 1
        output_f.write(second_space_string)

        num_of_entries_column_header = "Number of entries"
        output_f.write("\t" + num_of_entries_column_header)
        output_f.write('\t')

        output_f.write('Mantel p-value\n')

        num_iterations = opts.num_iterations

        for i,fp1 in enumerate(input_dm_fps):
            for fp2 in input_dm_fps[i+1:]:
                #this is a relatively benign looking line of code, but a lot is going on in the background that isn't being seen. For starters it's parsing distance matrice files and returning the infomration as a list in an array, then it has it made compatable and returned yet again as a pair of data with the informations being (sample ids, distant matrix data)
                (dm1_labels, dm1), (dm2_labels, dm2) =\
                 make_compatible_distance_matrices(parse_distmat(open(fp1,'U')), parse_distmat(open(fp2,'U')), lookup=sample_id_map)
                if len(dm1_labels) < 2:
                    output_f.write('%s\t%s\t%d\tToo few samples\n' % (fp1,fp2,len(dm1_labels)))
                    continue

                #This takes in a distance matrix object for the dm1 and dm2 of Mantel
                m = Mantel(DistanceMatrix(dm1, dm1_labels, dm1_labels), DistanceMatrix(dm2, dm2_labels, dm2_labels), num_iterations, opts.tail_type)
        
        #print "dm1 size: %d" % len(dm1)
        #print "dm1_labels size: %d" % len(dm1_labels)
        #print "dm2 size: %d" % len(dm2)
        #print "dm2_labels size: %d" % len(dm2_labels)
        #print dm1
        #print dm2
        #print dm1_labels
        #print dm2_labels

        resultsDict = {}
        resultsDict = m.runAnalysis()
        resultsDict['DM1_file_name'] = input_dm_fps[0] 
        resultsDict['DM2_file_name'] = input_dm_fps[1] 
        resultsDict['sample_size'] = len(dm1_labels)

        p_str = format_p_value_for_num_iters(resultsDict['p_value'],num_iterations)

        output_f.write(resultsDict['DM1_file_name'])
        output_f.write("\t")

        output_f.write(resultsDict['DM2_file_name'])
        output_f.write("\t")

        #fixes space issues for formatting
        third_word_spaces_needed = len("Number of entries") - len(dm1_labels)
        third_word_spaces = "" 
        while(third_word_spaces_needed > 0):
            third_word_spaces_needed = third_word_spaces_needed - 1
            third_word_spaces = third_word_spaces + " "
        output_f.write(str(resultsDict['sample_size']))
        output_f.write(third_word_spaces)
        output_f.write("\t")

        output_f.write(p_str)

        output_f.write("\n")
        output_f.close()

if __name__ == "__main__":
    main()