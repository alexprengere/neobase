#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import pytz
import pytest


import neobase


def test_empty_base():
    N1 = neobase.NeoBase([])
    N2 = neobase.NeoBase(iter([]))
    N3 = neobase.NeoBase(open(os.devnull))
    for N in N1, N2, N3:
        assert len(N) == 0


def test_get(base):
    assert base.get('CDG', 'city_code_list') == ['PAR']


def test_distance(base):
    assert base.distance('ORY', 'CDG') - 34.8747 < 1e-3


def test_airport_priority_over_city(base):
    assert base.get('NCE', 'name') == "Nice Côte d'Azur International Airport"
    assert base.get('MAD', 'name') == "Adolfo Suárez Madrid–Barajas Airport"


def test_obsolete_por_are_not_loaded(base):
    assert base.get('KMG', 'name') == "Kunming Changshui International Airport"


def test_duplicates(base):
    assert base.get('NCE', '__dup__') == set(['NCE@1'])
    assert base.get('NCE@1', '__dup__') == set(['NCE'])


def test_benchmark_get(benchmark, base):
    benchmark(base.get, 'NCE')


def test_benchmark_get_name(benchmark, base):
    benchmark(base.get, 'NCE', 'name')


def test_timezones(base):
    tz_cache = set()
    unknown_tz = []

    for por in base:
        data = base.get(por)
        tz = data['timezone']
        if tz not in tz_cache:
            tz_cache.add(tz)
            try:
                pytz.timezone(tz)
            except pytz.exceptions.UnknownTimeZoneError:
                unknown_tz.append((por, tz))

    if unknown_tz:
        pytest.fail('Unknown timezone for {0}/{1} pors: {2}'.format(
                    len(unknown_tz), len(base),
                    ', '.join('{0} ({1})'.format(*t) for t in unknown_tz)))


def test_missing_geocodes(base):
    missing_geocodes = []

    for por in base:
        if base.get_location(por) is None:
            missing_geocodes.append(por)

    if missing_geocodes:
        pytest.fail('Missing geocodes for: {0}'.format(', '.join(missing_geocodes)))


def test_empty_geocodes(base):
    empty_geocodes = []

    for por in base:
        loc = base.get_location(por)
        if loc is not None:
            lat, lng = loc
            if lat == 0 or lng == 0:
                empty_geocodes.append(por)

    if empty_geocodes:
        pytest.fail('Empty lat/lng for: {0}'.format(', '.join(empty_geocodes)))


def test_duplicate_airports(base):
    for k in base:
        duplicates = set([k]) | base.get(k, '__dup__')
        if len([d for d in duplicates if 'A' in base.get(d, 'location_type')]) > 1:
            pytest.fail('Duplicated airport code: {0}'.format(k))


def test_old_data(past_base, base):
    assert 'CPQ' in past_base
    assert 'CPQ' not in base


class TestReferenceData(object):
    """
    IATA codes can be shared between an airport and the associated city, like NCE
    which represents both the airport and the city. In that case, we want the airport
    to have "priority" when getting metadata for the point of reference. That is
    what we test first here. This relies on the fact that airports are loaded first
    in the optd_por_public.csv file.

    Note that in recent version of NeoBase (0.15+), there are no longer shared IATA
    codes between airports since obsolete point of references are no longer loaded.
    This is the second test.
    """

    def test_airport_priority_over_city(self, base):
        assert base.get('NCE', 'name') == "Nice Côte d'Azur International Airport"
        assert base.get('MAD', 'name') == "Adolfo Suárez Madrid–Barajas Airport"

        # Checking top 10 page rank of duplicated airport/city with same IATA code
        assert base.get('ATL', 'name') == "Hartsfield-Jackson Atlanta International Airport"
        assert base.get('DXB', 'name') == "Dubai International Airport"
        assert base.get('LAX', 'name') == "Los Angeles International Airport"
        assert base.get('SYD', 'name') == "Sydney International Airport"
        assert base.get('IST', 'name') == "Istanbul Airport"
        assert base.get('SEA', 'name') == "Seattle-Tacoma International Airport"
        assert base.get('DFW', 'name') == "Dallas/Fort Worth International Airport"
        assert base.get('DEN', 'name') == "Denver International Airport"
        assert base.get('FRA', 'name') == "Frankfurt Airport"
        assert base.get('AMS', 'name') == "Amsterdam Airport Schiphol"

    def test_obsolete_por_are_not_loaded(self, base):
        assert base.get('KMG', 'name') == "Kunming Changshui International Airport"
        assert base.get('HFE', 'name') == "Hefei Xinqiao International Airport"
        assert base.get('NAT', 'name') == "Greater Natal International Airport"
        assert base.get('JIJ', 'name') == "Jijiga Wilwal International Airport"
        assert base.get('SWA', 'name') == "Jieyang Chaoshan Airport"

    def test_city_codes(self, base):
        assert base.get("TSF", "city_code_list")[0] == "VCE"
        assert base.get("SEA", "city_code_list")[0] == "SEA"
        assert base.get("PAE", "city_code_list")[0] == "SEA"
        assert base.get("SWF", "city_code_list")[0] == "NYC"
        assert base.get("EWR", "city_code_list")[0] == "NYC"
        assert base.get("FLL", "city_code_list")[0] == "FLL"
        assert base.get("BWI", "city_code_list")[0] == "WAS"
        assert base.get("ICN", "city_code_list")[0] == "SEL"
        assert base.get("CMN", "city_code_list")[0] == "CMN"
        assert base.get("WHA", "city_code_list")[0] == "WHU"
