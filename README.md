# NeoBase

Simple reboot of GeoBase. Compatible with Python 2.6+, Python 3.x, Pypy.

```python
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

```
