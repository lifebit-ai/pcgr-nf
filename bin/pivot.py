#!/usr/bin/env python

import os
import sys
import json
import shutil
import pandas as pd

def __main__():

    columns = sys.argv[2:]
    combined = sys.argv[1]
    print("Input combined tiers file:", combined)
    print("Mandatory columns", ['GENOMIC_CHANGE', 'VCF_SAMPLE_ID'])
    print("Extra columns to include:", columns)
    
    columns = ['VCF_SAMPLE_ID'] + columns
    
    df = pd.read_csv(combined, delimiter='\t', header=0)
    variants = df['GENOMIC_CHANGE'].unique()

    pivot = pd.DataFrame(columns=['GENOMIC_CHANGE']+columns)
    for variant in variants:
        row = {'GENOMIC_CHANGE':variant}
        for column in columns:
            row[column] = ",".join(list(df[column][df['GENOMIC_CHANGE'] == variant].unique()))
        pivot = pivot.append(row,ignore_index=True)

    pivot.to_csv("pivot.tsv", sep='\t', index=False)


if __name__=="__main__": __main__()