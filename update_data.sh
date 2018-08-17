#!/usr/bin/env sh

rm -f optd_por_public.csv
wget 'https://raw.githubusercontent.com/opentraveldata/opentraveldata/master/opentraveldata/optd_por_public.csv' -O - |grep -v '^ZZZ\^' > neobase/optd_por_public.csv
