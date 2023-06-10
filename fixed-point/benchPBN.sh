#!/bin/bash
export LC_NUMERIC="en_US.UTF-8"

CURR=`pwd`
INPUTDIR=$CURR/models

max_sol=$1
timeout=$2

for j in `ls $INPUTDIR | grep "\.bnet"`
do
	echo "Run $j"
	start=$(date +%s.%N)
	second="s"
	timeout_str="$timeout$second"
	timeout $timeout_str python testPBN.py $INPUTDIR/$j $timeout $max_sol;killall -9 java;killall -9 python;killall -9 BNetToPrime_linux64
	dur=$(echo "$(date +%s.%N) - $start" | bc)
	echo "Finish $j"
	echo "==============================================="
done
