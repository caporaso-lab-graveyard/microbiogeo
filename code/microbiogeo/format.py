#!/usr/bin/env python
from __future__ import division

__author__ = "Jai Ram Rideout"
__copyright__ = "Copyright 2013, The QIIME Project"
__credits__ = ["Jai Ram Rideout"]
__license__ = "GPL"
__version__ = "0.0.0-dev"
__maintainer__ = "Jai Ram Rideout"
__email__ = "jai.rideout@gmail.com"

"""Module to format data for presentation."""

from collections import defaultdict
from os.path import join

from numpy import invert, mean, ones, std, tri
import numpy.ma

from matplotlib import cm
from matplotlib.pyplot import (colorbar, figure, imshow, legend, matshow,
                               savefig, subplot, tight_layout, title, xlim,
                               xticks, yticks)

from cogent.maths.stats.test import pearson, spearman

from qiime.util import create_dir

from microbiogeo.util import is_empty

def format_method_comparison_table(methods_results):
    constructed_header = None
    rows = []

    for method, method_res in sorted(methods_results.items()):
        header = ['Method']
        row = [method]

        for study, study_res in sorted(method_res['real'].items()):
            for category, category_res in sorted(study_res.items()):
                header_column_title = '%s\r%s' % (study, category)
                header.append(header_column_title)
                header.append(header_column_title + ' (shuffled)')

                if len(category_res) == 0:
                    row.extend(['N/A'] * 2)
                else:
                    if category_res['original'].isEmpty():
                        row.append('N/A')
                    else:
                        row.append(str(category_res['original']))

                    if category_res['shuffled'].isEmpty():
                        row.append('N/A')
                    else:
                        row.append(str(category_res['shuffled']))

        if constructed_header is None:
            rows.append(header)
            constructed_header = header
        elif constructed_header != header:
            raise ValueError("The studies and/or categories did not match up "
                             "exactly between one or more of the methods.")

        rows.append(row)

    return rows

# Not unit-tested.
def create_method_comparison_heatmaps(results, methods, out_dir):
    """Generates heatmaps showing the correlation between each pair of methods.

    Generates two heatmaps (one for Pearson correlation, one for Spearman
    correlation). Uses all available results (e.g. all even sampling depths,
    metrics, and datasets) that match between each pair of methods as input to
    the correlation coefficient methods.

    A heatmap will be written to out_dir for each type of method (grouping or
    gradient).
    """
    for method_type, data in \
            format_method_comparison_heatmaps(results, methods).items():
        for correlation_method, heatmap_data in data.items():
            # Generate the heatmap. Code based on
            # http://matplotlib.org/users/tight_layout_guide.html and
            # http://psaffrey.wordpress.com/2010/07/05/chromosome-interactions-
            #   heatmaps-and-matplotlib/
            fig = figure()
            ax = subplot(111)
            cmap = cm.get_cmap()
            cmap.set_bad('w') # default value is 'k'
            im = ax.imshow(heatmap_data, cmap=cmap, interpolation='nearest')
            method_labels = [method.DisplayName
                             for method in methods[method_type]]

            colorbar(im, use_gridspec=True)
            xticks(range(len(method_labels)), method_labels, rotation=90)
            yticks(range(len(method_labels)), method_labels)

            for loc, spine in ax.spines.items():
                if loc in ['right','top']:
                    spine.set_color('none') # don't draw spine

            ax.xaxis.set_ticks_position('bottom')
            ax.yaxis.set_ticks_position('left')
            ax.grid(True, which='minor')

            tight_layout()
            savefig(join(out_dir, '%s_analysis_heatmap_%s.pdf' % (method_type,
                    correlation_method)), format='pdf')
            savefig(join(out_dir, '%s_analysis_heatmap_%s.png' % (method_type,
                    correlation_method)), format='png', dpi=1000)

def format_method_comparison_heatmaps(results, methods):
    shared_studies = {}
    shared_categories = {}

    for depth_desc, depth_res in results.items():
        for metric, metric_res in depth_res.items():
            for method_type, method_type_res in metric_res.items():
                if method_type not in shared_categories:
                    shared_categories[method_type] = {}

                for method, method_res in method_type_res.items():
                    matched_method = False
                    for m in methods[method_type]:
                        if method == m.Name:
                            matched_method = True
                            break

                    if matched_method:
                        studies = sorted(method_res.keys())

                        if method_type not in shared_studies:
                            shared_studies[method_type] = studies
                        elif studies != shared_studies[method_type]:
                            raise ValueError("Not all methods to include in "
                                             "the heatmap have results for "
                                             "the same studies.")

                        for study, study_res in sorted(method_res.items()):
                            categories = [cat for cat, cat_res in \
                                          sorted(study_res.items()) if not
                                          is_empty(cat_res)]

                            if study not in shared_categories[method_type]:
                                shared_categories[method_type][study] = \
                                        set(categories)
                            else:
                                shared_categories[method_type][study] &= \
                                        set(categories)

    # Gather all test statistics for each method (in the same order for each
    # method!).
    method_data = defaultdict(lambda: defaultdict(list))
    for depth_desc, depth_res in results.items():
        for metric, metric_res in depth_res.items():
            for method_type, method_type_res in metric_res.items():
                for method, method_res in method_type_res.items():
                    matched_method = False
                    for m in methods[method_type]:
                        if method == m.Name:
                            matched_method = True
                            break

                    if not matched_method:
                        continue

                    for study, study_res in sorted(method_res.items()):
                        for category, category_res in \
                                sorted(study_res.items()):
                            if category in \
                                    shared_categories[method_type][study]:
                                method_data[method_type][method].append(
                                        category_res['full'].effect_size)
                                method_data[method_type][method].append(
                                        category_res['shuffled'].effect_size)

                                for res in category_res['subsampled']:
                                    method_data[method_type][method].append(
                                            res.effect_size)

    # Make sure our data looks sane. We should have the same number of
    # observations for each method.
    for method_type, results in method_data.items():
        data_length = None

        for method, data in results.items():
            if data_length is None:
                data_length = len(data)
            elif len(data) != data_length:
                raise ValueError("The number of test statistics is not the "
                                 "same between all methods, so we can't "
                                 "compare them.")

    # Compute the correlation coefficient between each pair of methods and put
    # the output in an array. This array can then be used to generate a
    # text-based table or heatmap.
    heatmaps = {}
    for method_type in methods:
        heatmaps[method_type] = {}

        for correlation_name, correlation_fn in \
                ('pearson', pearson), ('spearman', spearman):
            num_methods = len(methods[method_type])
            heatmap_data = ones((num_methods, num_methods))

            # I know this is inefficient, but it really doesn't matter for what
            # we're doing here.
            for method1_idx, method1 in enumerate(methods[method_type]):
                for method2_idx, method2 in enumerate(methods[method_type]):
                    corr_coeff = correlation_fn(
                            method_data[method_type][method1.Name],
                            method_data[method_type][method2.Name])
                    heatmap_data[method1_idx][method2_idx] = corr_coeff

            # Mask out the upper triangle. Taken from
            # http://stackoverflow.com/a/2332520
            mask = invert(tri(heatmap_data.shape[0], k=0, dtype=bool))
            heatmap_data = numpy.ma.array(heatmap_data, mask=mask)

            heatmaps[method_type][correlation_name] = heatmap_data

    return heatmaps
