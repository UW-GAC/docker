## docker ##

This project builds various docker images associated with TOPMed.  By default the following docker images are built:
- ubuntu-16.04-hpc
- apps
- r-3.5.2-mkl
- topmed-master
- topmed-devel

The project includes the following files:
- a makefile for building the various docker images in the appropriate order (see below)
- docker build file associated with each image
- python files associated with commands running the TOPMed analysis pipeline
- although not in this repository, the MKL installation tar file must also be in the makefile directory (_see **special note** below_)

## building the docker images ##
Execute the makefile (`Makefile`) for building the docker images in the correct order (as described in the next section).  The makefile contains macros defining each image name, image tag, and docker build file.  Also the make file defines the dependencies of the docker images.

When a docker image is successfully built, an empty target file is created with the following name:
```{r}
<docker image name>.image
```
If the target file does not exist (or it has been created before the associated docker build file), the docker build file is executed.  Conversely, if the target file does exist and is newer than the associated docker build file, then the docker build file is not executed.

By default the docker build does not use the cache when building an image (i.e., `--no-cache` option).  If using the cache is desirable, then specify `cfg=cache` option to the makefile.  For example
```{r}
make cfg=cache
```
Additionally, the makefile's macros associated with the versions of software (e.g., ubuntu, R) and tags of the docker images can be changed via command line arguments.  For example:
```{r}
make OS_VERSION=18.04 DTAG=18.04 R_VERSION=3.5.3
```
The above command builds docker images based on ubuntu 18.04 and R 3.5.3; the tags of all images will be 18.04

#### (special note for building building the ubuntu hpc image) ####
Building the ubuntu hpc image requires Intel's Math Kernel Library (MKL) and the tar file must exist in the current build directory.  The default MKL being installed and built is `l_mkl_2018.1.163.tgz`

The version of MKL can be changed by executing the makefile with the `MKL_VERSION` macro.  For example,

```{r}
make MKL_VERSION=2018.1.163
```

## pushing the docker images to uwgac repository##
The makefile also provides the ability to push the docker images to the repository:
```{r}
make push
```

If a docker image has not been built (because the .image file does not exist or is newer than the docker build file), the docker image will be built before the push.

## docker build files ##
The docker build files are:
1. ubuntu-16.04-hpc.dfile - Builds a ubuntu-based image with hpc functionality.
2. ubuntu-18.04-hpc.dfile - Builds a ubuntu-based image with hpc functionality.
3. apps.dfile - From the ubuntu-based image, build an application image including the applications `samtools` and `locuszoom`.
4. r-mkl.dfile - Build an R image from the application image using both sequential and parallel MKL.
5. topmed-master.dfile - From the R image, build a TOPMed image using the master branch of the analysis pipeline.
6. topmed-devel.dfile - From the R image, build a TOPMed image using the devel branch of the analysis pipeline.

## docker image names and tags ##
The docker image names and tags are controlled by the makefile in conjunction with the docker build files.  The default names and tags are described in the following table:

| docker build file | default docker image | default docker tag | base image |
| --- | --- | --- | --- |
| ubuntu-16.04-hpc.dfile | ubuntu-16.04-hpc | latest | ubuntu:16.04 |
| ubuntu-18.04-hpc.dfile | ubuntu-18.04-hpc | latest | ubuntu:18.04
| apps.dfile | apps | latest | ubuntu-xx.04-hpc |
| r-mkl.dfile | r-3.5.2-mkl | latest | apps |
| topmed-master.dfile | tomped-master | latest | r-3.x.x-mkl |
| topmed-devel.dfile | topmed-devel | latest | r-3.x.x-mkl |

The default versions of software (e.g., `R 3.5.2`) is specified in both the makefile and the docker build files; but these versions can be changed either in the makefile or as options when executing the makefile.  For example, to build with R version 3.5.3:

```{r}
make R_VERSION=3.5.3
```
## python files ##
The python files are:
- ap2batch.py
- submit_job.py

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
