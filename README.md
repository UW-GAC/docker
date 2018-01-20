## docker ##

This project contains the docker build files for building the docker images supporting TOPMed.

It also contains two bash script files (`BuildDocker.bash` and `PushDocker.bash`):  (1) to build one or all of the images and (2) to push the built images to the `uwgac` dockerhub.

## building and pushing the docker images ##
Each docker image is built from an associated docker build file.  Because building a docker image is dependent upon another image, the docker images must be built in a specific order.  Additionally, when a docker image is built, its name and tag is specified.

The build order and naming of the TOPMed docker images is specified in the build bash script `BuildDocker.bash`.

The current approach for creating a docker image in the `uwgac` docker hub is to do the following:
1. Build the docker images on your local computer using the bash build script (`BuildDocker.bash`) on a local computer
2. Push these docker images from your local computer to dockerhub using the bash push script (`PushDocker.bash`) on this local computer

The bash build script `BuildDocker.bash` can either build all of the docker images supporting TOPMed (by not specifying any command line arguments) or can be used to build a single docker image like `r343-topmed`.  When building all of the images, the script builds them in the appropriate order (see section below).  To building a specific docker image, one or two arguments are passed in:
1. the docker image name (e.g., `r343-topmed`)
2. optionally, the docker tag (e.g., `genesis2`)

The second option is used for building `r343-topmed` image because we have multiple tags which are associated the analysis pipeline github branches.  This enables us to have access to the various versions of analysis pipeline.  When building `r343-topmed`, if the tag argument is not passed, then the `master` version of analysis pipeline is built.

(See `build details` section below for additional information)

Similarly, the bash push script `PushDocker.bash` is used to push TOPMed's docker images to the dockerhub.  The script can push either all of the images (assuming they exist on your local computer) or a single image.  It takes the same shell arguments as the build script.

## docker image names and tags ##
The docker image names are similar to the names of the associated docker build file; but they are not exactly the same.  The following table lists the names of the docker build files, default names of the docker images, and the default tags of the images.  The build order is also implied in the table.

| docker build file | default docker image | default docker tag |
| --- | --- | --- |
| Dockerfile.ubuntu-base | ubuntu-1604-base | latest |
| Dockerfile.ubuntu-hpc | ubuntu-1604-hpc | latest |
| Dockerfile.ubuntu-mkl | ubuntu-1604-mkl | latest |
| Dockerfile.r-mkl | r-mkl | 3.4.3 |
| Dockerfile.apps | apps-topmed | latest |
| Dockerfile.r-topmed.master | r343-topmed | master |
| Dockerfile.r-topmed.genesis2 | r343-topmed | genesis2 |
| Dockerfile.r-topmed.devel | r343-topmed | devel |

From the above table, the build order or dependency of the docker images are:

`ubuntu-1604-base:latest => ubuntu-1604-hpc:latest => ubuntu-1604-mkl:latest => r-mkl:3.4.3 => apps-topmed:latest => r343-topmed:master => { r343-topmed:devel, r343-topmed:genesis2 }`

In the above build order, `r343-topmed:master` is the basis for both `r343-topmed:devel` and `r343-topmed:genesis2`
## build details ##
1. Building a docker image is based on executing the docker `build` command and specifying the docker build file.  When executing the `build` command, an image name and tag is provided. For example,
```{r}
docker build -t uwgac/r-mkl:3.4.3 -f Dockerfile.r-mkl .
```
(see `BuildDocker.bash`)

2. The docker build files rely on using the `ARG` instruction to define the default image names, tags, and software versions in the build file.  For example,
```{r}
ARG iname=ubuntu-1604-mkl
ARG iversion=latest
FROM uwgac/$iname:$iversion
ARG rversion=3.4.3
```
3. The docker build command can alter these default names using the `--build-arg` option.  For example,
```{r}
docker build -t uwgac/r-mkl:3.4.4 --build-arg rversion=3.4.4 -f Dockerfile.r-mkl .
```
In the above example, the `r-mkl:3.4.4` image using R 3.4.4 (see `Dockerfile.r-mkl` for more details)

4. The docker image `ubuntu-1604-mkl` builds and installs Intel's Math Kernel Library (MKL).  In order to do this, the MKL tar file must be present in the same directory where the build is executing.  The current MKL tar file being built (and identified as an ARG in the build file) is `l_mkl_2017.3.196.tgz`
