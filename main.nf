#!/usr/bin/env nextflow

def helpMessage() {
    log.info """
    Usage:
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
    See here for more info: https://github.com/lifebit-ai/hla/blob/master/docs/usage.md
    """.stripIndent()
}

// Show help message
if (params.help) {
  helpMessage()
  exit 0
}

// Define Channels from input
Channel
    .fromPath(params.input)
    .ifEmpty { exit 1, "Cannot find input file : ${params.input}" }
    .splitCsv(skip:1)
    .map {sample_name, file_path -> [ sample_name, file_path ] }
    .set { ch_input }

// Define Process
process pcgr {
    tag "$sample_name"
    label 'low_memory'
    publishDir "${params.outdir}", mode: 'copy'
    publishDir "${params.outdir}/MultiQC", mode: 'copy', pattern: "multiqc_report.html"

    input:
    set val(sample_name), file(input_file) from ch_input

    output:
    file "multiqc_report.html"
    file "result/*"
    script:
    """
    # Get reference data
    wget ${params.pcgr_data}
    unzip *.zip 

    mkdir result
    pcgr.py --input_vcf $input_file --pcgr_dir . --output_dir result/ --genome_assembly ${params.pcgr_genome} --conf ${params.pcgr_config} --sample_id $sample_name --no_vcf_validate --no-docker

    cp result/*${params.pcgr_genome}.html multiqc_report.html"
    """
  }
