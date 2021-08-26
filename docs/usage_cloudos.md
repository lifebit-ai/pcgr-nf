# Running pcgr-nf pipeline on CloudOS

Example CloudOS pcgr-nf job with test data: [CloudOS job link](https://cloudos.lifebit.ai/public/jobs/611a2c927db707019a066cbf)
<br>
<br>

## 1. Make sure the pipeline is available in your workspace

Once logged in to a workspace, got to the "Pipelines" tab, and search for `pcgr` in "Curated pipelines and tools" or "Workspaces tools". If you don't find a pipeline that refers to `lifebit-ai/pcgr-nf` repository (Pipeline name can vary though), then you can import the pipeline yourself. For this click "New", select Nextflow option, type in the current repo URL, and import the pipeline.
<br>
<br>

## 2. Prepare input data

> *If you wish to try first using the test data you can skip this step for now*

The only required input by the PCGR pipeline is the VCF file(s) containing somatic mutations to be analysed and annotated by PCGR. PCGR reference files are fetched automatically based on which human genome build version is used, unless you wish to provide a custom PCGR-compatible reference data bundle.

If you have the file(s) locally or on an HPC environment, you can upload them to CloudOS datasets and use them from there. If you have your VCF files already stored on an Amazon S3 bucket, you will be able to provide these files to the pipeline by just giving the S3 link to the file, no upload needed.

### 2.1 Uploading to CloudOS

You can upload the VCF file(s) to your CloudOS workspace at the "Data and results" page by creating a new dataset and choosing "Add data & folders" > "Upload files" option. Alternatively you could link VCF files from a linked S3 bucket. In this case the files themselves will stay in the source S3 bucket, and appear only as links in the CloudOS dataset, meaning no additional storage will be occupied.

### 2.2 CSV file for providing multiple VCFs

While you will be able to provide a single VCF to the pipeline simply by using the `--vcf my_file.vcf` pipeline option, it is not possible to provide more than one VCF this way.

To provide more than one VCF to be analysed pipeline, it's required to use a CSV file that provides paths to all vcf files. You can create this file locally and upload it to CloudOS as any other file.

The CSV file used for the test run - [testdata/testdata.csv](https://github.com/lifebit-ai/pcgr-nf/blob/upd-test-and-docs/testdata/testdata.csv)

An example csv file:
`my_vcf_list.csv`:

``` bash
vcf
s3://my-bucket/full/path/to/my_vcf_1.vcf
s3://my-bucket/full/path/to/my_vcf_2.vcf
s3://my-bucket/full/path/to/my_vcf_3.vcf
```

You can then provide this CSV file to the pipeline with a `--csv my_vcf_list.csv` option.

To get the S3 paths of files uploaded to CloudOS you can click the *"Text file"* blue icon on the very right from the file name in Data & Results page. This will copy the S3 path to your clipboard, and you will be able to paste it to the CSV file you are creating. For the files located on an external S3 bucket you should use their full URIs as shown in example CSV above.
<br>
<br>

## 3. Create a config file

> *If you wish to try first using the test data you can skip this step for now*

The best way to provide all the pipeline inputs would be by using a config file. However, if you'd like to provide all parameters as CloudOS job arguments, you can skip this step.

Example config file looks as follows - [conf/test.config](https://github.com/lifebit-ai/pcgr-nf/blob/upd-test-and-docs/conf/test.config):

``` bash
params {
    csv = 's3://lifebit-featured-datasets/pipelines/pcgr/testdata/test_1/testdata.csv'
    genome = 'grch38'

    max_cpus = 2
    max_memory = 4.GB
}
```

- `params {...}` is a [nextflow scope](https://www.nextflow.io/docs/latest/config.html#scope-params) to define all the parameters in a config file. You could also define parameters as `params.csv`, `params.genome` etc if you wish not to use the scope.
- with `csv` parameter we provide the S3 path to the CSV file that lists paths to multiple VCF files
- `genome` parameter defines human genome build version. It can be either `grch38` or `grch37` (Must be lowercase, nextflow is case-sensitive). This parameter is shown here only for demonstration purposes, because y default its value is already `grch38`. But make sure to change the default if using VCF files from `grch37` build.
- `max_cpus` and `max_memory` defines maximal resources to be used by a single process of the pipeline (not maximum total resources used by the pipeline, many small processes will still be parallelized if possible). Here we provide small valuse - only 2 CPUs and 4 Gb of RAM because we will be using small test data and that shouldbe enough. However for real-world data the defaults of 16 CPUs and 30 Gb RAM is recommended. Make sure to choose a machine that has at least this number of resources to run the pipeline on CloudOS, otherwise the job may fail.
- you can also define any other parameters in this config that are listed on the [main page](https://github.com/lifebit-ai/pcgr-nf) of this repository.

If you create a config file make sure to also upload it to a CloudOS datasets.
<br>
<br>

## 4. Run the pipeline on CloudOS

Once you have all input files and config prepared, you can submit the job.

1. From the pipelines page select the PCGR pipeline (see step 1 of this guide).
2. On the parameter setting page add a parameter `config`, and using a dataset viewer (blue data icon on the right) select the config file you created for your analysis. If you wish to use the pipeline's test config file, just paste the value `conf/test.config` for the `config` parameter value. This will use the pipeline in-built config that uses test data. If you decided not to use the config file, you can also provide all the parameters here individually. You can provide the VCF or CSV file for corresponding parameters by using the dataset viewer too. You could also paste in the full S3 path to your file to the argument value filed if you already have it without going to the dataset viewer.
3. Once config file or all other parameters are set, you can procced to job configuration by pressing the "Next" button in the upper right corner.
4. On the configuration page you can configure the instance type to be used for the job (Select instance size according to resources specified by `max_cpus` and `max_memory`, or 16 CPUs and 30 Gb if you use the defaults). Additionally you can add a maximum cost limit to your job (job will terminate if it reaches the limit), or make the job resumable to be able to use the nextflow [`-resume`](https://www.nextflow.io/docs/latest/cli.html?highlight=resume) option later on.
5. After the configuration is set, you can submit the job by pressing the "Run job" button in the upper right corner. the submitted job will take 3-5 minutes to initialize, and then the page will show you the pipeline progress until it is completed.
<br>


## 5. Investigate the report

Once the job is completed, you should be able to see two new tabs appear at the top: "Results" and "Report". Open the report tab.

Here you can see the summary information for somatic variants annotated, as well as by-gene and by-variant level information.
<br>
<br>

## 6. Using the pipeline results for further analysis

Under the "Results" tab you can find all the files generated by the pipeline. The main output file that can be used by downstream analysis is the `combined.tiers.tsv`. This file has information about all input variants annotated by PCGR and with added sample-level metadata. The table is in "long data" format, which makes it convenient for further filtering and segregation.

Under the `result` folder you can find all the raw files produced by PCGR and the sample-level output if you want to dig in into particular sample results.
