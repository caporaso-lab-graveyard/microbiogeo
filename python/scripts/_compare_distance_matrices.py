#!/usr/bin/env python
# File created on 21 April 2012
from __future__ import division

__author__ = "Michael Dwan"
__copyright__ = "Copyright 2012, The QIIME project"
__credits__ = ["Michael Dwan, Jai Rideout, Logan Knecht"]
__license__ = "GPL"
__version__ = "1.4.0-dev"
__maintainer__ = "Michael Dwan"
__email__ = "mdwan.tgen@gmail.com"
__status__ = "Development"
 

from os import path

from cogent.util.misc import create_dir

from qiime.parse import parse_distmat, fields_to_dict
from qiime.format import format_p_value_for_num_iters
from qiime.util import (parse_command_line_parameters, 
                        get_options_lookup,
                        make_compatible_distance_matrices,
                        make_option)

from python.qiime.parse import DistanceMatrix
from python.qiime.stats import Mantel, MantelCorrelogram, \
                              PartialMantel

options_lookup = get_options_lookup()

script_info = {}
script_info['brief_description'] = "Script for computing Mantel correlations between sets of distance matrices"
script_info['script_description'] = ""
script_info['script_usage'] = [("","Perform Mantel test on all pairs of four distance matrices, including 1000 Monte Carlo iterations. Write the output to mantel_out.txt.","%prog --method mantel -i weighted_unifrac_dm.txt,unweighted_unifrac_dm.txt,weighted_unifrac_even100_dm.txt,unweighted_unifrac_even100_dm.txt -o mantel_out.txt -n 1000")]
script_info['output_description']= ""
script_info['required_options'] = [\
 # All methods use these
make_option('--method', help='Matrix Correletion method to be executed. Valid options: [mantel, partial_mantel, mantel_corr]'),
 make_option('-i','--input_dms',help='the input distance matrices, comma-separated'),\
 make_option('-o','--output_dir',help='the output directory [default: %default]', default='.'),\
]
script_info['optional_options'] = [
 # All methods use these
 make_option('-n','--num_permutations',help='the number of iterations to perform',default=100,type='int'),
 make_option('-s','--sample_id_map_fp',
    help='Map of original sample ids to new sample ids [default: %default]',
    default=None),
 # Standard Mantel specific, i.e., method == mantel
make_option('-t','--tail_type',help='the type of tailed test to perform(1 or 2 tailed [default:%default]', default='two sided'),
 # Mantel Correlogram specific, i.e., method == mantel_corr
make_option('-a', '--alpha',
    help='the value of alpha to use when denoting significance in the '
         'correlogram plot', default=0.05, type='float'),
make_option('-g', '--image_type',
    help='type of image to produce (i.e. png, svg, pdf) '
         '[default: %default]', default='pdf', type="choice",
    choices=['pdf', 'png', 'svg']),
 # Partial Mantel specific, i.e., method == partial_mantel
    make_option('-c', '--control_dm',
        help='the control matrix, [default: %default]', default=None),

]
script_info['version'] = __version__

comment_mantel_pmantel = """# Number of entries refers to the number of rows (or cols)
# retained in each distance matrix after filtering the distance matrices 
# to include only those samples that were in both distance matrices. 
# p-value contains the correct number of significant digits.
"""

comment_corr = """# Number of entries refers to the number of rows (or cols) 
# retained in each distance matrix after filtering the distance matrices 
# to include only those samples that were in both distance matrices. 
# p-value contains the correct number of significant digits.
# Distance classes with values of None were in the second half of the distance
# classes and not all samples could be included in the distance class, so
# calculations were not performed.
"""

def main():
    option_parser, opts, args =\
       parse_command_line_parameters(**script_info)

    # Create the output dir if it doesn't already exist.
    try:
        if not path.exists(opts.output_dir):
            create_dir(opts.output_dir)
    except:
        option_parser.error("Could not create or access output directory "
                            "specified with the -o option.")

    sample_id_map_fp = opts.sample_id_map_fp
    if sample_id_map_fp:
        sample_id_map = dict([(k,v[0]) \
        for k,v in fields_to_dict(open(sample_id_map_fp, "U")).items()])
    else:
        sample_id_map = None

    input_dm_fps = opts.input_dms.split(',')


    if opts.method == 'mantel':
        output_f = open(path.join(opts.output_dir, "mantel_results.txt"), 'w')
        #this is where the heading information is added, it accounts for the spacing between file names for the first two elements DM1 and DM2, but it doesn't fix the spacing between the actual number values
        output_f.write(comment_corr)
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

        num_permutations = opts.num_permutations

        for i,fp1 in enumerate(input_dm_fps):
            for fp2 in input_dm_fps[i+1:]:
                #this is a relatively benign looking line of code, but a lot is going on in the background that isn't being seen. For starters it's parsing distance matrice files and returning the infomration as a list in an array, then it has it made compatable and returned yet again as a pair of data with the informations being (sample ids, distant matrix data)
                (dm1_labels, dm1), (dm2_labels, dm2) =\
                 make_compatible_distance_matrices(parse_distmat(open(fp1,'U')), parse_distmat(open(fp2,'U')), lookup=sample_id_map)
                if len(dm1_labels) < 2:
                    output_f.write('%s\t%s\t%d\tToo few samples\n' % (fp1,fp2,len(dm1_labels)))
                    continue

                #This takes in a distance matrix object for the dm1 and dm2 of Mantel
                m = Mantel(DistanceMatrix(dm1, dm1_labels, dm1_labels), DistanceMatrix(dm2, dm2_labels, dm2_labels), num_permutations, opts.tail_type)
        
                resultsDict = {}
                resultsDict = m.runAnalysis()
                resultsDict['DM1_file_name'] = fp1
                resultsDict['DM2_file_name'] = fp2
                resultsDict['sample_size'] = len(dm1_labels)

                p_str = format_p_value_for_num_iters(resultsDict['p_value'],num_permutations)

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

    elif opts.method == 'partial_mantel':
        num_perms = opts.num_permutations

        control_dm_fp = opts.control_dm
        res_file = open(path.join(opts.output_dir, "mantel_partial_results.txt"), 'w')
        res_file.write(comment_mantel_pmantel)

        (dm1_labels, dm1), (dm2_labels, dm2) = make_compatible_distance_matrices(
            parse_distmat(open(input_dm_fps[0], 'U')),
            parse_distmat(open(input_dm_fps[1], 'U')), lookup=sample_id_map)

        (dm1_labels, dm1), (cdm_labels, cdm) = make_compatible_distance_matrices(
            parse_distmat(open(input_dm_fps[0], 'U')),
            parse_distmat(open(control_dm_fp, 'U')), lookup=sample_id_map)

        # Output header to result file. 
        res_file.write('\nDM1: %s\nDM2: %s\nCM: %s\npermutations: %d\n' % (input_dm_fps[0], input_dm_fps[1], control_dm_fp, num_perms))

        # Construct a PartialMantel object.
        pm = PartialMantel(DistanceMatrix(dm1, dm1_labels, dm1_labels), 
                            DistanceMatrix(dm2, dm2_labels, dm2_labels), 
                            DistanceMatrix(cdm, cdm_labels, cdm_labels), num_perms)

        # Run the analysis.
        res = pm.runAnalysis()

        # Output statistic to result file.
        res_file.write('\nMantel stat(r-val)\tp-val\t')
        res_file.write('\n%f\t%f' % (res['mantel_r'], res['mantel_p']))
        res_file.close()

    elif opts.method == 'mantel_corr':
        num_perms = opts.num_permutations
        alpha = opts.alpha

        input_dm_fps = opts.input_dms.split(',')
        results_f = open(path.join(
            opts.output_dir, "mantel_correlogram_results.txt"), 'w')
        results_f.write(comment_mantel_pmantel)

        # Make the two distance matrices compatible before running the analysis.
        # This code was taken from Greg's compare_distance_matrices.py script.
        sample_id_map_fp = opts.sample_id_map_fp
        if sample_id_map_fp:
            sample_id_map = dict([(k,v[0]) \
             for k,v in fields_to_dict(open(sample_id_map_fp, "U")).items()])
        else:
            sample_id_map = None

        (dm1_labels, dm1), (dm2_labels, dm2) = make_compatible_distance_matrices(
            parse_distmat(open(input_dm_fps[0], 'U')),
            parse_distmat(open(input_dm_fps[1], 'U')), lookup=sample_id_map)
        if len(dm1_labels) < 3:
            option_parser.error("The distance matrices were not large enough "
                "after filtering them to include only samples that were in both "
                "matrices. The minimum required size to compute a Mantel "
                "correlogram is 3x3.")

        # Write header info to the results file.
        results_f.write('DM1: %s\nDM2: %s\nNumber of entries: %d\nNumber of '
            'permutations: %d\nAlpha: %s\n' % (input_dm_fps[0], input_dm_fps[1],
            len(dm1_labels), num_perms, alpha))

        # Construct a MantelCorrelogram object and run the analysis.
        results = MantelCorrelogram(DistanceMatrix(dm1, dm1_labels,
            dm1_labels), DistanceMatrix(dm2, dm2_labels, dm2_labels), num_perms,
            alpha=alpha).runAnalysis()

        # Write the correlogram plot to a file.
        results['correlogram_plot'].savefig(path.join(opts.output_dir,
            'mantel_correlogram.%s' % opts.image_type), format=opts.image_type)
        
        # Iterate over the results and write them to the text file.
        results_f.write('\nClass index\tNum dists\tMantel stat\tp-val\t'
            'p-val (Bonferroni corrected)\n')
        for class_idx, num_dist, r, p, p_corr in zip(results['class_index'],
            results['num_dist'], results['mantel_r'], results['mantel_p'],
            results['mantel_p_corr']):
            if p is not None:
                p_str = format_p_value_for_num_iters(p, num_perms)
            else:
                p_str = None
            if p_corr is not None:
                p_corr_str = format_p_value_for_num_iters(p_corr, num_perms)
            else:
                p_corr_str = None
            results_f.write('%s\t%d\t%s\t%s\t%s\n' % (class_idx, num_dist, r, p,
                p_corr))
        results_f.close()
    else:
        print "Method '%s' not recognized\n"%(opts.method)



if __name__ == "__main__":
    main()