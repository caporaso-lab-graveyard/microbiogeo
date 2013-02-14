#!/usr/bin/env python
from __future__ import division

__author__ = "Jai Ram Rideout"
__copyright__ = "Copyright 2013, The QIIME Project"
__credits__ = ["Jai Ram Rideout"]
__license__ = "GPL"
__version__ = "0.0.0-dev"
__maintainer__ = "Jai Ram Rideout"
__email__ = "jai.rideout@gmail.com"

"""Module for executing various workflows/analyses."""

from glob import glob
from os.path import exists, join
from shutil import copy

from IPython.parallel import Client

from numpy import median

from qiime.util import create_dir

from microbiogeo.format import create_results_summary_tables
from microbiogeo.parallel import (generate_per_study_depth_dms,
                                  build_grouping_method_commands,
                                  build_gradient_method_commands,
                                  build_gradient_method_keyboard_cmds)
from microbiogeo.parse import (parse_adonis_results,
                               parse_anosim_permanova_results,
                               parse_mantel_results,
                               parse_morans_i_results,
                               parse_partial_mantel_results)
from microbiogeo.util import run_command, StatsResults

def generate_distance_matrices(in_dir, out_dir, studies, metrics, num_shuffled,
                               num_subsets, tree_fp):
    """Generates distance matrices for each study.

    Distance matrices will be created at each even sampling depth and metric
    using the provided tree if necessary. Shuffled versions of each distance
    matrix will also be created, which can be used as negative controls.

    In addition, subsets of each distance matrix will be generated (based on a
    category's sample groupings or the entire distance matrix). These can be
    used to test how the methods perform on different study sizes.
    """
    # Process each depth in each study in parallel.
    c = Client()
    lview = c.load_balanced_view()
    lview.block = True

    create_dir(out_dir)

    per_study_depths = []
    for study in studies:
        # Prep per-study output directories before running each depth in
        # parallel.
        in_study_dir = join(in_dir, study)
        out_study_dir = join(out_dir, study)
        create_dir(out_study_dir)
        copy(join(in_study_dir, 'map.txt'), out_study_dir)
        map_fp = join(out_study_dir, 'map.txt')

        # Create distance matrices from environmental variables in mapping
        # file. These are independent of sampling depth and metric, so we only
        # need to create them once for each study. Again, keyboard is unique in
        # that we cannot easily create a key distance matrix from the mapping
        # file. We'll use one that has been precalculated.
        for category in studies[study]['gradient_categories']:
            env_dm_fp = join(out_study_dir, '%s_dm.txt' % category)

            cmd = ('distance_matrix_from_mapping.py -i %s -c %s -o %s' % (
                   map_fp, category, env_dm_fp))
            run_command(cmd)

        if study == 'keyboard':
            key_dm_fp = join(in_study_dir, 'euclidean_key_distances_dm.txt')
            copy(key_dm_fp, out_study_dir)

            indiv_dm_fp = join(in_study_dir,
                               'median_unifrac_individual_distances_dm.txt')
            copy(indiv_dm_fp, out_study_dir)

        for depth in studies[study]['depths']:
            per_study_depths.append((in_dir, out_dir, study, depth, metrics,
                                     studies[study]['grouping_categories'],
                                     studies[study]['gradient_categories'],
                                     studies[study]['group_sizes'],
                                     studies[study]['subset_sizes'],
                                     num_shuffled, num_subsets, tree_fp))

    lview.map(generate_per_study_depth_dms, per_study_depths)

def run_methods(in_dir, studies, methods, permutations):
    """Runs each statistical method on each distance matrix."""
    # Process each compare_categories.py/compare_distance_matrices.py run in
    # parallel.
    c = Client()
    lview = c.load_balanced_view()
    lview.block = True

    jobs = []
    for study in studies:
        for depth in studies[study]['depths']:
            for method_type in methods:
                for method in methods[method_type]:
                    study_dir = join(in_dir, study)
                    map_fp = join(study_dir, 'map.txt')
                    depth_dir = join(study_dir, 'bdiv_even%d' % depth)
                    dm_fps = glob(join(depth_dir, '*_dm*.txt'))

                    for dm_fp in dm_fps:
                        if method_type == 'grouping':
                            for category in \
                                    studies[study]['grouping_categories']:
                                jobs.extend(build_grouping_method_commands(
                                        depth_dir, dm_fp, map_fp, method,
                                        category, permutations))
                        elif method_type == 'gradient':
                            for category in \
                                    studies[study]['gradient_categories']:
                                jobs.extend(build_gradient_method_commands(
                                        study_dir, depth_dir, dm_fp, map_fp,
                                        method, category, permutations))

                            if study == 'keyboard':
                                jobs.extend(
                                    build_gradient_method_keyboard_commands(
                                            study_dir, depth_dir, dm_fp,
                                            method, permutations))
                        else:
                            raise ValueError("Unknown method type '%s'." %
                                             method_type)

    lview.map(run_command, jobs)

def summarize_results(in_dir, out_dir, studies, methods, depth_descs, metrics,
                      permutations, num_shuffled, num_subsets):
    """Summarizes the results of the various method runs.

    Effect size statistics and p-values are collected for each of the tests
    that were run and summary tables are created, one for each sampling depth /
    metric combination (separate tables for grouping and gradient analysis
    methods). These tables are written to out_dir.
    """
    results = _collate_results(in_dir, studies, methods, depth_descs, metrics,
                               permutations, num_shuffled, num_subsets)
    create_results_summary_tables(results, out_dir)

def _collate_results(in_dir, studies, methods, depth_descs, metrics,
                     permutations, num_shuffled, num_subsets):
    results = {}

    for depth_idx, depth_desc in enumerate(depth_descs):
        depth_res = {}

        for metric in metrics:
            metric_res = {}

            for method_type in methods:
                method_type_res = {}

                for method, res_parsing_fn in methods[method_type].items():
                    if method in ('mantel_corr', 'best'):
                        # Completely ignore Mantel correlogram and BEST (for
                        # now at least). Mantel correlogram is hard to
                        # summarize because it produces a correlogram and many
                        # Mantel statistics for each distance class. We'll need
                        # to look at those results by hand and summarize them
                        # in the paper. The same holds for BEST: though it does
                        # not create a visual plot, it does not provide
                        # p-values. It mainly tells you which environmental
                        # variables best correlate with the community data.
                        continue

                    method_res = {}

                    for study in studies:
                        study_res = {}

                        # Figure out what our actual depth is for the study,
                        # and what subset sizes we used.
                        depth = studies[study]['depths'][depth_idx]

                        if method_type == 'grouping':
                            subset_sizes = studies[study]['group_sizes']
                            categories = studies[study]['grouping_categories']
                        elif method_type == 'gradient':
                            subset_sizes = studies[study]['subset_sizes']

                            # Add our fictional 'key_distance' category, which
                            # isn't actually a category (i.e. not in a mapping
                            # file), but can be treated the same way as the
                            # others in this case.
                            categories = studies[study]['gradient_categories']\
                                    + ['key_distance']
                        else:
                            raise ValueError("Unknown method type '%s'." %
                                             method_type)

                        for category in categories:
                            category_res = {}
                            full_results = StatsResults()
                            shuffled_results = StatsResults()
                            ss_results = [StatsResults()
                                          for i in range(len(subset_sizes))]

                            # Moran's I does not use permutations.
                            if method == 'morans_i':
                                _collate_category_results(full_results,
                                        shuffled_results, ss_results, in_dir,
                                        study, depth, metric, method_type,
                                        method, res_parsing_fn, category,
                                        subset_sizes, num_shuffled,
                                        num_subsets, permutation=None)
                            else:
                                for permutation in permutations:
                                    _collate_category_results(full_results,
                                            shuffled_results, ss_results,
                                            in_dir, study, depth, metric,
                                            method_type, method,
                                            res_parsing_fn, category,
                                            subset_sizes, num_shuffled,
                                            num_subsets,
                                            permutation=permutation)

                            category_res['full'] = full_results
                            category_res['shuffled'] = shuffled_results
                            category_res['subsampled'] = ss_results

                            study_res[category] = category_res
                        method_res[study] = study_res
                    method_type_res[method] = method_res
                metric_res[method_type] = method_type_res
            depth_res[metric] = metric_res
        results[depth_desc] = depth_res

    return results

def _collate_category_results(full_results, shuffled_results, ss_results,
                              in_dir, study, depth, metric, method_type,
                              method, results_parsing_fn, category,
                              subset_sizes, num_shuffled, num_subsets,
                              permutation=None):
    depth_dir = join(in_dir, study, 'bdiv_even%d' % depth)

    # Collect results for full distance matrices.
    results_dir = join(depth_dir, '%s_dm_%s_%s' % (metric, method, category))
    if permutation is not None:
        results_dir += '_%d' % permutation

    results_fp = join(results_dir, '%s_results.txt' % method)

    # We will not always have results for every combination of parameters (e.g.
    # partial Mantel).
    if exists(results_fp):
        full_res_f = open(results_fp, 'U')
        full_es, full_p_val = results_parsing_fn(full_res_f)
        full_res_f.close()
        full_results.addResult(full_es, full_p_val)

    # Collect results for shuffled distance matrices.
    shuff_ess = []
    shuff_p_vals = []
    for shuff_num in range(1, num_shuffled + 1):
        results_dir = join(depth_dir, '%s_dm_shuffled%d_%s_%s' % (metric,
                                                                  shuff_num,
                                                                  method,
                                                                  category))
        if permutation is not None:
            results_dir += '_%d' % permutation

        results_fp = join(results_dir, '%s_results.txt' % method)

        if exists(results_fp):
            shuff_res_f = open(results_fp, 'U')
            shuff_es, shuff_p_val = results_parsing_fn(shuff_res_f)
            shuff_res_f.close()
            shuff_ess.append(shuff_es)
            shuff_p_vals.append(shuff_p_val)

    if shuff_ess and shuff_p_vals:
        shuffled_results.addResult(median(shuff_ess), median(shuff_p_vals))

    # Collect results for subset distance matrices.
    for subset_size_idx, subset_size in enumerate(subset_sizes):
        ss_ess = []
        ss_p_vals = []

        for ss_num in range(1, num_subsets + 1):
            if method_type == 'grouping':
                subset_path = '%s_dm_%s_gs%d_%d_%s_%s' % (metric, category,
                                                          subset_size, ss_num,
                                                          method, category)
            elif method_type == 'gradient':
                subset_path = '%s_dm_n%d_%d_%s_%s' % (metric, subset_size,
                                                      ss_num, method, category)
            else:
                raise ValueError("Unknown method type '%s'." % method_type)

            results_dir = join(depth_dir, subset_path)
            if permutation is not None:
                results_dir += '_%d' % permutation

            results_fp = join(results_dir, '%s_results.txt' % method)

            if exists(results_fp):
                ss_res_f = open(results_fp, 'U')
                ss_es, ss_p_val = results_parsing_fn(ss_res_f)
                ss_res_f.close()
                ss_ess.append(ss_es)
                ss_p_vals.append(ss_p_val)

        if ss_ess and ss_p_vals:
            ss_results[subset_size_idx].addResult(
                    median(ss_ess), median(ss_p_vals))

def main():
    in_dir = 'test_datasets'
    out_dir = 'test_output'
    tree_fp = join('test_datasets', 'overview', 'rep_set.tre')
    depth_descs = ['5_percent', '25_percent', '50_percent']
    studies = {
               'overview': {
                            'depths': [50, 100, 146],
                            'grouping_categories': ['Treatment'],
                            'gradient_categories': ['DOB'],
                            'group_sizes': [3, 4],
                            'subset_sizes': [3, 4],
                            'best_method_env_vars': ['DOB']
                           },
               'overview2': {
                             'depths': [50, 100, 146],
                             'grouping_categories': ['Treatment'],
                             'gradient_categories': [],
                             'group_sizes': [3, 4],
                             'subset_sizes': [],
                             'best_method_env_vars': []
                            }
              }
    metrics = ['euclidean', 'bray_curtis']
    methods = {
        'grouping': {
            'adonis': parse_adonis_results,
            'anosim': parse_anosim_permanova_results
        },

        'gradient': {
            'mantel': parse_mantel_results,
            'mantel_corr': None,
            'morans_i': parse_morans_i_results,
            'partial_mantel': parse_partial_mantel_results
        }
    }

    permutations = [99, 999]
    num_shuffled = 2
    num_subsets = 2

#    generate_distance_matrices(in_dir, out_dir, studies, metrics, num_shuffled,
#            num_subsets, tree_fp)
#
#    run_methods(out_dir, studies, methods, permutations)
#
    summarize_results(out_dir, out_dir, studies, methods, depth_descs, metrics,
                      permutations, num_shuffled, num_subsets)


if __name__ == "__main__":
    main()
