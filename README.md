## docker ##

This project builds various docker images associated with TOPMed.  There are two types of docker images: (1) core images and (2) TOPMed images.  All of the TOPMed images are built upon the core  images.

The core docker images are:
- `ubuntu-18.04-hpc` - ubuntu 18.04; python2; python3; hdf5; mpich; openmpi; Intel's MKL
- `apps` - samtools; locuszoom; awscli; boto3; unzip; king built from `ubuntu-18.04-hpc`
- `r-3.6.1-mkl` - R 3.6.1 built from `apps` using the MKL

The TOPMed images are associated with the TOPMed analysis pipeline.  The analysis pipeline includes python and R code. It has two major branches in its git hub repository: master and devel. The TOPMed docker images are built based on the branches of the git hub repository for the analysis pipeline.  The TOPMed docker images are:
- `tm-rpkgs-master` - All of TOPMed R packages based on the `master` branch of the analysis pipeline and built from the `r-3.6.1-mkl` image
- `tm-rpkgs-devel` - Only `SeqVarTools`, `GENESIS`, and `TopmedPipeline` R packages and built from the `tm-rpkgs-master` image
- `topmed-master` - Master branch of the analysis pipeline built from the `tm-rpkgs-master` image
- `topmed-devel`  - Devel branch of the analysis pipeline based built from the `tm-rpkgs-devel` image

The project includes the following files:
- a makefile for building the docker images (see below)
- docker build files associated with building the docker images
- python files added to the `topmed-devel` image and the `topmed-master` image
- although not in this repository, the MKL installation tar file must also be in the makefile directory (_see **special note** below_)

## building the docker images ##

The docker images are built by executing the makefile (`Makefile`).  The makefile builds the core images and one of the two TOPMed images (i.e., either `topmed-master` or `topmed-devel`).  In building a TOPMed image there are two tagged versions: `latest` and a version number of TopmedPipeline (e.g., 2.6).

There are two ways to control various aspects of the makefile:
1. modifying macros via command line arguments
2. modifying macros within the makefile

The makefile also defines the following dependencies:
- dependencies between the different images,
- an image target file associated with each docker image
- the date of the image build file compared to the image target file


By default (i.e., if none of the macros are altered and there are no image target files), the makefile will build and create the following:
- uwgac/ubuntu-18.04-hpc:latest
- uwgac/ubuntu-18.04-hpc:11.1.2019
- uwgac/apps:latest
- uwgac/apps:11.1.2019
- uwgac/r-3.6.1-mkl:latest
- uwgac/r-3.6.1-mkl:3.6.1
- uwgac/tm-rpkgs-master:latest
- uwgac/tm-rpkgs-master:2.7.5
- uwgac/tm-rpkgs-devel:latest
- uwgac/tm-rpkgs-devel:2.7.5
- uwgac/topmed-devel:latest
- uwgac/topmed-devel:2.7.5

A partial list of the macros include:
- GTAG - the git branch of the analysis pipeline [Default: devel]
- R_VERSION - the version of R to build [Default: 3.6.1]
- MKL_VERSION - the version of the MKL tar gz file [Default: l_mkl_2019.2.187.tgz]
- DEVEL_VERSION - the devel tag of TopmedPipeline version [Default: 2.7.5]
- OS_VERSION - Ubuntu version [Default: 18.04]

#### Examples of executing the makefile ####

1. No command execution
```{r}
make -n
```
With the _-n_ option, make outputs the various commands without executing them.

2. Build the docker images
```{r}
make
```
When appropriate executes commands to build the docker core images; and the TOPMed image using the devel branch of the analysis pipeline.

3. Build the master docker images
```{r}
make GTAG=master
```
When appropriate executes commands to build the docker core images; and the TOPMed images using the master branch of the analysis pipeline.  The TOPMed images will be:
- uwgac/topmed-master:latest
- uwgac/topmed-master:2.6.0

4. Create images based on R 3.6.3

```{r}
make R_VERSION=3.6.3
```
When appropriate executes commands to build the docker core images; and the TOPMed image using the devel branch of the analysis pipeline.

## docker build files ##

The docker build files are:
1. ubuntu-18.04-hpc.dfile - Builds a ubuntu-based image with hpc functionality.
2. apps.dfile - From the ubuntu-based image, builds an application image including the applications `samtools` and `locuszoom`.
3. r-mkl.dfile - Builds an R image from the application image using both sequential and parallel MKL.
4. tm-rpkgs-master.dfile - Builds all of TOPMed R packages based on the `master` branch of the analysis pipeline
5. tm-rpkgs-devel.dfile - Only `SeqVarTools`, `GENESIS`, and `TopmedPipeline` R packages based on the `devel` branch
5. topmed.dfile - Builds either `topmed-devel`or `topmed-master` image


## python files ##

The python files are:
- ap2batch.py
- submit_job.py
- jstats.py

#### jstats.py ####

When an analysis (via the analysis pipeline) is run on AWS batch, a job information file (e.g., `association_jobinfo.txt`) is produced that contains the job ids of the submitted jobs.  The `jstats.py` python script can either describe a specified job id or describe all the jobs in a specified jobinfo file.

#### ap2batch.py ####

The `ap2batch.py` python file added to the docker images `topmed-master` and `topmed-devel` and stored in `/usr/local/bin`. `ap2batch.py` and it's command line options are specified in the AWS batch job definition. Using the job definition, the script is run when an analysis pipeline job is submitted to AWS batch.

#### submit_job.py ####

There are times when it's desirable to submit only one job from an analysis pipeline to AWS batch.  For example, users may want to submit the single job `ld_pruning` (from the `king` pipeline) to AWS batch.

The script `submit_job.py` enables users to submit a single job to AWS batch.  It is added to the docker images `topmed-master` and `topmed-devel` and stored in `/usr/local/bin`.

The basic steps to submit a single job are as follows:
1. `ssh` to the docker image on AWS
2. `cd` to your working directory under `/projects` root folder
3. Run `pipeline_docker` using the desired topmed docker image which places you in the docker image
4. Run the full pipeline with the `--print_only` option
5. Make note of the _analysis driver_ and it's _parameters_
6. Execute `submit_job.py` with the appropriate command line options to submit the job to AWS batch

Here's an example:
```
ssh -i ~/.ssh/xxx jd@52.21.215.116
cd /projects/topmed/analysts/jd/freeze6a/ld_pruning/
# the following places you in the docker image
pipeline_docker -i uwgac/topmed-master

# run the full king pipeline with the `print_only` option
/usr/local//analysis_pipeline/king.py --cluster_type AWS_Batch --verbose --cluster_file aws_batch_freeze6.json ld_pruning.config --print
# from the print output, the ld_pruning job has the following
# Analysis driver: /usr/local/analysis_pipeline/runRscript.sh
# Analysis driver parameters: -c /usr/local/analysis_pipeline/R/ld_pruning.R config/ld_pruned_ld_pruning.config --version 2.2.
# use the test option first (-T)
submit_job.py -c aws_batch_freeze6.json -p="-c /usr/local/analysis_pipeline/R/ld_pruning.R ld_pruning.config --version 2.2.0" --array 1-22 -N 8 -M 100000 -T
# execute the real deal
submit_job.py -c aws_batch_freeze6.json -p="-c /usr/local/analysis_pipeline/R/ld_pruning.R ld_pruning.config --version 2.2.0" --array 1-22 -N 8 -M 100000
```
