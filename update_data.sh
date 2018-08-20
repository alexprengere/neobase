#!/usr/bin/env sh

wget 'https://raw.githubusercontent.com/opentraveldata/opentraveldata/master/opentraveldata/optd_por_public.csv' -O tmp.csv

(head -n 1 tmp.csv && tail -n +2 tmp.csv |grep -v '^\^' |sort -t'^' -k1,1 -k42,42 -k5n,5) > neobase/optd_por_public.csv
rm -f tmp.csv
