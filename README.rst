NeoBase
=======

Minimalist `GeoBases <http://opentraveldata.github.com/geobases/>`__
implementation:

-  no dependencies
-  compatible with Python 2.6+, Python 3.x, Pypy
-  one data source:
   `opentraveldata <https://github.com/opentraveldata/opentraveldata>`__
-  one Python module for easier distribution on clusters (like Hadoop)
-  faster load time (5x)
-  tested with pytest and tox

.. code:: python

    >>> from neobase import NeoBase
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

Installation
------------

You can install directly after cloning:

.. code:: bash

    pip install --user .

Or use the Python package:

.. code:: bash

    pip install --user neobase

Doc
---

Check out `readthedocs <http://neobase.readthedocs.org/en/latest/>`__ for the API.

You can customize fields loaded by subclassing.

.. code:: python

    class SubNeoBase(NeoBase):
        KEY = 0  # iata_code

        # Those loaded fields are the default ones
        FIELDS = (
            ("name", 6, None),
            ("lat", 8, None),
            ("lng", 9, None),
            ("page_rank", 12, lambda s: float(s) if s else None),
            ("country_code", 16, None),
            ("country_name", 18, None),
            ('continent_name', 19, None),
            ("timezone", 31, None),
            ("city_code_list", 36, lambda s: s.split(",")),
            ('city_name_list', 37, lambda s: s.split('=')),
            ('location_type', 41, None),
            ("currency", 46, None),
        )

        # Drop duplicates, keep only the first POR with a specific key
        # Default value is True
        DUPLICATES = False

    N = SubNeoBase()

You can also customize the source data when initializing:

.. code:: python

    with open("file.csv") as f:
        N = NeoBase(f)

Otherwise the loaded file will be the embedded one, unless the ``OPTD_POR_FILE`` environment variable is set. In that case, it will load from the path defined in that variable.

You can manually retrieve the latest data source yourself too, but you expose yourself to some breaking changes if they occur in the data.

.. code:: python

    URL = ('https://raw.githubusercontent.com/opentraveldata/opentraveldata/'
           'master/opentraveldata/optd_por_public.csv')

    import urllib3
    http = urllib3.PoolManager()
    from io import StringIO
    from neobase import NeoBase

    text = http.request("GET", URL).data.decode("utf8")
    N = NeoBase(StringIO(text))
    N.get("PAR")

Command-line interface
----------------------

You can query the data using:

.. code:: bash

    python -m neobase PAR NCE

Tests
-----

.. code:: bash

    tox
