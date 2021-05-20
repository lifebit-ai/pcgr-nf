ttype = config_options['tumor_type']['type'].replace(" ","_").replace("/","@")


pcgr_report_command = (docker_cmd_run1 + os.path.join(r_scripts_dir, "pcgr.R") + " " + output_dir + " " + str(output_pass_tsv) + ".gz" + " " + \
                    input_cna_docker + " " + str(arg_dict['sample_id']) + " " + input_conf_docker + " " + str(PCGR_VERSION) + " " +  \
                    str(arg_dict['genome_assembly']) + " " + data_dir + " " + \
                    str(input_cna_plot_docker) + " " + str(config_options['tumor_purity']) + " " + \
                    str(config_options['tumor_ploidy']) + " " + str(config_options['assay']) + " " + str(tumor_only) +  " " + \
                    str(config_options['tmb']['run']) + " " + str(config_options['tmb']['algorithm']) + " " + \
                    str(config_options['msi']['run']) + " " + str(config_options['msigs']['run']) + " " + \
                    str(config_options['tmb']['target_size_mb']) + " " + str(config_options['cna']['logR_homdel']) + " " + \
                    str(config_options['cna']['logR_gain']) + " " + str(config_options['cna']['cna_overlap_pct']) + " "  + \
                    str(config_options['msigs']['mutation_limit']) + " " + str(config_options['msigs']['all_reference_signatures']) + " " + \
                    str(config_options['allelic_support']['tumor_af_min']) + " " + str(config_options['allelic_support']['tumor_dp_min']) + " "  + \
                    str(config_options['allelic_support']['control_af_max']) + " " + str(config_options['allelic_support']['control_dp_min']) + " " + \
                    str(cell_line) + " " + str(include_trials) + " " + str(ttype) + docker_cmd_run_end)
check_subprocess(logger, pcgr_report_command)