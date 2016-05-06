# planetpy
Collection of planetary science tools.

[![Build Status](https://travis-ci.org/michaelaye/planetpy.svg?branch=master)](https://travis-ci.org/michaelaye/planetpy)
[![Code Health](https://landscape.io/github/michaelaye/planetpy/master/landscape.svg?style=flat)](https://landscape.io/github/michaelaye/planetpy/master)
[![Coverage Status](https://coveralls.io/repos/michaelaye/planetpy/badge.svg?branch=master&service=github)](https://coveralls.io/github/michaelaye/planetpy?branch=master)
[![Documentation Status](https://readthedocs.org/projects/planetpy/badge/?version=latest)](https://readthedocs.org/projects/planetpy/?badge=latest)
[![Join the chat at https://gitter.im/michaelaye/planetpy](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/michaelaye/planetpy?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

## Cite me

If you use this software, please consider citing it:

[![DOI](https://zenodo.org/badge/15486/michaelaye/planetpy.svg)](https://zenodo.org/badge/latestdoi/15486/michaelaye/planetpy)

## Vision

* Similar to `astropy` to collect useful planetary science modules.
* Managing easily accessible constants
* Hooking into existing SPICE and osgeo/gdal installs for some utilities:
 * SPICER: A SPICE utility class that makes SPICE-life easier for planetary surface calculations related to irradiation (available, but needs clean-up)
 * GeoRaster: A class that uses GDAL but again adds user-friendly interfaces to coordinate transformtion, sub-solar point direction marking, and combination of different data-sets into one (e.g. laser altimeter on top of image data etc.) (available, but needs clean-up)
* Areas I want to avoid overlapping with as much as possible:
 * GDAL's vast capability of reading geo-referenced images. Any functionality we are missing should be integrated as much as possible into GDAL, for example I think several PDS formats are still failing with the PDS reader of GDAL. Maybe, we could store virtual GDAL formats here, if requested.
 * scikit-image for image analysis routines. 

## Install

If you want to develop for `planetpy` I recommend installing it like this:
```python
python setup.py develop
```
That will create a path link into the github directory, and you can avoid adding setting up a PYTHONPATH which can create a lot of trouble. All new developments will become automatically active, i.e. importable without another `install`.
In addition to that I highly recommend these lines for the IPython notebook setup:
```python
%load_ext autoreload
%autoreload 2
```
This will even autoMAGICALLY make your notebook session aware of any new developments you have added to `planetpy`.

If you just want to use `planetpy` and don't want to be surprised about any changes that might be added into your repository clone after doing a `git pull` then install in the standard way:
```python
python setup.py install
```
Note that this way you will have to execute another `python setup.py install` each time you `git-pull` in updates from github.
