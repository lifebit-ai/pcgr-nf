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
        'GENE NAME'.capitalize(): group_name[1]}
    row['ONCOGENE'.capitalize()] = ";".join([str(x) for x in list(df_group['ONCOGENE'].unique())])
    row['TUMOR_SUPPRESSOR'.replace('_', ' ').capitalize()] = ";".join([str(x) for x in list(df_group['TUMOR_SUPPRESSOR'].unique())])
    
    for column in df_group.columns:
        if column not in ['SYMBOL', 'GENE_NAME', 'VARIANT_CLASS', 'CONSEQUENCE',  'ONCOGENE', 'TUMOR_SUPPRESSOR']:
            row[column.replace('_', ' ').capitalize()] = ";".join([str(x) for x in list(df_group[column].unique())])
    
    row['NUMBER OF VARIANTS'.capitalize()] = str(len(list(df_group['GENOMIC_CHANGE'].unique())))
    row['VARIANT CLASS'.capitalize()] = group_name[2]
    row['CONSEQUENCE'.capitalize()] =  group_name[3]
    return row


def __main__():

    combined = sys.argv[1]
    columns = sys.argv[2]
    if columns == 'false':
        columns = []
    else:
        columns = sys.argv[2].split(',')
    max_cpus = int(sys.argv[3])

    mandatory_columns = ['GENE_NAME','SYMBOL', 'ONCOGENE', 'TUMOR_SUPPRESSOR', 'VARIANT_CLASS', 'CONSEQUENCE', 'VCF_SAMPLE_ID', 'GENOMIC_CHANGE']

    print("Input combined tiers file:", combined)
    print("Mandatory columns", mandatory_columns)
    print("Extra columns to include:", columns)

    all_columns = list(set(mandatory_columns + columns))
        
    reader = pd.read_csv(combined, sep='\t', header=0, chunksize=1000, usecols=all_columns)
    chunk_arr = []
    for df in reader:
        chunk_arr.append(df)
    df = pd.concat(chunk_arr, axis=0)

    group_by = df.groupby(['SYMBOL','GENE_NAME','VARIANT_CLASS','CONSEQUENCE'])
    print("Number of genes found:", len(group_by))

    pool = mp.Pool(processes=max_cpus)
    f_list = []
    for group_name, df_group in group_by:
        f = pool.apply_async(process, [group_name, df_group])
        f_list.append(f)

    pivot = pd.DataFrame([f.get() for f in f_list]) 
    pivot.to_csv("pivot_gene_complete.tsv", sep='\t', index=False)

if __name__=="__main__": __main__()
