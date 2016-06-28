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

Check out `readthedocs <http://neobase.readthedocs.org/en/latest/>`__.

Tests
-----

.. code:: bash

    tox # or detox ;)
