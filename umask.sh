#!/bin/bash
umask 0002
if [ "$#" -eq 0 ]; then
    /bin/bash
else
   "$@"
fi
