#!/usr/bin/python
# -*- coding: utf-8 -*-

import pytz
import pytest


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


def test_geocodes(base):
    missing_geocodes = []

    for por in base:
        if base.get_location(por) is None:
            missing_geocodes.append(por)

    if missing_geocodes:
        pytest.fail('Missing geocodes for: {0}'.format(', '.join(missing_geocodes)))
