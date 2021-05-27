#!/usr/bin/env python3

import os
import sys
import glob
import json
import subprocess 
from subprocess import PIPE


def main():

    print("Argument List:", str(sys.argv))

    # input 
    try:
        sample_id = sys.argv[1]
        input_conf_docker = sys.argv[2]
        data_dir = sys.argv[3]
        genome_assembly = sys.argv[4]
        output_pass_tsv = sys.argv[5]
        config_option_file = sys.argv[6]
    except IndexError as e:
        print(e, "files not found")
        sys.exit(1)

    # default options
    input_cna_docker = None
    PCGR_VERSION = 'dev_lifebit'
    input_cna_plot_docker = None
    tumor_only = 0
    cell_line = 0
    include_trials = 0
    output_dir = 'result/'

    # load config dict
    with open(config_option_file) as json_file:
        config_options = json.load(json_file)
    
    ttype = config_options['tumor_type']['type'].replace(" ","_").replace("/","@")

    pcgr_report_command = ['pcgr.R', 
                            output_dir, 
                            output_pass_tsv,
                            str(input_cna_docker),
                            sample_id,
                            input_conf_docker,
                            str(PCGR_VERSION),
                            genome_assembly,
                            data_dir,
                            str(input_cna_plot_docker), 
                            str(config_options['tumor_purity']),
                            str(config_options['tumor_ploidy']),
                            str(config_options['assay']),
                            str(tumor_only),
                            str(config_options['tmb']['run']),
                            str(config_options['tmb']['algorithm']),
                            str(config_options['msi']['run']),
                            str(config_options['msigs']['run']),
                            str(config_options['tmb']['target_size_mb']),
                            str(config_options['cna']['logR_homdel']),
                            str(config_options['cna']['logR_gain']),
                            str(config_options['cna']['cna_overlap_pct']),
                            str(config_options['msigs']['mutation_limit']),
                            str(config_options['msigs']['all_reference_signatures']),
                            str(config_options['allelic_support']['tumor_af_min']),
                            str(config_options['allelic_support']['tumor_dp_min']),
                            str(config_options['allelic_support']['control_af_max']),
                            str(config_options['allelic_support']['control_dp_min']),
                            str(cell_line),
                            str(include_trials),
                            str(ttype)]

    print("Running command: " + ' '.join(pcgr_report_command))

    p = subprocess.Popen(pcgr_report_command, stdout=PIPE, stderr=PIPE, shell=False)
    stdout, stderr = p.communicate()

    try:
        stderr = stderr.decode("utf8")
    except (UnicodeDecodeError, AttributeError):
        stderr = str(stderr)

    print("Finished subprocess with STDOUT:\n"
                "======================================\n{}".format(stdout))
    print("Fished subprocesswith STDERR:\n"
                "======================================\n{}".format(stderr))
    print("Finished with return code: {}".format(p.returncode))

    try:
        report_file = glob('result/*{}.html'.format(genome_assembly))[0]
        os.rename(report_file, "multiqc_report.html")
    except:
        sys.exit(2)

if __name__ == '__main__':
    main()