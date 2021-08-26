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


def process(group_name, df_group, metadata):
    """
    Worker function to process the dataframe.
    """
    row = {'SYMBOL'.capitalize(): group_name[0],
            'GENE NAME'.capitalize(): group_name[1]}

    row['ONCOGENE'.capitalize()] = ";".join([str(x) for x in list(df_group['ONCOGENE'].unique())])
    row['TUMOR_SUPPRESSOR'.replace('_', ' ').capitalize()] = ";".join([str(x) for x in list(df_group['TUMOR_SUPPRESSOR'].unique())])

    for column in df_group.columns:
        if column not in ['SYMBOL', 'GENE_NAME', 'GENOMIC_CHANGE', 'ONCOGENE', 'TUMOR_SUPPRESSOR', 'TIER']:
            row[column.replace('_', ' ').capitalize()] = ";".join([str(x) for x in list(df_group[column].unique())])
    
    row['NUMBER OF VARIANTS'.capitalize()] = str(len(list(df_group['GENOMIC_CHANGE'])))

    row["Tier 1"] = len(df_group['TIER'][df_group['TIER']=="TIER 1"])
    row["Tier 2"] = len(df_group['TIER'][df_group['TIER']=="TIER 2"])
    row["Tier 3"] = len(df_group['TIER'][df_group['TIER']=="TIER 3"])
    row["Tier 4"] = len(df_group['TIER'][df_group['TIER']=="TIER 4"])
    row["Noncoding"] = len(df_group['TIER'][df_group['TIER']=="NONCODING"])
    
    if not metadata.empty:
        summed_values = pd.DataFrame(columns=sorted(metadata.columns))
        for sample in row['VCF SAMPLE ID'.capitalize()].split(';'):
            summed_values = summed_values.append(metadata.loc[sample])
        for col in summed_values.columns:
            total_category = metadata[col].sum()
            row[col.replace('_', ' ').capitalize()] = int(sum(summed_values[col]))
            row[col.replace('_', ' ').replace('Number',"Percentage").capitalize()] = sum(summed_values[col])/total_category * 100
    return row


def __main__():

    # input
    combined = sys.argv[1]
    combined_header = open(combined).readline().rstrip().split("\t")

    columns = sys.argv[2]
    if columns == 'false':
        columns = []
    else:
        columns = sys.argv[2].split(',')

    max_cpus = int(sys.argv[3])

    # columns for report
    mandatory_columns = ['GENE_NAME','SYMBOL', 'ONCOGENE','TUMOR_SUPPRESSOR', 'VCF_SAMPLE_ID', 'GENOMIC_CHANGE', 'TIER']

    print("Input combined tiers file:", combined)
    print("Mandatory columns", mandatory_columns)
    print("Extra columns to include:", columns)
    print("Metadata columns: METADATA_HISTOLOGICAL_TYPE")

    # create dataframe with value counts per metadata - histological type
    metadata_col = ['VCF_SAMPLE_ID', 'METADATA_HISTOLOGICAL_TYPE']
    metadata_df = pd.read_csv(combined, sep='\t', header=0, usecols=metadata_col).drop_duplicates()

    group_metadata_df = metadata_df.groupby(['VCF_SAMPLE_ID'])
    metadata_rows = []
    for group_name, df_group in group_metadata_df:
        row = {'VCF SAMPLE ID'.capitalize(): group_name}
        _count_dict = json.loads((df_group['METADATA_HISTOLOGICAL_TYPE'].value_counts().to_json()))
        for k,v in _count_dict.items():
                if k != group_name:
                    row['Number_'+k] = v
        metadata_rows.append(row)
    count_metadata_df = pd.DataFrame([f for f in metadata_rows]).fillna(0).set_index('VCF SAMPLE ID'.capitalize()) 

    # parse and process pcgr combined file
    all_columns = list(set(mandatory_columns + columns))
    reader = pd.read_csv(combined, sep='\t', header=0, chunksize=1000, usecols=all_columns)
    chunk_arr = []
    for df in reader:
        chunk_arr.append(df)
    df = pd.concat(chunk_arr, axis=0)

    # combine information per gene
    group_by = df.groupby(['SYMBOL','GENE_NAME'])
    print("Number of genes found:", len(group_by))

    pool = mp.Pool(processes=max_cpus)
    f_list = []
    for group_name, df_group in group_by:
        f = pool.apply_async(process, [group_name, df_group, count_metadata_df])
        f_list.append(f)

    pivot = pd.DataFrame([f.get() for f in f_list]) 


    pivot.to_csv("pivot_gene_simple.tsv", sep='\t', index=False)

if __name__=="__main__": __main__()
