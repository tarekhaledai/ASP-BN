#!/bin/bash
export LC_NUMERIC="en_US.UTF-8"

CURR=`pwd`
INPUTDIR=$CURR/models
OUTDIR=$CURR/results

rm -f $OUTDIR/*
for j in `ls $INPUTDIR`
do
	echo "Run $j"
	timeout 600s python3 trappist.py -c fix -m 0 -t 120 -s asp $INPUTDIR/$j > $OUTDIR/$j.txt
	echo "Finish $j"
done
