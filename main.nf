#!/usr/bin/env nextflow

def helpMessage() {
    log.info """
    Usage:
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
    See here for more info: https://github.com/lifebit-ai/pcgr-nf
    """.stripIndent()
}

// Show help message
if (params.help) {
    helpMessage()
    exit 0
}

// Define Channels from input

// - Check input mode 
if (!params.vcf && !params.csv){ exit 1, "Essential parameters missing"}

if (params.vcf && params.csv){ exit 1, "Multiple modes selected. Run single file mode (--vcf and --name) or multiple file (--csv) independently"}

if (params.vcf){
    Channel
        .fromPath(params.input)
        .ifEmpty { exit 1, "Cannot find input file : ${params.vcf}" }
        .set { ch_input }
}

if (params.csv){
    Channel
        .fromPath(params.csv)
        .splitCsv(header:true)
        .map{ row -> file(row.vcf) }
        .flatten()
        .set { ch_input }
}

Channel.fromPath(params.pcgr_data)
    .ifEmpty { exit 1, "Cannot find data bundle path : ${params.pcgr_data}" }
    .set{ data_bundle }

Channel.fromPath(params.pcgr_config)
    .ifEmpty { exit 1, "Cannot find config file : ${params.pcgr_config}" }
    .set{ config }

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

process pcgr {
    tag "$input_file"
    label 'process_high'
    publishDir "${params.outdir}", mode: 'copy'
    publishDir "${params.outdir}/MultiQC", mode: 'copy', pattern: "multiqc_report.html"

    input:
    file input_file from out_vcf_filter
    path data from data_bundle
    path config_file from config

    output:
    file "multiqc_report.html"
    file "result/*"
    script:
    """
    mkdir result
    pcgr.py --input_vcf $input_file --pcgr_dir $data --output_dir result/ --genome_assembly $params.pcgr_genome --conf $config_file --sample_id $input_file.baseName --no_vcf_validate --no-docker

    cp result/*${params.pcgr_genome}.html multiqc_report.html
    """
}
