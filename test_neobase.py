#!/usr/bin/python
# -*- coding: utf-8 -*-


def test_get(base):
    assert base.get('CDG', 'city_code_list') == ['PAR']


def test_distance(base):
    assert base.distance('ORY', 'CDG') - 34.8747 < 1e-3


def test_duplicates(base):
    assert base.get('NCE', '__dup__') == set(['NCE@1'])
    assert base.get('NCE@1', '__dup__') == set(['NCE'])


def test_benchmark_get(benchmark, base):
    benchmark(base.get, 'NCE')

def test_benchmark_get_name(benchmark, base):
    benchmark(base.get, 'NCE', 'name')
