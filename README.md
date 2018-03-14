## docker ##

This project builds the docker images associated with TOPMed.  The project includes a docker build file associated with each image and a makefile for building the docker images by executing docker build files in a correct order (see below).

## building the docker images ##
Execute the makefile (`Makefile`) for building the docker images in the correct order (as described in the next section).  The makefile contains macros defining each image name, image tag, and docker build file.  Also the make file defines the dependencies of the docker images.

When a docker image is successfully built, an empty target file is created with the following name:
```{r}
<docker image name>.image
```
If the target file does not exist (or it has been created before the associated docker build file), the docker build file is executed.  Conversely, if the target file does exist and is newer than the associated docker build file, then the docker build file is not executed.

Additionally, the docker build option to build without using the cache can be specified when executing the makefile using the DB_FLAGS.  For example,
```{r}
make DB_FLAGS=--no-cache
```

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
1. ubuntu-hpc.dfile - Builds a ubuntu-based image with hpc functionality.
2. apps.dfile - From the ubuntu-based image, build an application image including the applications `samtools` and `locuszoom`.
3. r-mkl.dfile - Build an R image from the application image using both sequential and parallel MKL.
4. topmed-master.dfile - From the R image, build a TOPMed image using the master branch of the analysis pipeline.
5. topmed-devel.dfile - Build a TOPMed image of the devel branch of analysis pipeline from the TOPMed master image.

## docker image names and tags ##
The docker image names and tags are controlled by the makefile in conjunction with the docker build files.  The default names and tags are described in the following table:

| docker build file | default docker image | default docker tag |
| --- | --- | --- |
| ubuntu-hpc.dfile | ubuntu-16.04-hpc | latest |
| apps.dfile | apps | latest |
| r-mkl.dfile | r-3.4.3-mkl | latest |
| topmed-master.dfile | tomped-master | latest |
| topmed-devel.dfile | topmed-devel | latest |

The default versions of software (e.g., `R 3.4.3`) is specified in both the makefile and the docker build files; but these versions can be changed either in the makefile or as options when executing tthe makefile.  For example, to build with R version 3.5.0:

```{r}
make R_VERSION=3.5.0
```
(Note: this functionality has not been fully tested.)
