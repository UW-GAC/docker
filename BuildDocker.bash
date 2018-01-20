#!/bin/bash
declare -a DFILES=("Dockerfile.ubuntu-base" "Dockerfile.ubuntu-hpc" "Dockerfile.ubuntu-mkl"  "Dockerfile.r-mkl" "Dockerfile.apps" "Dockerfile.r-topmed.master" "Dockerfile.r-topmed.devel"  "Dockerfile.r-topmed.roybranch" "Dockerfile.r-topmed.genesis2")
declare -a INAMES=("ubuntu-1604-base" "ubuntu-1604-hpc" "ubuntu-1604-mkl" "r-mkl" "apps-topmed" "r343-topmed" "r343-topmed" "r343-topmed" "r343-topmed")
declare -a TAGS=("latest" "latest" "latest" "3.4.3" "latest" "master" "devel" "roybranch" "genesis2")

INDEX=0
if [ $# -eq 0 ]; then
    # build them all
    for f in ${DFILES[@]}; do
        echo ">>> Building $f"
        cmd="docker build --no-cache -t uwgac/${INAMES[INDEX]}:${TAGS[INDEX]} -f $f ."
        echo $cmd
        $cmd
        let INDEX=INDEX+1
    done
else
    IN=$1
    for i in ${INAMES[@]}; do
    if [ $i == $IN ]; then
        R343=r343-topmed
        if [ $i == $R343 ]; then
            if [ $# -eq 2 ]; then
              TAG=$2
            else
              TAG=devel
            fi
        else
            TAG=${TAGS[INDEX]}
        fi
        TINDEX=0
        FINDEX=0
        for tt in ${TAGS[@]}; do
            if [ $tt == $TAG ]; then
                FINDEX=$TINDEX
            fi
            let TINDEX=TINDEX+1
        done
        f="${DFILES[FINDEX]}"
        echo ">>> Building $f"
        cmd="docker build --no-cache -t uwgac/$i:$TAG -f $f ."
        echo $cmd
         $cmd
        exit 0
    fi
      let INDEX=INDEX+1
    done
fi
