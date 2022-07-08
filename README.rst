NeoBase |actions|_ |cratev|_ |crated|_
======================================

.. _actions : https://github.com/alexprengere/neobase/actions/workflows/python-package.yml
.. |actions| image:: https://github.com/alexprengere/neobase/actions/workflows/python-package.yml/badge.svg

.. _cratev : https://pypi.org/project/NeoBase/
.. |cratev| image:: https://img.shields.io/pypi/v/neobase.svg

.. _crated : https://pypi.org/project/NeoBase/
.. |crated| image:: https://static.pepy.tech/badge/neobase

Minimalist `GeoBases <https://github.com/opentraveldata/geobases/>`__
implementation:

-  no dependencies
-  compatible with Python 3.6+, CPython and PyPy
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

Use the Python package:

.. code:: bash

    pip install neobase

Docs
----

Check out `readthedocs <http://neobase.readthedocs.org/en/latest/>`__ for the API.

You can customize the source data when initializing:

.. code:: python

    with open("file.csv") as f:
        N = NeoBase(f)

Otherwise the loaded file will be the embedded one, unless the ``OPTD_POR_FILE`` environment variable is set. In that case, it will load from the path defined in that variable.

You can manually retrieve the latest data source yourself too, but you expose yourself to some breaking changes if they occur in the data.

.. code:: python

    from io import StringIO
    from urllib.request import urlopen

    from neobase import NeoBase, OPTD_POR_URL

    data = urlopen(OPTD_POR_URL).read().decode('utf8')
    N = NeoBase(StringIO(data))
    N.get("PAR")

The reference date of validity can be changed as well:

.. code:: python

    N = NeoBase(date="2000-01-01")
    N.get("AIY")  # was decommissioned in 2015

By default, the reference date will be set to today, unless the ``OPTD_POR_DATE`` environment variable is set. In that case, it will use that value.

You can customize the behavior regarding duplicates: points sharing the same IATA code, like NCE as airport and NCE as city. By default everything is kept, but you can set it so that only the first point with an IATA code is kept:

.. code:: python

    N = NeoBase(duplicates=False)
    len(N)  # about 10,000 "only"

Note that you can use the ``OPTD_POR_DUPLICATES`` environment variable to control this as well: set it to ``0`` to drop duplicates.

Finally, you can customize fields loaded by subclassing.

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

    N = SubNeoBase()

Command-line interface
----------------------

You can query the data using:

.. code:: bash

    python -m neobase PAR NCE

Tests
-----

.. code:: bash

    tox
