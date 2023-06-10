#!/bin/bash
export LC_NUMERIC="en_US.UTF-8"

CURR=`pwd`
INPUTDIR=$CURR/models

max_sol=$1
solver=$2
timeout=$3

for j in `ls $INPUTDIR | grep "\.bnet"`
do
	echo "Run $j"
	start=$(date +%s.%N)
	second="s"
	timeout_str="$timeout$second"
	timeout $timeout_str python teststableconf.py $INPUTDIR/$j $max_sol $solver;killall -9 java;killall -9 python
	dur=$(echo "$(date +%s.%N) - $start" | bc)
	echo "Finish $j"
	echo "==============================================="
done
