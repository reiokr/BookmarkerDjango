#!/bin/bash

cd /home/rk/projektid/BookmarkerDjango || exit
parallel -u ::: './run1.sh 1' './run2.sh 2'
