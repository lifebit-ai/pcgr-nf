#!/usr/bin/env python

import csv
import re
import argparse
import os
import subprocess
import logging
import sys
import getpass
import platform
import toml
import json
from argparse import RawTextHelpFormatter


PCGR_VERSION = '0.9.1'
DB_VERSION = 'PCGR_DB_VERSION = 20201123'
VEP_VERSION = '101'
GENCODE_VERSION = '35'
NCBI_BUILD_MAF = "GRCh38"
VEP_ASSEMBLY = "GRCh38"
DOCKER_IMAGE_VERSION = 'sigven/pcgr:' + str(PCGR_VERSION)


#global vep_assembly
global debug

tsites = {
		0: "Any",
      1: "Adrenal Gland",
      2: "Ampulla of Vater",
      3: "Biliary Tract",
      4: "Bladder/Urinary Tract",
      5: "Bone",
      6: "Breast",
      7: "Cervix",
      8: "CNS/Brain",
      9: "Colon/Rectum",
      10: "Esophagus/Stomach",
      11: "Eye",
      12: "Head and Neck",
      13: "Kidney",
      14: "Liver",
      15: "Lung",
      16: "Lymphoid",
      17: "Myeloid",
      18: "Ovary/Fallopian Tube",
      19: "Pancreas",
      20: "Peripheral Nervous System",
      21: "Peritoneum",
      22: "Pleura",
      23: "Prostate",
      24: "Skin",
      25: "Soft Tissue",
      26: "Testis",
      27: "Thymus",
      28: "Thyroid",
      29: "Uterus",
      30: "Vulva/Vagina"
	}

def __main__():

   tumor_sites = "1 = Adrenal Gland\n"
   tumor_sites = tumor_sites + "2 = Ampulla of Vater\n"
   tumor_sites = tumor_sites + "3 = Biliary Tract\n"
   tumor_sites = tumor_sites + "4 = Bladder/Urinary Tract\n"
   tumor_sites = tumor_sites + "5 = Bone\n"
   tumor_sites = tumor_sites + "6 = Breast\n"
   tumor_sites = tumor_sites + "7 = Cervix\n"
   tumor_sites = tumor_sites + "8 = CNS/Brain\n"
   tumor_sites = tumor_sites + "9 = Colon/Rectum\n"
   tumor_sites = tumor_sites + "10 = Esophagus/Stomach\n"
   tumor_sites = tumor_sites + "11 = Eye\n"
   tumor_sites = tumor_sites + "12 = Head and Neck\n"
   tumor_sites = tumor_sites + "13 = Kidney\n"
   tumor_sites = tumor_sites + "14 = Liver\n"
   tumor_sites = tumor_sites + "15 = Lung\n"
   tumor_sites = tumor_sites + "16 = Lymphoid\n"
   tumor_sites = tumor_sites + "17 = Myeloid\n"
   tumor_sites = tumor_sites + "18 = Ovary/Fallopian Tube\n"
   tumor_sites = tumor_sites + "19 = Pancreas\n"
   tumor_sites = tumor_sites + "20 = Peripheral Nervous System\n"
   tumor_sites = tumor_sites + "21 = Peritoneum\n"
   tumor_sites = tumor_sites + "22 = Pleura\n"
   tumor_sites = tumor_sites + "23 = Prostate\n"
   tumor_sites = tumor_sites + "24 = Skin\n"
   tumor_sites = tumor_sites + "25 = Soft Tissue\n"
   tumor_sites = tumor_sites + "26 = Testis\n"
   tumor_sites = tumor_sites + "27 = Thymus\n"
   tumor_sites = tumor_sites + "28 = Thyroid\n"
   tumor_sites = tumor_sites + "29 = Uterus\n"
   tumor_sites = tumor_sites + "30 = Vulva/Vagina\n"

   program_description = "Personal Cancer Genome Reporter (PCGR) workflow for clinical interpretation of " + \
      "somatic nucleotide variants and copy number aberration segments"
   program_options = "--input_vcf <INPUT_VCF> --pcgr_dir <PCGR_DIR> --output_dir <OUTPUT_DIR> --genome_assembly " + \
      " <GENOME_ASSEMBLY> --conf <CONFIG_FILE> --sample_id <SAMPLE_ID>"

   logger = getlogger('pcgr-get-OS')

   # NEW ARGUMENT PARSER FOR COMBINED RUN
   arg_dict = {}
   arg_dict['pcgr_dir'] = sys.argv[3]
   arg_dict['output_dir'] = os.path.join(os.getcwd(),'result/')
   arg_dict['sample_id'] = sys.argv[1]
   arg_dict['configuration_file'] = sys.argv[2]
   arg_dict['genome_assembly'] = sys.argv[4]
   arg_dict['output_pass_tsv'] = os.path.join(sys.argv[8], sys.argv[5])
   arg_dict['no_docker'] = True
   arg_dict['debug'] = False

   ## read PCGR configuration file
   config_option_file = sys.argv[6]
   with open(config_option_file) as json_file:
      config_options = json.load(json_file)
   
   ## read host_directories configuration file
   host_directories_file = sys.argv[7]
   with open(host_directories_file) as json_file:
      host_directories = json.load(json_file)

   ## Required arguments
   ## Check the existence of required arguments
   if arg_dict['pcgr_dir'] is None or not os.path.exists(arg_dict['pcgr_dir']):
      err_msg = "Required argument --pcgr_dir has no/undefined value (" + str(arg_dict['pcgr_dir']) + "). Type pcgr.py --help to view all options and required arguments"
      pcgr_error_message(err_msg,logger)
   
   if arg_dict['output_dir'] is None or not os.path.exists(arg_dict['output_dir']):
      err_msg = "Required argument --output_dir has no/undefined value (" + str(arg_dict['output_dir']) + "). Type pcgr.py --help to view all options and required arguments"
      pcgr_error_message(err_msg,logger)
   
   if arg_dict['configuration_file'] is None or not os.path.exists(arg_dict['configuration_file']):
      err_msg = "Required argument --conf has no/undefined value (" + str(arg_dict['configuration_file']) + "). Type pcgr.py --help to view all options and required arguments"
      pcgr_error_message(err_msg,logger)
   
   if arg_dict['genome_assembly'] is None:
      err_msg = "Required argument --genome_assembly has no/undefined value (" + str(arg_dict['genome_assembly']) + "). Type pcgr.py --help to view all options and required arguments"
      pcgr_error_message(err_msg,logger)
   
   if arg_dict['sample_id'] is None:
      err_msg = "Required argument --sample_id has no/undefined value (" + str(arg_dict['sample_id']) + "). Type pcgr.py --help to view all options and required arguments"
      pcgr_error_message(err_msg,logger)
   
   if len(arg_dict['sample_id']) <= 2 or len(arg_dict['sample_id']) > 35:
      err_msg = "Sample name identifier (--sample_id) requires a name with more than 2 characters (and less than 35). Current sample identifier: " + str(arg_dict['sample_id'])
      pcgr_error_message(err_msg,logger)

   ## Optional arguments
   ## Check the existence of Docker (if not --no_docker is et)
   global debug
   debug = False
   global DOCKER_IMAGE_VERSION

   if arg_dict['no_docker']:
      DOCKER_IMAGE_VERSION = None
   else:
      # check that script and Docker image version correspond
      check_docker_command = 'docker images -q ' + str(DOCKER_IMAGE_VERSION)
      output = subprocess.check_output(str(check_docker_command), stderr=subprocess.STDOUT, shell=True)
      if(len(output) == 0):
         err_msg = 'Docker image ' + str(DOCKER_IMAGE_VERSION) + ' does not exist, pull image from Dockerhub (docker pull ' + str(DOCKER_IMAGE_VERSION) + ')'
         pcgr_error_message(err_msg,logger)

   ## Run PCGR workflow (HTML report generation only!)
   run_pcgr(arg_dict, host_directories, config_options)

def pcgr_error_message(message, logger):
   logger.error('')
   logger.error(message)
   logger.error('')
   sys.exit(1)

def pcgr_warn_message(message, logger):
   logger.warning(message) 

def check_subprocess(logger, command):
   if debug:
      logger.info(command)
   try:
      output = subprocess.check_output(str(command), stderr=subprocess.STDOUT, shell=True)
      if len(output) > 0:
         print (str(output.decode()).rstrip())
   except subprocess.CalledProcessError as e:
      print (e.output.decode())
      exit(0)

def getlogger(logger_name):
   logger = logging.getLogger(logger_name)
   logger.setLevel(logging.DEBUG)

   # create console handler and set level to debug
   ch = logging.StreamHandler(sys.stdout)
   ch.setLevel(logging.DEBUG)

   # add ch to logger
   logger.addHandler(ch)

   # create formatter
   formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", "20%y-%m-%d %H:%M:%S")

   #add formatter to ch
   ch.setFormatter(formatter)

   return logger

def run_pcgr(arg_dict, host_directories, config_options):
   """
   Main function to run the PCGR workflow
   """

   debug = arg_dict['debug']
   docker_user_id = None
   tumor_only = 0
   cell_line = 0
   vcf_validation = 1
   include_trials = 0
   clinical_trials_set = "OFF"
   msi_prediction_set = "OFF"
   tmb_estimation_set = "OFF"
   msig_estimation_set = "OFF"

   ## set basic Docker run commands
   output_vcf = 'None'
   output_pass_vcf = 'None'
   output_pass_tsv = os.path.abspath(arg_dict['output_pass_tsv'])
   output_maf = 'None'
   uid = ''
   
   global GENCODE_VERSION, VEP_ASSEMBLY, NCBI_BUILD_MAF
   if arg_dict['genome_assembly'] == 'grch37':
      NCBI_BUILD_MAF = 'GRCh37'
      GENCODE_VERSION = 'release 19'
      VEP_ASSEMBLY = 'GRCh37'

   logger = getlogger('pcgr-get-OS')

   if docker_user_id:
      uid = docker_user_id
   elif platform.system() == 'Linux' or platform.system() == 'Darwin' or sys.platform == 'darwin' or sys.platform == 'linux2' or sys.platform == 'linux':
      uid = os.getuid()
   else:
      if platform.system() == 'Windows' or sys.platform == 'win32' or sys.platform == 'cygwin':
         uid = getpass.getuser()

   if uid == '':
      logger.warning('Was not able to get user id/username for logged-in user on the underlying platform (platform.system(): ' + \
         str(platform.system()) + ', sys.platform: ' + str(sys.platform) + '), now running PCGR as root')
      uid = 'root'

   vepdb_dir_host = os.path.join(str(host_directories['db_dir_host']),'.vep')
   input_vcf_docker = 'None'
   input_cna_docker = 'None'
   input_cna_plot_docker = 'None'
   input_conf_docker = 'None'
   panel_normal_docker = 'None'
   docker_cmd_run1 = ''
   docker_cmd_run2 = ''
   docker_cmd_run_end = ''
   ## panel-of-normals annotation
   pon_annotation = 0

   if host_directories['input_vcf_basename_host'] != 'NA':
      input_vcf_docker = os.path.join(host_directories['input_vcf_dir_host'], host_directories['input_vcf_basename_host'])
   if host_directories['input_cna_basename_host'] != 'NA':
      input_cna_docker = os.path.join(host_directories['input_cna_dir_host'], host_directories['input_cna_basename_host'])
   if host_directories['input_cna_plot_basename_host'] != 'NA':
      input_cna_plot_docker = os.path.join(host_directories['input_cna_plot_dir_host'], host_directories['input_cna_plot_basename_host'])
   if host_directories['input_conf_basename_host'] != 'NA':
      input_conf_docker = os.path.join(host_directories['input_conf_dir_host'], host_directories['input_conf_basename_host'])
   if host_directories['panel_normal_vcf_basename_host'] != 'NA':
      panel_normal_docker = os.path.join(host_directories['panel_normal_vcf_dir_host'], host_directories['panel_normal_vcf_basename_host'])

   data_dir = host_directories['base_dir_host']
   output_dir = host_directories['output_dir_host']
   vep_dir = vepdb_dir_host
   r_scripts_dir = ''

   check_subprocess(logger, docker_cmd_run1.replace("-u " + str(uid), "") + 'mkdir -p ' + output_dir + docker_cmd_run_end)

   print()

   ## Generation of HTML reports for VEP/vcfanno-annotated VCF and copy number segment file

   ttype = config_options['tumor_type']['type'].replace(" ","_").replace("/","@")
   logger = getlogger('pcgr-writer')
   logger.info("PCGR - STEP 4: Generation of output files - variant interpretation report for precision oncology")
   pcgr_report_command = (docker_cmd_run1 + os.path.join(r_scripts_dir, "pcgr.R") + " " + output_dir + " " + output_pass_tsv + " " + \
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
   print(pcgr_report_command)
   check_subprocess(logger, pcgr_report_command)
   logger.info("Finished")
   print()

if __name__=="__main__": __main__()

