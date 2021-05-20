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

// Header log info
def summary = [:]
if (workflow.revision) summary['Pipeline Release'] = workflow.revision
summary['Max Resources']    = "$params.max_memory memory, $params.max_cpus cpus, $params.max_time time per job"
if (workflow.containerEngine) summary['Container'] = "$workflow.containerEngine - $workflow.container"
summary['Output dir']       = params.outdir
summary['Launch dir']       = workflow.launchDir
summary['Working dir']      = workflow.workDir
summary['Script dir']       = workflow.projectDir
summary['User']             = workflow.userName
summary['Config Profile']   = workflow.profile
summary['Input file']       = params.input
log.info summary.collect { k,v -> "${k.padRight(20)}: $v" }.join("\n")
log.info "-\033[2m--------------------------------------------------\033[0m-"


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

// Define Processes

process sanitise_vcf {

    label 'low_memory'
    publishDir "${params.outdir}", mode: 'copy'

    input:
    file(input_file) from ch_input

    output:
    file("fixed.vcf") into in_split_vcf

    """
    bcftools +fixploidy $input_file > fixed.vcf
    """
}

process split_vcf_by_chr {

    label 'low_memory'
    publishDir "${params.outdir}", mode: 'copy'

    input:
    file(input_file) from in_split_vcf

    output:
    file("*.recode.vcf") into ch_variant_query_sets

    """
    seq  -f "chr%1g" 22 | xargs -n1 -P4 -I {} vcftools --gzvcf ${input_file} --chr {} --recode --recode-INFO-all --out ${input_file.baseName}.{}.vcf
    for file in \$(ls *.recode.vcf); do res=\$(cat \$file |grep -v ^# | wc -l); echo \$res; if (( \$res == 0)); then echo \$file; rm \$file;  fi; done
    """
}

ch_variant_query_sets_flat = ch_variant_query_sets.flatten()

process pcgr {
    tag "$input_file"
    label 'low_memory'
    errorStrategy 'ignore'
    publishDir "${params.outdir}", mode: 'copy'
    publishDir "${params.outdir}/MultiQC", mode: 'copy', pattern: "multiqc_report.html"

    input:
    file input_file from ch_variant_query_sets_flat
    each path(data) from data_bundle
    each sample_name
    each file(config_file) from config

    output:
    file "multiqc_report.html"
    file "result/*"

    script:
    """
    mkdir result
    echo pcgr.py --input_vcf $input_file --pcgr_dir $data --output_dir result/ --genome_assembly $params.pcgr_genome --conf $config_file --sample_id $sample_name --no_vcf_validate --no-docker
    
    pcgr.py --input_vcf $input_file --pcgr_dir $data --output_dir result/ --genome_assembly $params.pcgr_genome --conf $config_file --sample_id $sample_name --no_vcf_validate --no-docker

    cp result/*${params.pcgr_genome}.html multiqc_report.html
    """
}
