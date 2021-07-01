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

if (params.vcf && params.csv){ exit 1, "Multiple modes selected. Run single file mode (--vcf) or multiple file (--csv) independently"}

if (params.vcf){
    Channel
        .fromPath(params.vcf)
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

// Check for valid reference options 
def human_reference_expected = ['grch37', 'grch38'] as Set
def parameter_diff = human_reference_expected - params.pcgr_genome
if (parameter_diff.size() > 1){
        println "[Pipeline warning] Parameter $params.pcgr_genome is not valid in the pipeline! Running with default 'grch38'\n"
        ch_reference = Channel.value('grch38')
    } else {
        ch_reference = Channel.value(params.pcgr_genome)
    }

// Custum scripts
projectDir = workflow.projectDir
getfilter = Channel.fromPath("${projectDir}/bin/filtervcf.py",  type: 'file', followLinks: false)
run_report = Channel.fromPath("${projectDir}/bin/report.py",  type: 'file', followLinks: false)
pcgr_toml_config = params.pcgr_config ? Channel.value(file(params.pcgr_config)) : Channel.fromPath("${projectDir}/bin/pcgr.toml", type: 'file', followLinks: false) 
style_css = Channel.fromPath("${projectDir}/bin/style.css",  type: 'file', followLinks: false)
logo_png = Channel.fromPath("${projectDir}/bin/logo.png",  type: 'file', followLinks: false)

if (!params.skip_filtering) {

    process check_fields {
        tag "$input_file"
        label 'process_low'

        input:
        file input_file from ch_input
        each file("filtervcf.py") from getfilter

        output:
        file input_file into ch_input_2
        file("filter") into filterstr

        script:
        "python filtervcf.py $input_file $params.min_qd $params.max_fs $params.max_sor $params.min_mq"
    }

    process vcffilter {
        tag "$input_file"
        label 'process_low'

        input:
        file input_file from ch_input_2
        file filter from filterstr

        output:
        file "*filtered.vcf" into ch_vcf_for_pcgr

        script:
        """
        if [ -s $filter ]; then 
            echo "No tags present in VCF for filtering"
            cp $input_file ${input_file.baseName}_filtered.vcf
        else
            vcffilter -s -f \$(cat $filter) $input_file > ${input_file.baseName}_filtered.vcf
        fi
        """
    }
}else{
    ch_vcf_for_pcgr = ch_input
}


process pcgr {
    tag "$input_file"
    label 'process_high'
    publishDir "${params.outdir}", mode: 'copy'

    input:
    file input_file from ch_vcf_for_pcgr
    each path(data) from data_bundle
    each file(config_toml) from pcgr_toml_config
    each reference from ch_reference

    output:
    file "*_pcgr.html" into out_pcgr
    file "result/*"

    script:
    """
    # Modify config_toml pass the params
    cp ${config_toml} new_config.toml

    # Swap placeholders with user provided values
    sed -i "s/maf_onekg_eur_placeholder/${params.maf_onekg_eur}/g" new_config.toml
    sed -i "s/maf_onekg_amr_placeholder/${params.maf_onekg_amr}/g" new_config.toml
    sed -i "s/maf_onekg_afr_placeholder/${params.maf_onekg_afr}/g" new_config.toml
    sed -i "s/maf_onekg_sas_placeholder/${params.maf_onekg_sas}/g" new_config.toml
    sed -i "s/maf_onekg_eas_placeholder/${params.maf_onekg_eas}/g" new_config.toml
    sed -i "s/maf_onekg_global_placeholder/${params.maf_onekg_global}/g" new_config.toml
    sed -i "s/maf_gnomad_nfe_placeholder/${params.maf_gnomad_nfe}/g" new_config.toml
    sed -i "s/maf_gnomad_amr_placeholder/${params.maf_gnomad_amr}/g" new_config.toml
    sed -i "s/maf_gnomad_afr_placeholder/${params.maf_gnomad_afr}/g" new_config.toml
    sed -i "s/maf_gnomad_asj_placeholder/${params.maf_gnomad_asj}/g" new_config.toml
    sed -i "s/maf_gnomad_sas_placeholder/${params.maf_gnomad_sas}/g" new_config.toml
    sed -i "s/maf_gnomad_eas_placeholder/${params.maf_gnomad_eas}/g" new_config.toml
    sed -i "s/maf_gnomad_fin_placeholder/${params.maf_gnomad_fin}/g" new_config.toml
    sed -i "s/maf_gnomad_oth_placeholder/${params.maf_gnomad_oth}/g" new_config.toml
    sed -i "s/maf_gnomad_global_placeholder/${params.maf_gnomad_global}/g" new_config.toml
    sed -i "s/exclude_pon_placeholder/${params.exclude_pon}/g" new_config.toml
    sed -i "s/exclude_likely_hom_germline_placeholder/${params.exclude_likely_hom_germline}/g" new_config.toml
    sed -i "s/exclude_likely_het_germline_placeholder/${params.exclude_likely_het_germline}/g" new_config.toml
    sed -i "s/exclude_dbsnp_nonsomatic_placeholder/${params.exclude_dbsnp_nonsomatic}/g" new_config.toml
    sed -i "s/exclude_nonexonic_placeholder/${params.exclude_nonexonic}/g" new_config.toml
    sed -i "s/tumor_dp_tag_placeholder/${params.tumor_dp_tag}/g" new_config.toml
    sed -i "s/tumor_af_tag_placeholder/${params.tumor_af_tag}/g" new_config.toml
    sed -i "s/control_dp_tag_placeholder/${params.control_dp_tag}/g" new_config.toml
    sed -i "s/control_af_tag_placeholder/${params.control_af_tag}/g" new_config.toml
    sed -i "s/call_conf_tag_placeholder/${params.call_conf_tag}/g" new_config.toml
    sed -i "s/report_theme_placeholder/${params.report_theme}/g" new_config.toml
    sed -i "s/custom_tags_placeholder/${params.custom_tags}/g" new_config.toml
    sed -i "s/list_noncoding_placeholder/${params.list_noncoding}/g" new_config.toml
    sed -i "s/n_vcfanno_proc_placeholder/${params.n_vcfanno_proc}/g" new_config.toml
    sed -i "s/n_vep_forks_placeholder/${params.n_vep_forks}/g" new_config.toml
    sed -i "s/vep_pick_order_placeholder/${params.vep_pick_order}/g" new_config.toml
    sed -i "s/vep_skip_intergenic_placeholder/${params.vep_skip_intergenic}/g" new_config.toml
    sed -i "s/vcf2maf_placeholder/${params.vcf2maf}/g" new_config.toml

    # Run PCGR
    mkdir result
    pcgr.py --tumor_site ${params.pcgr_tumor_site} --input_vcf $input_file --pcgr_dir $data --output_dir result/ --genome_assembly $reference --conf new_config.toml --sample_id $input_file.baseName --no_vcf_validate --no-docker

    # Save RMarkdown report
    cp result/*${reference}.html ${input_file.baseName}_pcgr.html
    """
}

process report {
    label 'process_low'
    publishDir "${params.outdir}/MultiQC", mode: 'copy'

    input:
    file report from out_pcgr.collect()
    each file("report.py") from run_report
    file style from style_css
    file logo from logo_png

    output:
    file "*.html"
    file report

    script:
    "python report.py $style $logo $report"

}