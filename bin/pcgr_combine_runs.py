#!/usr/bin/env python3

import os
import pandas as pd
import numpy as np
import sys
import glob
import csv
import gzip
from subprocess import check_call


__version__ = "0.0.1"
__build__ = "27.05.2021"
__template__ = "combine_pcgr-nf"

_FILTER_LISTS = {'all': ['TIER 1', 'TIER 2', 'TIER 3', 'TIER 4', 'NONCODING'],
                '4': ['TIER 1', 'TIER 2', 'TIER 3', 'TIER 4'],
                '3': ['TIER 1', 'TIER 2', 'TIER 3'],
                '2': ['TIER 1', 'TIER 2'],
                '1': ['TIER 1']}


def main():

    print("Argument List:", str(sys.argv))

    # input 
    try:
        filter_value = sys.argv[1]
        output_files = sys.argv[2:]
    except IndexError as e:
        print(e, "files not found")
        sys.exit(1)
    
    if filter_value not in _FILTER_LISTS.keys():
        print("filter option not found")
        sys.exit(1)
    else:
        allowed_tiers = _FILTER_LISTS[filter_value]
        print("Allowed Tiers:", str(allowed_tiers))
    
    # filter tiers files
    allowed_variants = []
    tiers_files = [x for x in output_files if x.endswith('snvs_indels.tiers.tsv')]
    with open("combined.filtered.snvs_indels.tiers.tsv", "w") as fh:
        tsv_writer = csv.writer(fh, delimiter="\t")
        for t_file in tiers_files:
            skipHeader = tiers_files.index(t_file) != 0
            with open(t_file) as t_file_h:
                tsv_reader = csv.reader(t_file_h, delimiter="\t")
                header = next(tsv_reader, None)
                if not skipHeader:
                    tsv_writer.writerow(header)
                for row in tsv_reader:
                    if row[-2] in allowed_tiers:
                        tsv_writer.writerow(row)
                        allowed_variants.append(row[0]+'_'+row[1])

    # filter output_pass_tsv
    pass_tsv_files = [x for x in output_files if x.endswith('pass.tsv.gz')]
    with open("combined.filtered.pass.tsv", "w") as fh:
        tsv_writer = csv.writer(fh, delimiter="\t")
        for pass_tsv_file in pass_tsv_files:
            skipHeader = pass_tsv_files.index(pass_tsv_file) != 0
            with gzip.open(pass_tsv_file, 'rt') as f:
                header_comment = f.readline()
                header_comment = header_comment.strip().split('\t')
                header_names = f.readline()
                header_names = header_names.strip().split('\t')
                if not skipHeader:
                    tsv_writer.writerow(header_comment)
                    tsv_writer.writerow(header_names)
                for line in f:
                    row = line.strip().split('\t')
                    print(row)
                    variant_id = row[0]+'_'+row[1]
                    if variant_id in allowed_variants and len(row) == 189:  # TODO
                        tsv_writer.writerow(row)

if __name__ == '__main__':
    main()