#!/usr/bin/env nextflow

def helpMessage() {
    log.info """
    Usage:
    The typical command for running the pipeline is as follows:
    nextflow run main.nf --input sample.csv [Options]
    
    Inputs Options:
    --input         Input VCF file
    --name          Sample name

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
    .set { ch_input }

Channel
    .from(params.name)
    .ifEmpty { exit 1, "Cannot find input name : ${params.name}" }
    .set { sample_name }

Channel.fromPath(params.pcgr_data)
    .ifEmpty { exit 1, "Cannot find data bundle path : ${params.pcgr_data}" }
    .set{ data_bundle }

Channel.fromPath(params.pcgr_config)
    .ifEmpty { exit 1, "Cannot find config file : ${params.pcgr_config}" }
    .set{ config }

if (!params.skip_filtering) {

process vcffilter {
    tag "$input_file"
    label 'process_low'

    input:
    file input_file from ch_input

    output:
    file "filtered.vcf" into out_vcf_filter

    script:
    """
    vcffilter -s -f "QD > ${params.min_qd} | FS < ${params.max_fs} | SOR < ${params.max_sor} | MQ > ${params.min_mq}" $input_file > filtered.vcf
    """
}
}else{
ch_vcf_for_pcgr = ch_input
}


process pcgr {
    tag "$name"
    label 'process_high'
    publishDir "${params.outdir}", mode: 'copy'
    publishDir "${params.outdir}/MultiQC", mode: 'copy', pattern: "multiqc_report.html"

    input:
    file input_file from ch_vcf_for_pcgr
    path data from data_bundle
    val name from sample_name
    path config_file from config

    output:
    file "multiqc_report.html"
    file "result/*"
    script:
    """
    mkdir result
    pcgr.py --input_vcf $input_file --pcgr_dir $data --output_dir result/ --genome_assembly $params.pcgr_genome --conf $config_file --sample_id $name --no_vcf_validate --no-docker

    cp result/*${params.pcgr_genome}.html multiqc_report.html
    """
  }
