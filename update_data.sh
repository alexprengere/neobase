#!/usr/bin/env sh

DIR=`dirname $0`
cd "$DIR/neobase"

rm -f optd_por_public.csv
wget 'https://raw.githubusercontent.com/opentraveldata/opentraveldata/master/opentraveldata/optd_por_public.csv'
