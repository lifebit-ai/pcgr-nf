#!/usr/bin/env python

import os
import sys


def __main__():

    vcf = sys.argv[1]
    min_qd = sys.argv[2]
    max_fs = sys.argv[3]
    max_sor = sys.argv[4]
    min_mq = sys.argv[5]

    filterstr = ""
    if 'ID=QD' in open(vcf).read():
        filterstr += "QD > {}".format(min_qd)
    if 'ID=FS' in open(vcf).read():
        if filterstr == "":
            filterstr += "FS < {}".format(max_fs)
        else:
            filterstr += " | FS < {}".format(max_fs)
    if 'ID=SOR' in open(vcf).read():
        if filterstr == "":
            filterstr += "SOR < {}".format(max_sor)
        else:
            filterstr += " | SOR < {}".format(max_sor)
    if 'ID=MQ' in open(vcf).read():
        if filterstr == "":
            filterstr += "MQ > {}".format(min_mq)
        else:
            filterstr += " | MQ > {}".format(min_mq)
    
    with open("filter", "w") as fh:
        fh.write(filterstr)   


if __name__=="__main__": __main__()