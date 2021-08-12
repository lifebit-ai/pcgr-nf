#!/usr/bin/env python

import os
import sys
import json
import shutil
import pandas as pd
import multiprocessing as mp


PCGR_COLUMNS = ['CHROM','POS','REF','ALT','GENOMIC_CHANGE','GENOME_VERSION','VCF_SAMPLE_ID',
                'VARIANT_CLASS','SYMBOL','GENE_NAME','CCDS','CANONICAL','ENTREZ_ID','UNIPROT_ID',
                'ENSEMBL_TRANSCRIPT_ID','ENSEMBL_GENE_I','REFSEQ_MRNA','ONCOGENE','TUMOR_SUPPRESSOR',
                'ONCOGENE_EVIDENCE','TUMOR_SUPPRESSOR_EVIDENCE','CONSEQUENCE','PROTEIN_CHANGE','PROTEIN_DOMAIN',
                'CODING_STATUS','EXONIC_STATUS','CDS_CHANGE','HGVSp','HGVSc','EFFECT_PREDICTIONS',
                'MUTATION_HOTSPOT','MUTATION_HOTSPOT_TRANSCRIPT','MUTATION_HOTSPOT_CANCERTYPE','PUTATIVE_DRIVER_MUTATION',
                'CHASMPLUS_DRIVER','CHASMPLUS_TTYPE','VEP_ALL_CSQ','DBSNPRSID','COSMIC_MUTATION_ID','TCGA_PANCANCER_COUNT',
                'TCGA_FREQUENCY','ICGC_PCAWG_OCCURRENCE','CHEMBL_COMPOUND_ID','CHEMBL_COMPOUND_TERMS','SIMPLEREPEATS_HIT',
                'WINMASKER_HIT','OPENTARGETS_RANK','CLINVAR','CLINVAR_CLNSIG','GLOBAL_AF_GNOMAD','GLOBAL_AF_1KG',
                'CALL_CONFIDENCE','DP_TUMOR','AF_TUMOR','DP_CONTROL','AF_CONTROL','TIER','TIER_DESCRIPTION']


def process(group_name, df_group):
    """
    Worker function to process the dataframe.
    """
    row = {'SYMBOL'.capitalize(): group_name[0],
            'VARIANT CLASS'.capitalize(): group_name[1],
            'CONSEQUENCE'.capitalize(): group_name[2]}
    for column in df_group.columns:
        if column not in ['SYMBOL', 'VARIANT_CLASS', 'CONSEQUENCE']:
            row[column.replace('_', ' ').capitalize()] = ",".join([str(x) for x in list(df_group[column].unique())])
    row['NUMBER OF VARIANTS'.capitalize()] = str(len(list(df_group['GENOMIC_CHANGE'].unique())))
    return row


def __main__():

    combined = sys.argv[1]
    max_cpus = int(sys.argv[2])
    metadata = sys.argv[3]

    print("Input combined tiers file:", combined)
    print("Mandatory columns", ['GENE_NAME','SYMBOL', 'VARIANT_CLASS', 'CONSEQUENCE', 'VCF_SAMPLE_ID', 'GENOMIC_CHANGE'])
    print("Extra columns to include:")
    
    all_columns = ['GENE_NAME','SYMBOL', 'VARIANT_CLASS', 'CONSEQUENCE', 'VCF_SAMPLE_ID', 'GENOMIC_CHANGE']
    
    reader = pd.read_csv(combined, sep='\t', header=0, chunksize=1000, usecols=all_columns)
    chunk_arr = []
    for df in reader:
        chunk_arr.append(df)
    df = pd.concat(chunk_arr, axis=0)

    group_by = df.groupby(['SYMBOL', 'VARIANT_CLASS', 'CONSEQUENCE'])
    print("Number of genes found:", len(group_by))

    pool = mp.Pool(processes=max_cpus)
    f_list = []
    for group_name, df_group in group_by:
        f = pool.apply_async(process, [group_name, df_group])
        f_list.append(f)

    pivot = pd.DataFrame([f.get() for f in f_list]) 

    if not os.stat(metadata).st_size==0:
        metadata_dict = {}

        with open(metadata, "r") as fh:
            categories = f.readline().split('\t')[1:]
            for cat in categories:
                metadata_dict[cat] = []
            for line in fh:
                line = line.split('\t')
                sample = line[0]
                attributes = line[1:]
                i = 0
                for cat_attribute in attributes:
                    metadata_cat = categories[i]
                    if cat_attribute == 1:
                        metadata_dict[metadata_cat].append(os.basename(sample))

        print(metadata_dict)


    pivot.to_csv("pivot_gene.tsv", sep='\t', index=False)

if __name__=="__main__": __main__()
