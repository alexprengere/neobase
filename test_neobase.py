#!/usr/bin/python

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
    assert base.get("CDG", "city_code_list") == ["PAR"]


def test_get_on_unknown(base):
    assert base.get("___", "city_code_list", default=[1]) == [1]
    with pytest.raises(KeyError):
        base.get("___", "city_code_list")
    with pytest.raises(neobase.UnknownKeyError):
        base.get("___", "city_code_list")


def test_get_location(base):
    loc = base.get_location("CDG")
    assert loc.lat == pytest.approx(49.01278)
    assert loc.lng == pytest.approx(2.55)


def test_get_location_on_unknown(base):
    assert base.get_location("___", default=(0, 0)) == (0, 0)
    with pytest.raises(KeyError):
        base.get_location("___")


def test_distance(base):
    assert base.distance("ORY", "CDG") == pytest.approx(34.874805)
    assert base.distance("ORY", "CDG", "NCE") == pytest.approx(729.391132)


def test_distance_on_unknown(base):
    assert base.distance("___", "CDG", default=-1) == -1
    assert base.distance("CDG", "___", default=-1) == -1
    assert base.distance("___", "___", default=-1) == -1
    with pytest.raises(KeyError):
        base.distance("CDG", "___")
    with pytest.raises(KeyError):
        base.distance("___", "CDG")
    with pytest.raises(KeyError):
        base.distance("___", "___")


def test_airport_priority_over_city(base):
    assert base.get("NCE", "name") == "Nice Côte d'Azur International Airport"
    assert base.get("MAD", "name") == "Adolfo Suárez Madrid–Barajas Airport"


def test_obsolete_por_are_not_loaded(base):
    assert base.get("KMG", "name") == "Kunming Changshui International Airport"


def test_duplicates(base):
    assert base.get("NCE", "__dup__") == {"NCE@1"}
    assert base.get("NCE@1", "__dup__") == {"NCE"}


def test_benchmark_get(benchmark, base):
    benchmark(base.get, "NCE")


def test_benchmark_get_name(benchmark, base):
    benchmark(base.get, "NCE", "name")


def test_missing_city_info(base):
    missing_city_codes = []
    missing_city_names = []

    for por in base:
        if not base.get(por, "city_code_list"):
            missing_city_codes.append(por)
        if not base.get(por, "city_name_list"):
            missing_city_names.append(por)

    if missing_city_codes:
        pytest.fail("Missing city codes for: {}".format(", ".join(missing_city_codes)))
    if missing_city_names:
        pytest.fail("Missing city names for: {}".format(", ".join(missing_city_names)))


def test_timezones(base):
    tz_cache = set()
    unknown_tz = []

    for por in base:
        data = base.get(por)
        tz = data["timezone"]
        if tz not in tz_cache:
            tz_cache.add(tz)
            try:
                pytz.timezone(tz)
            except pytz.exceptions.UnknownTimeZoneError:
                unknown_tz.append((por, tz))

    if unknown_tz:
        pytest.fail(
            "Unknown timezone for {}/{} pors: {}".format(
                len(unknown_tz),
                len(base),
                ", ".join("{} ({})".format(*t) for t in unknown_tz),
            )
        )


def test_missing_timezones(base):
    missing_timezones = []

    for por in base:
        if not base.get(por, "timezone"):
            missing_timezones.append(por)

    if missing_timezones:
        pytest.fail("Missing timezones for: {}".format(", ".join(missing_timezones)))


def test_missing_geocodes(base):
    missing_geocodes = []

    for por in base:
        if base.get_location(por) is None:
            missing_geocodes.append(por)

    if missing_geocodes:
        pytest.fail("Missing geocodes for: {}".format(", ".join(missing_geocodes)))


def test_empty_geocodes(base):
    empty_geocodes = []

    for por in base:
        loc = base.get_location(por)
        if loc is not None:
            lat, lng = loc
            if lat == 0 or lng == 0:
                empty_geocodes.append(por)

    if empty_geocodes:
        pytest.fail("Empty lat/lng for: {}".format(", ".join(empty_geocodes)))


def test_duplicate_airports(base):
    for k in base:
        duplicates = {k} | base.get(k, "__dup__")
        if len([d for d in duplicates if "A" in base.get(d, "location_type")]) > 1:
            pytest.fail(f"Duplicated airport code: {k}")


def test_old_data(past_base, base):
    assert "CPQ" in past_base
    assert "CPQ" not in base


def test_subclassing():
    class SubNeoBase(neobase.NeoBase):
        DUPLICATES = False

    neo = neobase.NeoBase()
    sub = SubNeoBase()
    assert len(sub) < len(neo)


def test_custom_fields():
    class SubNeoBase(neobase.NeoBase):
        FIELDS = neobase.NeoBase.FIELDS + (
            ("geolat", 49, None),
            ("geolng", 50, None),
        )

    sub = SubNeoBase()
    assert sub.get("AAE", "geolat") == "36.82889"
    assert sub.get("AAE", "geolng") == "7.81278"

    # Testing get_location with custom fields
    loc = sub.get_location("AAE")
    assert loc.lat == pytest.approx(36.822225)
    assert loc.lng == pytest.approx(7.809167)

    loc = sub.get_location("AAE", "geolat", "geolng")
    assert loc.lat == pytest.approx(36.82889)
    assert loc.lng == pytest.approx(7.81278)


class TestReferenceData:
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
        assert base.get("NCE", "name") == "Nice Côte d'Azur International Airport"
        assert base.get("MAD", "name") == "Adolfo Suárez Madrid–Barajas Airport"

        # Checking top 10 page rank of duplicated airport/city with same IATA code
        assert (
            base.get("ATL", "name")
            == "Hartsfield-Jackson Atlanta International Airport"
        )
        assert base.get("DXB", "name") == "Dubai International Airport"
        assert base.get("LAX", "name") == "Los Angeles International Airport"
        assert base.get("SYD", "name") == "Sydney International Airport"
        assert base.get("IST", "name") == "Istanbul Airport"
        assert base.get("SEA", "name") == "Seattle-Tacoma International Airport"
        assert base.get("DFW", "name") == "Dallas/Fort Worth International Airport"
        assert base.get("DEN", "name") == "Denver International Airport"
        assert base.get("FRA", "name") == "Frankfurt Airport"
        assert base.get("AMS", "name") == "Amsterdam Airport Schiphol"

    def test_obsolete_por_are_not_loaded(self, base):
        assert base.get("KMG", "name") == "Kunming Changshui International Airport"
        assert base.get("HFE", "name") == "Hefei Xinqiao International Airport"
        assert base.get("NAT", "name") == "Greater Natal International Airport"
        assert base.get("JIJ", "name") == "Jijiga Wilwal International Airport"
        assert base.get("SWA", "name") == "Jieyang Chaoshan Airport"

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
