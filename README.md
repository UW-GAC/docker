## docker ##

This project contains some docker build files using the docker command (where your current working directory contains these files):

    docker build -t uwgac/<repository>:tag -f <docker file> .

where `repository` is the name of the repository; `tag`is the version; and `docker file`is the name of the docker build file. 

The naming convention of the docker build file is as follows:

    Dockerfile.<repository>.<version>
or

    Dockerfile.<repository>.<update>

The `repository` is the target repository as specified in the docker build command.  

The `version` is the version number of the build file and may also reflect target repository's version number. The first version (which is not always 1) in a target repository is built from an external repository.  Subsequent builds may either be based on a change to a previous version in the target repository or a new configuration from the original external repository. 

The `update` is a rebuild of an existing target repository.  This is typically done when an existing package or component of a target repository has been updated.  For example, when an R package has been updated, then the corresponding target repository is updated by reinstalling the R package. 

Remember that it's the docker build command that specifies the target repository and version associated with the build.  The build files specifies the source repository (and version) to build from. 
