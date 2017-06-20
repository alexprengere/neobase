#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
GeoBase. Rebooted.

    >>> b = NeoBase()
    >>> b.get('ORY', 'city_code_list')
    ['PAR']
    >>> b.get('ORY', 'city_name_list')
    ['Paris']
    >>> b.get('ORY', 'country_code')
    'FR'
    >>> b.distance('ORY', 'CDG')
    34.87...
    >>> b.get_location('ORY')
    LatLng(lat=48.72..., lng=2.35...)
"""

from __future__ import with_statement, print_function, division

from os import getenv
import os.path as op
import operator
from collections import namedtuple
from math import pi, cos, sin, asin, sqrt
import csv
import heapq

__all__ = ['NeoBase', 'LatLng']

_DIR = op.dirname(__file__)
_OPTD_POR_FILE = getenv('OPTD_POR_FILE', op.join(_DIR, 'optd_por_public.csv'))

_DEFAULT_RADIUS = 50

LatLng = namedtuple('LatLng', ['lat', 'lng'])

# Sentinel value for signatures
_sentinel = object()


class NeoBase(object):
    """Main structure, a wrapper around a dict, with dict-like behavior.
    """
    KEY = 0
    FIELDS = (
        ('iata_code', 0, None),
        ('name', 6, None),
        ('lat', 8, None),
        ('lng', 9, None),
        ('country_code', 16, None),
        ('continent_name', 19, None),
        ('timezone', 31, None),
        ('city_code_list', 36, lambda s: s.split(',')),
        ('city_name_list', 37, lambda s: s.split('=')),
        ('location_type', 41, list),
    )

    @staticmethod
    def skip(row):
        # This column is the date_until, meaning if this is not empty, the entry is now obsolete
        return bool(row[14])

    def __init__(self, rows=None):
        if rows is None:
            with open(_OPTD_POR_FILE) as f:
                self._data = self.load(f)
        else:
            self._data = self.load(rows)

    @staticmethod
    def _empty_value():
        return {'__dup__': set()}

    @classmethod
    def load(cls, f):
        """Building a dictionary of geographical data from optd_por.

        >>> path = op.join(_DIR, 'optd_por_public.csv')
        >>> with open(path) as f:
        ...     b = NeoBase.load(f)
        >>> b['ORY']['city_code_list']
        ['PAR']
        """
        fields, key_c, empty_value = cls.FIELDS, cls.KEY, cls._empty_value

        next(f)  # skipping first line
        data = {}

        for row in csv.reader(f, delimiter='^', quotechar='"'):
            # Comments and empty lines
            if not row or row[0].startswith('#'):
                continue

            if cls.skip(row):
                continue

            d = empty_value()
            for field, c, splitter in fields:
                if splitter is None:
                    d[field] = row[c]
                else:
                    d[field] = splitter(row[c])

            key = row[key_c]
            if key not in data:
                data[key] = d
            else:
                prev_d = data[key]
                new_key = '{0}@{1}'.format(key, 1 + len(prev_d['__dup__']))
                data[new_key] = d
                # Exchanging duplicata information
                d['__dup__'] = prev_d['__dup__'] | set([key])
                prev_d['__dup__'].add(new_key)

        return data

    def __iter__(self):
        """Returns iterator of all keys in the base.

        :returns: the iterator of all keys

        >>> b = NeoBase()
        >>> sorted(b)
        ['AAA', 'AAA@1', 'AAB', ...
        """
        return iter(self._data)

    def __contains__(self, key):
        """Test if a key is in the base.

        :param key: the key of to be tested
        :returns:   a boolean

        >>> b = NeoBase()
        >>> 'AN' in b
        False
        >>> 'AGN' in b
        True
        """
        return key in self._data

    def __nonzero__(self):
        """Testing structure emptiness.

        :returns: a boolean

        >>> b = NeoBase()
        >>> if b:
        ...     print('not empty')
        not empty
        """
        return bool(self._data)

    def __len__(self):
        """Testing structure size.

        :returns: a integer

        >>> b = NeoBase()
        >>> 18000 < len(b) < 20000
        True
        """
        return len(self._data)

    def keys(self):
        """Returns iterator of all keys in the base.

        :returns: the iterator of all keys

        >>> b = NeoBase()
        >>> sorted(b.keys())
        ['AAA', 'AAA@1', 'AAB', ...
        """
        return iter(self)

    def set(self, key, **data):
        """Set information.

        >>> b = NeoBase()
        >>> b.get('ORY', 'name')
        'Paris Orly Airport'
        >>> b.set('ORY', name='test')
        >>> b.get('ORY', 'name')
        'test'
        >>> b.set('Wow!', name='test')
        >>> b.get('Wow!', 'name')
        'test'
        """
        if key not in self:
            self._data[key] = self._empty_value()
        self._data[key].update(data)

    def get(self, key, field=None, default=_sentinel):
        """Get data from structure.

        >>> b = NeoBase()
        >>> b.get('OR', 'city_code_list', default=None)
        >>> b.get('ORY', 'city_code_list')
        ['PAR']
        """
        try:
            d = self._data[key]
        except KeyError:
            # Unless default is set, we raise an Exception
            if default is _sentinel:
                raise KeyError("Key not found: {0}".format(key))
            return default

        if field is None:
            return d  # we return the whole dictionary

        try:
            res = d[field]
        except KeyError:
            raise KeyError("Field '{0}' (for key '{1}') not in {2}".format(
                field, key, list(d)))
        else:
            return res

    def get_location(self, key, default=_sentinel):
        """Get None or the geocode.

        >>> b = NeoBase()
        >>> b.get_location('ORY')
        LatLng(lat=48.72..., lng=2.35...)
        """
        if key not in self:
            # Unless default is set, we raise an Exception
            if default is _sentinel:
                raise KeyError("Key not found: {0}".format(key))
            return default

        try:
            loc = LatLng(float(self.get(key, 'lat')),
                         float(self.get(key, 'lng')))

        except (ValueError, TypeError, KeyError):
            # Decode geocode, if error, returns None
            # TypeError : input type is not a string, probably None
            # ValueError: could not convert to float
            # KeyError  : could not find lat or lng 'fields'
            return None
        else:
            return loc

    @staticmethod
    def distance_between_locations(l0, l1):
        """Great circle distance

        :param l0: the LatLng tuple of the first location
        :param l1: the LatLng tuple of the second location
        :returns:  the distance in kilometers

        >>> NeoBase.distance_between_locations((48.84, 2.367), (43.70, 7.26)) # Paris -> Nice
        683.85...

        Case of unknown location.

        >>> NeoBase.distance_between_locations(None, (43.70, 7.26)) # returns None
        """
        if l0 is None or l1 is None:
            return None

        l0_lat = l0[0] / 180 * pi
        l0_lng = l0[1] / 180 * pi
        l1_lat = l1[0] / 180 * pi
        l1_lng = l1[1] / 180 * pi

        # Haversine formula (6371 is Earth radius)
        return 2 * 6371.0 * asin(sqrt(
            sin(0.5 * (l0_lat - l1_lat)) ** 2 +
            sin(0.5 * (l0_lng - l1_lng)) ** 2 *
            cos(l0_lat) * cos(l1_lat)
        ))

    def distance(self, key_0, key_1):
        """Compute distance between two elements.

        This is just a wrapper between the original haversine
        function, but it is probably the most used feature :)

        :param key_0: the first key
        :param key_1: the second key
        :returns:    the distance (km)

        >>> b = NeoBase()
        >>> b.distance('ORY', 'CDG')
        34.87...
        """
        return self.distance_between_locations(self.get_location(key_0),
                                               self.get_location(key_1))

    def _build_distances(self, lat_lng_ref, keys):
        """
        Compute the iterable of (dist, keys) of a reference
        lat_lng and a list of keys. Keys which have not valid
        geocodes will not appear in the results.

        >>> b = NeoBase()
        >>> list(b._build_distances((0,0), ['ORY', 'CDG']))
        [(5422.74..., 'ORY'), (5455.45..., 'CDG')]
        """
        if lat_lng_ref is None:
            return

        for key in keys:
            if key in self:
                lat_lng = self.get_location(key)
                if lat_lng is not None:
                    yield self.distance_between_locations(lat_lng_ref, lat_lng), key

    def find_near_location(self, lat_lng, radius=_DEFAULT_RADIUS, from_keys=None):
        """
        Returns a list of nearby keys from a location (given
        latidude and longitude), and a radius for the search.
        Note that the haversine function, which compute distance
        at the surface of a sphere, here returns kilometers,
        so the radius should be in kms.

        :param lat_lng: the lat_lng of the location
        :param radius:  the radius of the search (kilometers)
        :param from_keys: if None, it takes all keys in consideration, else takes from_keys \
            iterable of keys to perform search.
        :returns:       an iterable of keys (like ['ORY', 'CDG'])

        >>> b = NeoBase()
        >>> # Paris, airports <= 50km
        >>> [b.get(k, 'iata_code') for d, k in sorted(b.find_near_location((48.84, 2.367), 10))]
        ['PAR', 'XGB', 'XHP', 'XPG', 'XEX', 'XTT', 'QAF', 'JDP', 'XBT', 'QNL', 'QBH', 'QFC', 'QEV']
        """
        if from_keys is None:
            from_keys = iter(self)

        for dist, key in self._build_distances(lat_lng, from_keys):
            if dist <= radius:
                yield dist, key

    def find_near(self, key, radius=_DEFAULT_RADIUS, from_keys=None):
        """
        Same as find_near_location, except the location is given
        not by a lat/lng, but with its key, like ORY or SFO.
        We just look up in the base to retrieve lat/lng, and
        call find_near_location.

        :param key:     the key of the location
        :param radius:  the radius of the search (kilometers)
        :param from_keys: if None, it takes all keys in consideration, else takes from_keys \
            iterable of keys to perform search.
        :returns:       a list of keys (like ['ORY', 'CDG'])

        >>> b = NeoBase()
        >>> sorted(b.find_near('ORY', 10)) # Orly, por <= 10km
        [(0.0, 'ORY'), (6.94..., 'XJY'), (9.96..., 'QFC')]
        """
        if from_keys is None:
            from_keys = iter(self)

        if key not in self:
            return

        for dist, key in self.find_near_location(self.get_location(key),
                                                 radius=radius,
                                                 from_keys=from_keys):
            yield dist, key

    def find_closest_from_location(self, lat_lng, N=1, from_keys=None):
        """
        Concept close to find_near_location, but here we do not
        look for the keys radius-close to a location,
        we look for the closest key from this location, given by
        latitude/longitude.

        Note that a similar implementation is done in
        the LocalHelper, to find efficiently N closest location
        in a graph, from a location (using heaps).

        :param lat_lng:   the lat_lng of the location
        :param N:         the N closest results wanted
        :param from_keys: if None, it takes all keys in consideration, else takes from_keys \
            iterable of keys to perform find_closest_from_location. This is useful to combine \
            searches
        :returns:   one key (like 'SFO'), or a list if approximate is not None

        >>> b = NeoBase()
        >>> list(b.find_closest_from_location((43.70, 7.26))) # Nice
        [(0.60..., 'NCE@1')]
        >>> list(b.find_closest_from_location((43.70, 7.26), N=3)) # Nice
        [(0.60..., 'NCE@1'), (5.82..., 'NCE'), (5.89..., 'XBM')]
        """
        if from_keys is None:
            from_keys = iter(self)

        iterable = self._build_distances(lat_lng, from_keys)

        for dist, key in heapq.nsmallest(N, iterable):
            yield dist, key

    def find_with(self, conditions, from_keys=None, reverse=False):
        """Get iterator of all keys with particular field.

        For example, if you want to know all airports in Paris.

        :param conditions: a list of (field, value) conditions
        :param reverse:    we look keys where the field is *not* the particular value
        :returns:          an iterator of matching keys

        Testing several conditions.

        >>> b = NeoBase()
        >>> c0 = [('city_code_list', ['PAR'])]
        >>> c1 = [('location_type', ['H'])]
        >>> len(list(b.find_with(c0)))
        16
        >>> len(list(b.find_with(c1)))
        121
        >>> len(list(b.find_with(c0 + c1)))
        2
        """
        if from_keys is None:
            from_keys = iter(self)

        match = operator.ne if reverse else operator.eq

        for key in from_keys:
            if key in self:
                if all(match(self.get(key, f), v) for f, v in conditions):
                    yield key


def main():
    import argparse
    from pprint import pprint

    parser = argparse.ArgumentParser()
    parser.add_argument('keys', nargs='+', help="List of IATA codes")
    args = parser.parse_args()
    b = NeoBase()

    for key in args.keys:
        if key in b:
            pprint(b.get(key))
        else:
            print('{0} not in data.'.format(key))


if __name__ == '__main__':
    main()
