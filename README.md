# planetpy
Collection of planetary science tools.

## Install

If you want to develop `planetpy` I recommend installing it like this:
```python
python setup.py develop
```
That will create a path link into the github directory, and all new developments will become automatically active.
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
