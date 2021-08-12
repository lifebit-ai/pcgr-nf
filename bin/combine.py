#!/usr/bin/env python

import os
import sys
import shutil

def __main__():
    
    pcgr_tsvs = sys.argv[1:]
    print("Input tsv files:", pcgr_tsvs)

    if len(pcgr_tsvs) == 1:
        shutil.copyfile(pcgr_tsvs[0], "combined.tsv", follow_symlinks=True)
    else:
        with open("combined.tiers.tsv", "w") as combined_fh:
            for tsvfile in pcgr_tsvs:
                with open(tsvfile, "r") as tsv_fh:
                    #check if first file - only copy the header once
                    if pcgr_tsvs.index(tsvfile) == 0:
                        #get header line, add sample column at the start
                        first_line = tsv_fh.readline().split('\t')
                        combined_fh.write('\t'.join(first_line))
                    else:
                        #skip first line
                        tsv_fh.readline()
                    for line in tsv_fh:
                        line = line.split('\t')
                        combined_fh.write('\t'.join(line))

if __name__=="__main__": __main__()