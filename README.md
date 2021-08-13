# PCGR-nf 

Nextflow workflow for variant interpretation for precision cancer medicine using [Personal Cancer Genome Reporter (PCGR)](https://github.com/sigven/pcgr).

## Rationale

The Personal Cancer Genome Reporter (PCGR) is a stand-alone software package for functional annotation and translation of individual cancer genomes for precision cancer medicine. Currently, it interprets both somatic SNVs/InDels and copy number aberrations. The software extends basic gene and variant annotations from the [Ensembl’s Variant Effect Predictor (VEP)](http://www.ensembl.org/info/docs/tools/vep/index.html) with oncology-relevant, up-to-date annotations retrieved flexibly through [vcfanno](https://github.com/brentp/vcfanno), and produces interactive HTML reports intended for clinical interpretation.

## Requirements
This workflow requires at least 16 CPUs and 20GB of memory.

## Usage
The typical command for running the pipeline is as follows:
    
    nextflow run main.nf --vcf sample.vcf [Options]
    
    Essential paramenters:
        Single File Mode:
    --vcf           Input `VCF` file.
                    See example in `testdata/test.vcf`. 

        Multiple File Mode:
    --csv           A list of `VCF` files.
                    Should be a `*.csv` file with a header called `vcf` and the path to each file, one per line. 
                    See example in `testdata/list-vcf-files-local.csv`. 

    PCGR Options:
    --pcgr_config   Tool config file (path)
                    (default: s3://fast-ngs/cloudos-public-data-ines/pcgr.toml)
    --pcgr_genome   Reference genome assembly
                    (default: grch38)
    --pcgr_data     URL for reference data bundle
                    Optional filed. If not provided, the appropriate data bundle is infered from --pcgr_genome. 
                    (default: false)

    Resource Options:
    --max_cpus      Maximum number of CPUs (int)
                    (default: 16)  
    --max_memory    Maximum memory (memory unit)
                    (default: 20 GB)
    --max_time      Maximum time (time unit)
                    (default: 10d)

## Basic run command example
    nextflow run main.nf --vcf sample.vcf

## Run test
    nextflow run main.nf -profile test,<docker...>
## Publicly available Reference Genome Bundle
* [grch37 data bundle - 20201123](http://insilico.hpc.uio.no/pcgr/pcgr.databundle.grch37.20201123.tgz) (approx 17Gb)
* [grch38 data bundle - 20201123](http://insilico.hpc.uio.no/pcgr/pcgr.databundle.grch38.20201123.tgz) (approx 18Gb)
