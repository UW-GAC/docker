#!/bin/bash
DFILES="Dockerfile.ubuntu-base Dockerfile.ubuntu-hpc Dockerfile.ubuntu-mkl Dockerfile.r-mkl Dockerfile.apps Dockerfile.r-topmed.master Dockerfile.r-topmed.devel"
declare -a INAMES=("ubuntu-1604-base" "ubuntu-1604-hpc" "ubuntu-1604-mkl" "r-mkl" "apps-topmed" "r343-topmed" "r343-topmed");
declare -a TAGS=("latest" "latest" "latest" "3.4.3" "latest" "master" "devel")

INDEX=0
if [ $# -eq 0 ]; then
   # build them all
   for f in $DFILES; do
      echo ">>> Building $f"
      cmd="docker build -t uwgac/${INAMES[INDEX]}:${TAGS[INDEX]} -f $f ."
      echo $cmd
      $cmd
      let INDEX=INDEX+1
   done
else
   TF=$1
   for f in $DFILES; do
      if [ $f == $TF ]; then
         echo ">>> Building $f"
         cmd="docker build -t uwgac/${INAMES[INDEX]}:${TAGS[INDEX]} -f $f ."
         echo $cmd
         $cmd
         exit 0
      fi
      let INDEX=INDEX+1
   done
fi
