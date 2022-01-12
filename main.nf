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
    --pcgr_genome   Reference genome assembly
                    (default: $params.pcgr_genome)
    --pcgr_data     URL for reference data bundle.
                    Optional file. Can be passed as a path to the folder or to a tarball (compressed or not).
                    If not provided, the appropriate data bundle is infered from --pcgr_genome. 
                    (default: $params.pcgr_genome)

    Optional paramenters:
    --metadata      `CSV` file with metadata information.
                    Available only when using --csv mode
                    Should be a `*.csv` file with the first column called `vcf` and the path to each file, one per line,
                    matching the file in --csv, followed by metadata, one per column, for each sample. 
                    The column `histological_type` is required to be present.
                    See example in `testdata/metadata.csv`.

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


// Header log info
def summary = [:]
summary['Max Resources']    = "$params.max_memory memory, $params.max_cpus cpus, $params.max_time time per job"
if (workflow.containerEngine) summary['Container'] = "$workflow.containerEngine - $workflow.container"
summary['Output dir']       = params.outdir
summary['Launch dir']       = workflow.launchDir
summary['Working dir']      = workflow.workDir
summary['Script dir']       = workflow.projectDir
summary['User']             = workflow.userName
summary['Config Profile']   = workflow.profile
summary['Additional config']= params.config
summary['Input file']       = params.vcf ? params.vcf : params.csv
summary['Genome']           = params.pcgr_genome 
if (params.pcgr_data) summary['Custom PCGR data'] = params.pcgr_data
summary['PCGR config']      = params.pcgr_config
log.info summary.collect { k,v -> "${k.padRight(20)}: $v" }.join("\n")
log.info "-\033[2m--------------------------------------------------\033[0m-"

// Define Channels from input

// - Check input mode 
if (!params.vcf && !params.csv){ exit 1, "Essential parameters missing"}

if (params.vcf && params.csv){ exit 1, "Multiple modes selected. Run single file mode (--vcf) or multiple file (--csv) independently"}

if (!params.pcgr_data && !params.pcgr_genome){ exit 1, "Essential parameters missing. The reference genome needs to be defined (--pcg_genome) to properly load the pcgr database (--pcgr_data)"}

if (params.metadata && !params.csv){ exit 1, "Metadata can only be used with multiple file mode (--csv)"}

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

if (params.pcgr_data){
    Channel.fromPath(params.pcgr_data)
        .ifEmpty { exit 1, "Cannot find data bundle path : ${params.pcgr_data}" }
        .set{ data_bundle }
}

Channel.fromPath(params.pcgr_config)
    .ifEmpty { exit 1, "Cannot find config file : ${params.pcgr_config}" }
    .set{ config }

// Check for valid reference options 
if (!params.genomes.containsKey(params.pcgr_genome)){exit 1, "Error: Parameter $params.pcgr_genome is not valid in the pipeline. Available values: ${params.genomes.keySet().join(", ")}"}
if (!params.pcgr_data){
    pcgr_data = params.genomes[params.pcgr_genome].pcgr_data
} else {
    pcgr_data = params.pcgr_data
}

data_bundle = Channel.fromPath(pcgr_data)
ch_reference = Channel.value(params.pcgr_genome)


// Check for valid output mode options 
def report_expected = ['summary', 'report'] as Set
def report_parameter_diff = report_expected - params.report_mode
if (report_parameter_diff.size() > 1){
        println "[Pipeline warning] Parameter $params.report_mode is not valid in the pipeline! Running with default 'report'\n"
        report_mode = 'report'
    } else {
        report_mode = params.report_mode
    }

// Check optional metadata file
ch_optional_metadata = params.metadata ? Channel.fromPath(params.metadata) : "null"

// Custum scripts
projectDir = workflow.projectDir
getfilter = Channel.fromPath("${projectDir}/bin/filtervcf.py",  type: 'file', followLinks: false)
run_report = Channel.fromPath("${projectDir}/bin/report.py",  type: 'file', followLinks: false)
pcgr_toml_config = params.pcgr_config ? Channel.value(file(params.pcgr_config)) : Channel.fromPath("${projectDir}/bin/pcgr.toml", type: 'file', followLinks: false) 
combine_tables = Channel.fromPath("${projectDir}/bin/combine.py",  type: 'file', followLinks: false)
pivot_gene_simple_py = Channel.fromPath("${projectDir}/bin/pivot_gene_simple.py",  type: 'file', followLinks: false)
pivot_gene_complete_py = Channel.fromPath("${projectDir}/bin/pivot_gene_complete.py",  type: 'file', followLinks: false)
pivot_variant_py = Channel.fromPath("${projectDir}/bin/pivot_variant.py",  type: 'file', followLinks: false)
plot_tiers_py = Channel.fromPath("${projectDir}/bin/tiers_plot.py",  type: 'file', followLinks: false)

if (params.filtering) {

    process check_fields {
        tag "$input_file"
        label 'process_low'

        publishDir "${params.outdir}/process-logs/${task.process}/${input_file}/", pattern: "command-logs-*", mode: 'copy'

        input:
        file input_file from ch_input
        each file("filtervcf.py") from getfilter

        output:
        file input_file into ch_input_2
        file("filter") into filterstr
        file("command-logs-*") optional true

        script:
        """
        python filtervcf.py $input_file $params.min_qd $params.max_fs $params.max_sor $params.min_mq

        # save .command.* logs
        ${params.savescript}
        """
    }

    process vcffilter {
        tag "$input_file"
        label 'process_low'

        publishDir "${params.outdir}/process-logs/${task.process}/${input_file}/", pattern: "command-logs-*", mode: 'copy'

        input:
        file input_file from ch_input_2
        file filter from filterstr

        output:
        file "*filtered.vcf" into ch_vcf_for_pcgr
        file("command-logs-*") optional true

        script:
        """
        if [ -s $filter ]; then 
            echo "No tags present in VCF for filtering"
            cp $input_file ${input_file.baseName}_filtered.vcf
        else
            vcffilter -s -f \$(cat $filter) $input_file > ${input_file.baseName}_filtered.vcf
        fi

        # save .command.* logs
        ${params.savescript}
        """
    }
}else{
    ch_vcf_for_pcgr = ch_input
}

process check_data_bundle {
    label 'process_high'

    publishDir "${params.outdir}/process-logs/${task.process}/", pattern: "command-logs-*", mode: 'copy'

    input:
    path(data) from data_bundle

    output:
    file("*") into data_bundle_checked
    file("command-logs-*") optional true

    script:
    """
    # Check if data is compressed
    if [[ -d $data ]]; then
        echo "$data is a directory"
        mv $data data_bundle
    elif [[ -f $data ]]; then
        echo "$data is a file"
        data_bundle_name=`echo $data | cut -d'.' --complement -f2-`
        echo \$data_bundle_name

        { # try compressed tar file
            tar -xvzf $data
        } || { # catch - not in gzip format
            tar -xvf $data
        }
        mv \$data_bundle_name data_bundle
    fi

    # save .command.* logs
    ${params.savescript}
    """
}

process pcgr {
    tag "$input_file"
    label 'process_high'

    publishDir "${params.outdir}", pattern: "result*", mode: 'copy'
    publishDir "${params.outdir}/process-logs/${task.process}/${input_file}/", pattern: "command-logs-*", mode: 'copy'

    input:
    file input_file from ch_vcf_for_pcgr
    each path(data) from data_bundle_checked
    each file(config_toml) from pcgr_toml_config
    each reference from ch_reference

    output:
    file "*_pcgr.html" into out_pcgr
    file "result/*.tiers.tsv" into pcgr_tsv
    file "result/*"
    file("command-logs-*") optional true

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
    pcgr.py --tumor_site ${params.pcgr_tumor_site} --input_vcf $input_file --pcgr_dir ${data[1]} --output_dir result/ --genome_assembly $reference --conf new_config.toml --sample_id $input_file.baseName --no_vcf_validate --no-docker

    # Save RMarkdown report
    cp result/*${reference}.html ${input_file.baseName}_pcgr.html

    # save .command.* logs
    ${params.savescript}
    """
}

process combine_tiers {
    label "process_low"

    publishDir "${params.outdir}", pattern: "*.tsv", mode: 'copy'
    publishDir "${params.outdir}/process-logs/${task.process}/", pattern: "command-logs-*", mode: 'copy'
    
    input:
    file tables from pcgr_tsv.collect()
    each file(metadata) from ch_optional_metadata
    each file("combine.py") from combine_tables

    output:
    file("combined.tiers.tsv") into (combined_tiers_gene_simple, combined_tiers_gene_complete, combined_tiers_variant, combined_tiers_plot)
    file("command-logs-*") optional true

    script:
    optional_metadata = params.metadata ? "$metadata": "PASS"
    """
    python combine.py $optional_metadata $tables

    # save .command.* logs
    ${params.savescript}
    """
}

if (report_mode == 'report') {
    process report {
        label 'process_low'

        publishDir "${params.outdir}/MultiQC", mode: 'copy', pattern: "*.html"
        publishDir "${params.outdir}/process-logs/${task.process}/", pattern: "command-logs-*", mode: 'copy'

        input:
        file report from out_pcgr.collect()
        each file("report.py") from run_report

        output:
        file "*.html"
        file report
        file("command-logs-*") optional true

        script:
        """
        python report.py $report

        # save .command.* logs
        ${params.savescript}
        """
    }

} else {

        process pivot_table_gene_simple {
        label 'process_low'

        publishDir "${params.outdir}", pattern: "*.tsv", mode: 'copy'
        publishDir "${params.outdir}/process-logs/${task.process}/", pattern: "command-logs-*", mode: 'copy'

        input:
        file tiers from combined_tiers_gene_simple
        each file("pivot_gene_simple.py") from pivot_gene_simple_py

        output:
        file("pivot_gene_simple.tsv") into pivot_tiers_gene_simple
        file("command-logs-*") optional true

        script:
        metadata_opt = params.metadata ? "true": "false"
        """
        python pivot_gene_simple.py $tiers ${params.columns_genes_simple} $task.cpus $metadata_opt
        
        # save .command.* logs
        ${params.savescript}
        """
    }

    process pivot_table_gene_complete {
        label 'process_low'

        publishDir "${params.outdir}", pattern: "*.tsv", mode: 'copy'
        publishDir "${params.outdir}/process-logs/${task.process}/", pattern: "command-logs-*", mode: 'copy'

        input:
        file tiers from combined_tiers_gene_complete
        each file("pivot_gene_complete.py") from pivot_gene_complete_py

        output:
        file("pivot_gene_complete.tsv") into pivot_tiers_gene_complete
        file("command-logs-*") optional true

        script:
        """
        python pivot_gene_complete.py $tiers ${params.columns_genes_complete} $task.cpus

        # save .command.* logs
        ${params.savescript}
        """
    }

    process pivot_table_variant {
        label 'process_low'

        publishDir "${params.outdir}", pattern: "*.tsv", mode: 'copy'
        publishDir "${params.outdir}/process-logs/${task.process}/", pattern: "command-logs-*", mode: 'copy'

        input:
        file tiers from combined_tiers_variant
        each file("pivot_variant.py") from pivot_variant_py

        output:
        file("pivot_variant.tsv") into pivot_tiers_variant
        file("command-logs-*") optional true

        script:
        """
        python pivot_variant.py $tiers ${params.columns_variants} $task.cpus

        # save .command.* logs
        ${params.savescript}
        """
    }

    process plot_tiers {
        label 'process_low'

        publishDir "${params.outdir}", pattern: "*.png", mode: 'copy'
        publishDir "${params.outdir}/process-logs/${task.process}/", pattern: "command-logs-*", mode: 'copy'

        input:
        file tiers from combined_tiers_plot
        each file("tiers_plot.py") from plot_tiers_py

        output:
        file("tiers.png") into tiers_plot
        file("command-logs-*") optional true

        script:
        """
        python tiers_plot.py $tiers

        # save .command.* logs
        ${params.savescript}
        """
    }

    process summary {
        label 'process_low'

        publishDir "${params.outdir}/MultiQC", mode: 'copy', pattern: "*.html"
        publishDir "${params.outdir}/process-logs/${task.process}/", pattern: "command-logs-*", mode: 'copy'

        input:
        file gene_table_simple from pivot_tiers_gene_simple
        file gene_table_complete from pivot_tiers_gene_complete
        file variant_table from pivot_tiers_variant
        file plot_tiers from tiers_plot

        output:
        file "multiqc_report.html"
        file("command-logs-*") optional true

        script:
        """
        cp ${workflow.projectDir}/bin/* .
        R -e "rmarkdown::render('report.Rmd', params = list(ptable_gene_simple='${gene_table_simple}', ptable_gene_complete='${gene_table_complete}', ptable_variant='${variant_table}', pplot_tiers='${plot_tiers}'))"
        mv report.html multiqc_report.html

        # save .command.* logs
        ${params.savescript}
        """
    }

}
