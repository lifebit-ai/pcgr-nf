#!/usr/bin/env python

import os
import sys
import shutil
import pandas

def __main__():
    
    pcgr_tsvs = sys.argv[1:]
    print(pcgr_tsvs)

    if len(pcgr_tsvs) == 1:
        shutil.copyfile(pcgr_tsvs[0], "combined.tsv", follow_symlinks=True)
    else:
        li = []
        for tsvfile in pcgr_tsvs:
            samplename = os.path.basename(tsvfile).split('.')[0]
            df = pd.read_csv(tsvfile, index_col=0, header=0)
            df['Sample'] = samplename
            li.append(df)
        frame = pd.concat(li, ignore_index=True)
        frame.to_csv("combined.tsv", index=False, sep="\t")

if __name__=="__main__": __main__()