#!/usr/bin/python
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

from importlib.resources import files
from os import getenv
import operator
from datetime import datetime
from math import pi, cos, sin, asin, sqrt, fsum
from itertools import starmap, pairwise
from typing import NamedTuple, TypeAlias, Any, cast
import csv
import heapq
from collections.abc import Callable, Iterable, Iterator, Sequence

from functools import partial

open_ = partial(open, encoding="utf-8")


__all__ = ["OPTD_POR_URL", "LatLng", "NeoBase", "UnknownKeyError"]

OPTD_POR_URL = (
    "https://raw.githubusercontent.com/opentraveldata/opentraveldata/"
    "master/opentraveldata/optd_por_public.csv"
)

_DEF_OPTD_POR_FILE = "optd_por_public.csv"
_DEFAULT_RADIUS = 50

FieldValue: TypeAlias = Any
PointData: TypeAlias = dict[str, FieldValue]
Splitter: TypeAlias = Callable[[str], FieldValue]
DistanceResult: TypeAlias = tuple[float, str]
LatLngTuple: TypeAlias = tuple[float, float]


class LatLng(NamedTuple):
    lat: float
    lng: float


class UnknownKeyError(KeyError):
    pass


# Sentinel value for signatures
_sentinel = object()


class NeoBase:
    """Main structure, a wrapper around a dict, with dict-like behavior."""

    KEY = 0  # iata_code
    FIELDS: Sequence[tuple[str, int, Splitter | None]] = (
        ("iata_code", 0, None),
        ("name", 6, None),
        ("lat", 8, None),
        ("lng", 9, None),
        ("page_rank", 12, lambda s: float(s) if s else None),
        ("country_code", 16, None),
        ("country_name", 18, None),
        ("continent_name", 19, None),
        ("timezone", 31, None),
        ("city_code_list", 36, lambda s: s.split(",")),
        ("city_name_list", 37, lambda s: s.split("=")),
        ("location_type", 41, list),
        ("currency", 46, None),
    )

    # Duplicates behavior, by default we keep everything
    DUPLICATES = getenv("OPTD_POR_DUPLICATES", "1") == "1"

    @staticmethod
    def skip(row: Sequence[str], date: str) -> bool:
        date_from, date_until = row[13], row[14]
        if date_from and date < date_from:
            return True
        if date_until and date > date_until:
            return True
        return False

    def __init__(
        self,
        rows: Iterable[str] | None = None,
        date: str | None = None,
        duplicates: bool | None = None,
    ) -> None:
        if date is None:
            date = getenv("OPTD_POR_DATE", datetime.today().strftime("%Y-%m-%d"))

        if duplicates is None:
            duplicates = self.DUPLICATES

        if rows is None:
            filename = getenv("OPTD_POR_FILE")
            if filename is None:
                f = files("neobase").joinpath(_DEF_OPTD_POR_FILE).open(encoding="utf-8")
            else:
                f = open_(filename)
            self._data = self.load(f, date, duplicates)
            f.close()
        else:
            self._data = self.load(rows, date, duplicates)

    @staticmethod
    def _empty_value() -> PointData:
        return {"__dup__": set()}

    @classmethod
    def load(
        cls,
        f: Iterable[str],
        date: str,
        duplicates: bool,
    ) -> dict[str, PointData]:
        """Building a dictionary of geographical data from optd_por.

        >>> import os.path as op
        >>> path = op.join(op.dirname(__file__), 'optd_por_public.csv')
        >>> with open_(path) as f:
        ...     b = NeoBase.load(f, '2030-01-01', True)
        >>> b['ORY']['city_code_list']
        ['PAR']
        """
        f = iter(f)  # convert lists to iterators

        fields, key_c, skip = cls.FIELDS, cls.KEY, cls.skip
        empty_value = cls._empty_value

        data: dict[str, PointData] = {}
        try:
            next(f)  # skipping first line
        except StopIteration:
            pass

        for line in f:
            # Comments and empty lines
            if not line or line.startswith("#"):
                continue

            if '"' in line:
                row = next(csv.reader([line], delimiter="^", quotechar='"'))
            else:
                row = line.rstrip("\r\n").split("^")

            if skip(row, date):
                continue

            key = row[key_c]
            if not key:
                continue

            if key in data and not duplicates:
                continue

            d = empty_value()
            for field, c, splitter in fields:
                if splitter is None:
                    d[field] = row[c]
                else:
                    d[field] = splitter(row[c])

            if key not in data:
                data[key] = d
            else:
                prev_d = data[key]
                prev_d_dup = cast("set[str]", prev_d["__dup__"])
                new_key = f"{key}@{1 + len(prev_d_dup)}"
                data[new_key] = d
                # Exchanging duplicata information
                d["__dup__"] = prev_d_dup | {key}
                prev_d_dup.add(new_key)

        return data

    def __iter__(self) -> Iterator[str]:
        """Returns iterator of all keys in the base.

        :returns: the iterator of all keys

        >>> b = NeoBase()
        >>> sorted(b)
        ['AAA', 'AAA@1', 'AAB', ...
        """
        return iter(self._data)

    def __contains__(self, key: str | None) -> bool:
        """Test if a key is in the base.

        :param key: the key of to be tested
        :returns:   a boolean

        >>> b = NeoBase()
        >>> 'AN' in b
        False
        >>> 'AGN' in b
        True
        >>> 'agn' in b
        True
        >>> None in b
        False
        """
        if key is not None:
            key = key.upper()
        return key in self._data

    def __bool__(self) -> bool:
        """Testing structure emptiness.

        :returns: a boolean

        >>> b = NeoBase()
        >>> if b:
        ...     print('not empty')
        not empty
        """
        return bool(self._data)

    def __len__(self) -> int:
        """Testing structure size.

        :returns: a integer

        >>> b = NeoBase()
        >>> 18000 < len(b) < 21000
        True
        """
        return len(self._data)

    def keys(self) -> Iterator[str]:
        """Returns iterator of all keys in the base.

        :returns: the iterator of all keys

        >>> b = NeoBase()
        >>> sorted(b.keys())
        ['AAA', 'AAA@1', 'AAB', ...
        """
        return iter(self)

    def set(self, key: str | None, **data: FieldValue) -> None:
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
        if key is None:
            return
        key = key.upper()
        if key not in self:
            self._data[key] = self._empty_value()
        self._data[key].update(data)

    def get(
        self,
        key: str | None,
        field: str | None = None,
        default: object = _sentinel,
    ) -> Any:
        """Get data from structure.

        >>> b = NeoBase()
        >>> b.get('OR', 'city_code_list', default=None)
        >>> b.get('ORY', 'city_code_list')
        ['PAR']
        >>> b.get('nce', 'city_code_list')
        ['NCE']
        """
        if key is not None:
            key = key.upper()

        d = self._data.get(key)
        if d is None:
            # Unless default is set, we raise an Exception
            if default is _sentinel:
                raise UnknownKeyError(f"Key not found: {key}")
            return default

        if field is None:
            return d  # we return the whole dictionary

        try:
            res = d[field]
        except KeyError as e:
            raise KeyError(f"Field '{field}' (for key '{key}') not in {list(d)}") from e
        else:
            return res

    def get_location(
        self,
        key: str | None,
        lat_field: str = "lat",
        lng_field: str = "lng",
        default: object = _sentinel,
    ) -> LatLng | None:
        """Get None or the geocode.

        >>> b = NeoBase()
        >>> b.get_location('ORY')
        LatLng(lat=48.72..., lng=2.35...)
        """
        if key is not None:
            key = key.upper()

        d = self._data.get(key)
        if d is None:
            # Unless default is set, we raise an Exception
            if default is _sentinel:
                raise UnknownKeyError(f"Key not found: {key}")
            return cast("LatLng | None", default)

        try:
            loc = LatLng(
                float(cast("str", d[lat_field])),
                float(cast("str", d[lng_field])),
            )

        except (ValueError, TypeError, KeyError):
            # Decode geocode, if error, returns None
            # TypeError : input type is not a string, probably None
            # ValueError: could not convert to float
            # KeyError  : could not find lat or lng 'fields'
            return None
        else:
            return loc

    @staticmethod
    def distance_between_locations(
        l0: LatLngTuple | None,
        l1: LatLngTuple | None,
    ) -> float | None:
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
        return (
            2
            * 6371.0
            * asin(
                sqrt(
                    sin(0.5 * (l0_lat - l1_lat)) ** 2
                    + sin(0.5 * (l0_lng - l1_lng)) ** 2 * cos(l0_lat) * cos(l1_lat)
                )
            )
        )

    def distance(
        self,
        *keys: str | None,
        default: object = _sentinel,
    ) -> float | None:
        """Compute distance between two elements.

        This is just a wrapper between the original haversine
        function, but it is probably the most used feature :)

        :param keys: the keys
        :returns:    the distance (km)

        >>> b = NeoBase()
        >>> b.distance('ORY', 'CDG')
        34.87...
        >>> b.distance('ORY', 'NCE', 'CDG')
        1370.34...
        """
        try:
            locations = [self.get_location(k) for k in keys]
        except KeyError:
            if default is _sentinel:
                raise
            return cast("float | None", default)
        else:
            return fsum(starmap(self.distance_between_locations, pairwise(locations)))  # type: ignore

    def _build_distances(
        self,
        lat_lng_ref: LatLngTuple | None,
        keys: Iterable[str | None],
    ) -> Iterator[DistanceResult]:
        """
        Compute the iterable of (dist, keys) of a reference
        lat_lng and a list of keys. Keys which have not valid
        geocodes will not appear in the results.

        >>> b = NeoBase()
        >>> list(b._build_distances((0, 0), ['ORY', 'CDG']))
        [(5422.74..., 'ORY'), (5455.45..., 'CDG')]
        """
        if lat_lng_ref is None:
            return

        data_get = self._data.get
        distance_between_locations = self.distance_between_locations
        for key in keys:
            if key is None:
                continue
            d = data_get(key.upper())

            if d is None:
                continue
            try:
                lat_lng = (
                    float(cast("str", d["lat"])),
                    float(cast("str", d["lng"])),
                )
            except (ValueError, TypeError, KeyError):
                continue

            dist = distance_between_locations(lat_lng_ref, lat_lng)
            if dist is not None:
                yield dist, key

    def find_near_location(
        self,
        lat_lng: LatLngTuple | None,
        radius: float = _DEFAULT_RADIUS,
        from_keys: Iterable[str | None] | None = None,
    ) -> Iterator[DistanceResult]:
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
        :returns:       an iterable of (dist, key)

        >>> b = NeoBase()
        >>> # Paris, airports <= 50km
        >>> [b.get(k, 'iata_code') for d, k in sorted(b.find_near_location((48.84, 2.367), 5))]
        ['LYY', 'PAR', 'XGB', 'MPE', 'XHP', 'XPG', 'XEX']
        """
        if from_keys is None:
            from_keys = iter(self)

        for dist, key in self._build_distances(lat_lng, from_keys):
            if dist <= radius:
                yield dist, key

    def find_near(
        self,
        key: str | None,
        radius: float = _DEFAULT_RADIUS,
        from_keys: Iterable[str | None] | None = None,
    ) -> Iterator[DistanceResult]:
        """
        Same as find_near_location, except the location is given
        not by a lat/lng, but with its key, like ORY or SFO.
        We just look up in the base to retrieve lat/lng, and
        call find_near_location.

        :param key:     the key of the location
        :param radius:  the radius of the search (kilometers)
        :param from_keys: if None, it takes all keys in consideration, else takes from_keys \
            iterable of keys to perform search.
        :returns:       an iterable of (dist, key)

        >>> b = NeoBase()
        >>> sorted(b.find_near('ORY', 10)) # Orly, por <= 10km
        [(0.0, 'ORY'), (6.94..., 'XJY'), (9.96..., 'QFC')]
        """
        if from_keys is None:
            from_keys = iter(self)

        if key not in self:
            return

        yield from self.find_near_location(
            self.get_location(key),
            radius=radius,
            from_keys=from_keys,
        )

    def find_closest_from_location(
        self,
        lat_lng: LatLngTuple | None,
        N: int = 1,
        from_keys: Iterable[str | None] | None = None,
    ) -> Iterator[DistanceResult]:
        """
        Concept close to find_near_location, but here we do not
        look for the keys radius-close to a location,
        we look for the closest key from this location, given by
        latitude/longitude.

        :param lat_lng:   the lat_lng of the location
        :param N:         the N closest results wanted
        :param from_keys: if None, it takes all keys in consideration, else takes from_keys \
            iterable of keys to perform find_closest_from_location. This is useful to combine \
            searches
        :returns:       an iterable of (dist, key)

        >>> b = NeoBase()
        >>> list(b.find_closest_from_location((43.70, 7.26))) # Nice
        [(0.60..., 'NCE@1')]
        >>> list(b.find_closest_from_location((43.70, 7.26), N=3)) # Nice
        [(0.60..., 'NCE@1'), (5.82..., 'NCE'), (5.89..., 'XBM')]
        """
        if from_keys is None:
            from_keys = iter(self)

        iterable = self._build_distances(lat_lng, from_keys)

        yield from heapq.nsmallest(N, iterable)

    def find_closest_from(
        self,
        key: str | None,
        N: int = 1,
        from_keys: Iterable[str | None] | None = None,
    ) -> Iterator[DistanceResult]:
        """
        Same as find_closest_from_location, except the location is given
        not by a lat/lng, but with its key, like ORY or SFO.
        We just look up in the base to retrieve lat/lng, and
        call find_closest_from_location.

        :param key:       the key of the location
        :param N:         the N closest results wanted
        :param from_keys: if None, it takes all keys in consideration, else takes from_keys \
            iterable of keys to perform find_closest_from_location. This is useful to combine \
            searches
        :returns:       an iterable of (dist, key)

        >>> b = NeoBase()
        >>> list(b.find_closest_from('NCE'))
        [(0.0, 'NCE')]
        >>> list(b.find_closest_from('NCE', N=3))
        [(0.0, 'NCE'), (5.07..., 'XCG@1'), (5.45..., 'XCG')]
        """
        if from_keys is None:
            from_keys = iter(self)

        if key not in self:
            return

        yield from self.find_closest_from_location(
            self.get_location(key),
            N=N,
            from_keys=from_keys,
        )

    def find_with(
        self,
        conditions: Iterable[tuple[str, FieldValue]],
        from_keys: Iterable[str | None] | None = None,
        reverse: bool = False,
    ) -> Iterator[str | None]:
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
        17
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
