# PCGR-nf 

Nextflow workflow for variant interpretation for precision cancer medicine using [Personal Cancer Genome Reporter (PCGR)](https://github.com/sigven/pcgr).

## Rationale

The Personal Cancer Genome Reporter (PCGR) is a stand-alone software package for functional annotation and translation of individual cancer genomes for precision cancer medicine. Currently, it interprets both somatic SNVs/InDels and copy number aberrations. The software extends basic gene and variant annotations from the [Ensembl’s Variant Effect Predictor (VEP)](http://www.ensembl.org/info/docs/tools/vep/index.html) with oncology-relevant, up-to-date annotations retrieved flexibly through [vcfanno](https://github.com/brentp/vcfanno), and produces interactive HTML reports intended for clinical interpretation.

## Requirements
This workflow requires at least 4 cpus and 8GB of memory.

## Usage
The typical command for running the pipeline is as follows:

    nextflow run main.nf --input sample.csv [Options]
    
    Inputs Options:
    --input         Input file

    PCGR Options:
    --pcgr_config   Tool config file (path)
                    (default: $params.pcgr_config)
    --pcgr_data     URL for reference data bundle
                    (default: $params.pcgr_data)
    --pcgr_genome   Reference genome assembly
                    (default: $params.pcgr_genome)

    Resource Options:
    --max_cpus      Maximum number of CPUs (int)
                    (default: $params.max_cpus)  
    --max_memory    Maximum memory (memory unit)
                    (default: $params.max_memory)
    --max_time      Maximum time (time unit)
                    (default: $params.max_time)

## Basic run command example
    nextflow run main.nf

## Run test
    nextflow run main.nf -profile test,<docker...>
## Publicly available Reference Genome Bundle
* [grch37 data bundle - 20201123](http://insilico.hpc.uio.no/pcgr/pcgr.databundle.grch37.20201123.tgz) (approx 17Gb)
* [grch38 data bundle - 20201123](http://insilico.hpc.uio.no/pcgr/pcgr.databundle.grch38.20201123.tgz) (approx 18Gb)
