#!/usr/bin/env python

import os
import sys
import shutil
import pandas as pd

def __main__():
    
    metadata = sys.argv[1]
    pcgr_tsvs = sys.argv[2:]
    print("Input tsv files:", pcgr_tsvs)
    print("Metadata: ", metadata)

    if len(pcgr_tsvs) == 1:
        df = pd.read_csv(pcgr_tsvs[0], index_col=None, header=0, delimiter="\t")
    else:
        df = pd.DataFrame()
        li =[]
        for tsv_file in pcgr_tsvs:
            df_ = pd.read_csv(tsv_file, index_col=None, header=0, delimiter="\t")
            li.append(df_)

        df = pd.concat(li, axis=0, ignore_index=True)
    
    if metadata != "PASS":
        # process metadata
        metadata_df = pd.read_csv(metadata, index_col=None, header=0, delimiter=",")
        metadata_df = metadata_df.add_prefix("metadata_")
        metadata_df['VCF_SAMPLE_ID'] = metadata_df['metadata_vcf'].str.replace('.vcf', '')
        metadata_df = metadata_df.drop(columns='metadata_vcf')
        metadata_df.columns = map(str.upper, metadata_df.columns)

        df = df.merge(metadata_df, on='VCF_SAMPLE_ID', how="left")
        print(df)

    # save final file
    df.to_csv("combined.tiers.tsv", sep="\t", index=False, na_rep="NA") 

if __name__=="__main__": __main__()