# planetpy
Collection of planetary science tools.

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
