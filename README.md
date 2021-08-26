# pcgr-nf

Nextflow workflow for variant interpretation for precision cancer medicine using [Personal Cancer Genome Reporter (PCGR)](https://github.com/sigven/pcgr).

## Rationale

The Personal Cancer Genome Reporter (PCGR) is a stand-alone software package for functional annotation and translation of individual cancer genomes for precision cancer medicine. Currently, it interprets both somatic SNVs/InDels and copy number aberrations. The software extends basic gene and variant annotations from the [Ensembl’s Variant Effect Predictor (VEP)](http://www.ensembl.org/info/docs/tools/vep/index.html) with oncology-relevant, up-to-date annotations retrieved flexibly through [vcfanno](https://github.com/brentp/vcfanno), and produces interactive HTML reports intended for clinical interpretation.

## Requirements

This workflow requires at least 16 CPUs and 20GB of memory for optimal execution, however on small input data like test data it can be run with as few as 2 CPUs and 4GB of memory.

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

    Optional parameters:
    --config        Additional nextflow config file that can specify all parameters instead of providing them 
                    from command line.

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

## Run test locally

    nextflow run main.nf -profile standard,docker --config conf/test.config

which is equivalent to

    nextflow run main.nf -profile standard,docker \
        --csv testdata/testdata.csv \
        --genome grch38 \
        --max_cpus 2 \
        --max_memory 4.GB

## Run pipeline on CloudOS

To see how to run the pipeline on [CloudOS](https://cloudos.lifebit.ai/) see [docs/usage_cloudos.md](docs/usage_cloudos.md) guide.

## Publicly available reference genome bundles

* [grch37 data bundle - 20201123](http://insilico.hpc.uio.no/pcgr/pcgr.databundle.grch37.20201123.tgz) (approx 17Gb)
* [grch38 data bundle - 20201123](http://insilico.hpc.uio.no/pcgr/pcgr.databundle.grch38.20201123.tgz) (approx 18Gb)
