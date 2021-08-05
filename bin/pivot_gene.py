#!/usr/bin/env python

import os
import sys
import json
import shutil
import pandas as pd

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

def __main__():

    #columns = sys.argv[2].split(',')
    combined = sys.argv[1]
    print("Input combined tiers file:", combined)
    print("Mandatory columns", ['SYMBOL', 'GENE_NAME', 'VARIANT_CLASS', 'CONSEQUENCE', 'VCF_SAMPLE_ID', 'GENOMIC_CHANGE'])
    print("Extra columns to include:")
    
    columns = ['GENE_NAME', 'VCF_SAMPLE_ID', 'GENOMIC_CHANGE']
    
    df = pd.read_csv(combined, delimiter='\t', header=0)
    pivot = pd.DataFrame()

    print("Number of genes found:", len(df['SYMBOL'].unique()))
    
    for gene in df['SYMBOL'].unique():
        for variant_class in df['VARIANT_CLASS'][df['SYMBOL'] == gene].unique():
            for consequence in df['CONSEQUENCE'][(df['SYMBOL'] == gene) & (df['VARIANT_CLASS'] == variant_class)].unique():
                row = {'SYMBOL'.capitalize(): gene,
                        'VARIANT CLASS'.capitalize(): variant_class,
                        'CONSEQUENCE'.capitalize(): consequence}
                
                for column in columns:
                    if column in PCGR_COLUMNS:
                        row[column.replace('_', ' ').capitalize()] = ",".join([str(x) for x in list(df[column][(df['SYMBOL'] == gene) &
                                                                                                    (df['VARIANT_CLASS'] == variant_class) &
                                                                                                    (df['CONSEQUENCE'] == consequence)].unique())])
                    else:
                        print("unrecognized column {}, skipping...".format(column))
                row['NUMBER OF VARIANTS'.capitalize()] = len(list(df['GENOMIC_CHANGE'][(df['SYMBOL'] == gene) &
                                                                        (df['VARIANT_CLASS'] == variant_class) &
                                                                        (df['CONSEQUENCE'] == consequence)].unique()))

        pivot = pivot.append(row,ignore_index=True)

    pivot.to_csv("pivot_gene.tsv", sep='\t', index=False)

if __name__=="__main__": __main__()
