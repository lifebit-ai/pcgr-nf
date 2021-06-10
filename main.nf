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
    .into{ data_bundle ;  data_bundle_2}

Channel.fromPath(params.pcgr_config)
    .ifEmpty { exit 1, "Cannot find config file : ${params.pcgr_config}" }
    .into{ config ; config_2 }

// Custum scripts
projectDir = workflow.projectDir
custum_pcgr = Channel.fromPath("${projectDir}/bin/modified_pcgr.py",  type: 'file', followLinks: false)
combine_runs = Channel.fromPath("${projectDir}/bin/pcgr_combine_runs.py",  type: 'file', followLinks: false)
run_report = Channel.fromPath("${projectDir}/bin/pcgr_report.py",  type: 'file', followLinks: false)


// Define Processes
process vcffilter {
    tag "$input_file"
    label 'process_low'

    input:
    file input_file from ch_input

    output:
    file "filtered.vcf" into out_vcffilter

    script:
    """
    vcffilter -s -f "QD > ${params.min_qd} | FS < ${params.max_fs} | SOR < ${params.max_sor} | MQ > ${params.min_mq}" $input_file > filtered.vcf
    """
}


process sanitise_vcf {

    label 'low_memory'
    publishDir "${params.outdir}", mode: 'copy'

    input:
    file(input_file) from out_vcffilter

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
    publishDir "${params.outdir}/pcgr/${input_file.baseName}", mode: 'copy'

    input:
    file input_file from ch_variant_query_sets_flat
    each path(data) from data_bundle
    each file(config_file) from config
    each file("modified_pcgr.py") from custum_pcgr

    output:
    file "result/*" into out_pcgr
    file("*config_options.json") into pcgr_config_option
    file("*arg_dict.json") into pcgr_arg_dict
    file("*host_directories.json") into pcgr_host_directories
    
    script:
    """
    mkdir result
    echo modified_pcgr.py --input_vcf $input_file --pcgr_dir $data --output_dir result/ --genome_assembly $params.pcgr_genome --conf $config_file --sample_id ${input_file.baseName} --no_vcf_validate --no-docker
    
    python modified_pcgr.py --input_vcf $input_file --pcgr_dir $data --output_dir result/ --genome_assembly $params.pcgr_genome --conf $config_file --sample_id ${input_file.baseName} --no_vcf_validate --no-docker
    mv arg_dict.json ${input_file.baseName}_arg_dict.json
    mv config_options.json ${input_file.baseName}_config_options.json
    rm -r result/pcgr_rmarkdown result/pcgr_flexdb
    """
}

// check filtering parameters... in a hacky way
def filter_mode_expected = ['all', '1', '2', '3', '4'] as Set
def parameter_diff = filter_mode_expected - params.filter
    if (parameter_diff.size() > 4){
        println "[Pipeline warning] Parameter $params.filter is not valid in the pipeline! Running with default 'all'\n"
        IN_filter_mode = Channel.value('all')
    } else {
        IN_filter_mode = Channel.value(params.filter)
    }

process combine_pcgr {

    publishDir "${params.outdir}/pcgr/combine", mode: 'copy'

    input:
    val filter_value from IN_filter_mode
    file output_files from out_pcgr.collect()
    each file("pcgr_combine_runs.py") from combine_runs

    output:
    file("combined.filtered.snvs_indels.tiers.tsv")
    file("combined.recode.pcgr_acmg.grch38.pass.tsv") into tsv_combined_filtered

    script:
    """
    python pcgr_combine_runs.py $filter_value $output_files
    """
}

process compress_tsv {
    input:
    file tsv from tsv_combined_filtered

    output:
    file("*gz") into compressed_tsv_combined_filtered

    script:
    """
    gzip -f ${tsv}
    """
}

process report {
    tag "$name"
    label 'low_memory'

    publishDir "${params.outdir}/MultiQC", mode: 'copy', pattern: "multiqc_report.html"

    input:
    val name from sample_name
    file(config_file) from config_2
    path(data) from data_bundle_2
    file(result_tsv) from compressed_tsv_combined_filtered
    each file("pcgr_report.py") from run_report
    file config_option from pcgr_config_option
    file host_directories from pcgr_host_directories

    output:
    file "multiqc_report.html"

    script:
    """
    mkdir result
    python pcgr_report.py $name $config_file $data $params.pcgr_genome $result_tsv $config_option $host_directories \$PWD
    
    cp result/*${params.pcgr_genome}.html multiqc_report.html
    """
}