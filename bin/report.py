#!/usr/bin/env python

import os
import sys
import shutil

def __main__():
    
    pcgr_reports = sys.argv[1].split()

    if len(pcgr_reports) == 1:
        shutil.copyfile(pcgr_reports[0], "multiqc_report.html", follow_symlinks=True)
    else:
        shutil.copyfile(pcgr_reports[0], "multiqc_report.html", follow_symlinks=True)


if __name__=="__main__": __main__()