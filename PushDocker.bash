#!/bin/bash
INAMES="ubuntu-1604-base ubuntu-1604-hpc ubuntu-1604-mkl r-mkl apps-topmed r343-topmed  r343-topmed"
declare -a TAGS=("latest" "latest" "latest" "3.4.3" "latest" "master" "devel")

INDEX=0
if [ $# -eq 0 ]; then
   # build them all
   for f in $INAMES; do
      echo ">>> Pushing $f"
      cmd="docker push uwgac/$f:${TAGS[INDEX]}"
      echo $cmd
      $cmd
      let INDEX=INDEX+1
   done
else
   TF=$1
   for f in $INAMES; do
      if [ $f == $TF ]; then
         echo ">>> Pushing $f"
         cmd="docker push uwgac/$f:${TAGS[INDEX]}"
         echo $cmd
         $cmd
         exit 0
      fi
      let INDEX=INDEX+1
   done
fi
