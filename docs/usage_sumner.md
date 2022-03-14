# Supplemental guide for running pcgr-nf pipeline on Sumner HPC

## Clone the repository to your workspace

    cd $yourDirectory/
    git clone -b dev_addSumnerConfig https://github.com/AaronMichaelTaylor/pcgr-nf/
    cd ./pcgr-nf


## Optional: make a local copy of the PCGR data bundles for faster execution

    mkdir pcgr_data/ && cd $_
    wget https://insilico.hpc.uio.no/pcgr/pcgr.databundle.grch38.20201123.tgz
    gzip -dc pcgr.databundle.grch38.20201123.tgz | tar xvf -
    cd ..

* [grch37 data bundle - 20201123](http://insilico.hpc.uio.no/pcgr/pcgr.databundle.grch37.20201123.tgz) (approx 17Gb)
* [grch38 data bundle - 20201123](http://insilico.hpc.uio.no/pcgr/pcgr.databundle.grch38.20201123.tgz) (approx 18Gb)

## Use `sumnerTest.pbs` as a template for your run

If you created a local copy of the PCGR data bundle, make sure to modify the modify the `pcgr_data` parameter. Use the unmodified script to run the test data.

## Submit your job to the cluster

    sbatch sumnerTest.pbs
