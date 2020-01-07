## docker ##

This project builds various docker images associated with TOPMed.  There are two types of docker images: (1) core images and (2) TOPMed images.  All of the TOPMed images are built upon the core  images.  

The core docker images are:
- `ubuntu-18.04-hpc` - ubuntu 18.04; python2; python3; hdf5; mpich; openmpi; Intel's MKL
- `apps` - samtools; locuszoom; awscli; boto3; unzip; king built from `ubuntu-18.04-hpc`
- `r-3.6.1-mkl` - R 3.6.1 built from `apps` using the MKL

The TOPMed images are associated with the TOPMed analysis pipeline.  The analysis pipeline includes python and R code. It has two major branches in its git hub repository: master and devel. The TOPMed docker images are built based on the branches of the git hub repository for the analysis pipeline.  The TOPMed docker images are:
- `tm-rpkgs-master` - TOPMed R packages compatible with the master branch of the analysis pipeline and built from the `r-3.6.1-mkl` image
- `tm-rpkgs-devel` - TOPMed R packages compatible with the devel branch of the analysis pipeline and built from the `r-3.6.1-mkl` image
- `topmed-master` - Master branch of the analysis pipeline built from the `tm-rpkgs-master` image
- `topmed-devel`  - Devel branch of the analysis pipeline based built from the `tm-rpkgs-devel` image
- `topmed-python3` - Python3 branch of the analysis pipeline based built from the `topmed-devel` image

The project includes the following files:
- a makefile for building the docker images (see below)
- docker build files associated with building the docker images
- python files added to the `topmed-devel` image and the `topmed-master` image
- although not in this repository, the MKL installation tar file must also be in the makefile directory (_see **special note** below_)
## building the docker images ##
Execute the makefile (`Makefile`) for building the core and TOPMed docker images.  By default, the master branch topmed images are built (the core docker images are independent of the git branch of the analysis pipeline).  The makefile contains macros defining the git branch, each image name, image tag, and docker build file.  Also the makefile defines the dependencies of the docker images.

When a docker image is successfully built using an associated docker build file, an empty target file is created with the following name:
```{r}
<docker image name>.image
```
If the target file does not exist (or it has been created before the associated docker build file), the makefile will execute the docker build command using the docker build file.  Conversely, if the target file does exist and is newer than the associated docker build file, the the makefile will not execute the docker build command.

There are numerous macros used by the makefile.  All macros can be defined to new values when executing the makefile; however, the most common macros include the following:
1. GTAG - the git branch of the analysis pipeline [Default: `master`]
2. R_VERSION - the version of R to build [Default: 3.6.1]
3. USECACHE - if defined, used docker's cache when building [Default: not defined]
4. MKL_VERSION - the version of the MKL tar gz file [Default: `l_mkl_2018.1.163.tgz`]
4. DTAG - Docker tag for the docker images [Default: 2.6]
_(Note: If the docker tag, `DTAG` is not defined as `latest`, then the docker tag `latest` will also be created for each image)_
#### examples of execute the makefile ####
1. No command execution
```{r}
make -n
```
Run make with the _-n_ option, outputs the various commands without executing them.

2. Build the docker images
```{r}
make
```
Run make and when appropriate execute commands to build the docker core images; and the TOPMed images using the master branch of the analysis pipeline.

By default all docker images will have two tags: `latest` and `2.6`

3. Build the devel docker images
```{r}
make GTAG=devel
```
Run make and when appropriate execute commands to build the docker core images; and the TOPMed images using the devel branch of the analysis pipeline.

By default all docker images will have two tags: `latest` and `2.6`

## docker build files ##
The docker build files are:
1. ubuntu-18.04-hpc.dfile - Builds a ubuntu-based image with hpc functionality.
2. apps.dfile - From the ubuntu-based image, build an application image including the applications `samtools` and `locuszoom`.
3. r-mkl.dfile - Build an R image from the application image using both sequential and parallel MKL.
4. tm-rpkgs.dfile - Based on the value of GTAG, builds the TOPMed R packages associated with analysis pipeline
5. topmed.dfile - Based on the value of GTAG, builds a TOPMed image

## docker image names and tags ##
The docker image names and tags are controlled by the makefile in conjunction with the docker build files.  The default names and tags are described in the following table:

| docker build file | GTAG |default docker image | default docker tags | base image |
| --- | --- | --- | --- |--- |
| ubuntu-18.04-hpc.dfile | n/a | ubuntu-18.04-hpc | latest; 2.6 | ubuntu:18.04
| apps.dfile | n/a | apps | latest; 2.6 | ubuntu-18.04-hpc |
| r-mkl.dfile | n/a | r-3.6.1-mkl | latest | apps |
| tm-rpkgs.dfile | master | tm-rpkgs-master | latest | r-3.6.1-mkl |
| topmed-master.dfile | master | tomped-master | latest | tm-rpkgs-master |

The default versions of software (e.g., `R 3.6.1`) is specified in both the makefile and the docker build files; but these versions can be changed either in the makefile or as options when executing the makefile.  For example, to build with R version 3.6.3:

```{r}
make R_VERSION=3.6.3
```
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
ssh -i ~/.ssh/xxx kuraisa@52.21.215.116
cd /projects/topmed/analysts/kuraisa/freeze6a/ld_pruning/
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
