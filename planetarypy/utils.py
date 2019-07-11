import datetime as dt
import logging
import warnings
from math import radians, tan
from pathlib import Path
from urllib.request import urlretrieve

import click
import pandas as pd

try:
    from importlib_resources import path
except ModuleNotFoundError:
    from importlib.resources import path

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from tqdm.autonotebook import tqdm

logger = logging.getLogger(__name__)
try:
    from osgeo import gdal
except ImportError:
    GDAL_INSTALLED = False
    logger.warning("No GDAL found.Some util funcs not working, but okay.")
else:
    GDAL_INSTALLED = True


nasa_date_format = "%Y-%j"
nasa_dt_format = nasa_date_format + "T%H:%M:%S"
nasa_dt_format_with_ms = nasa_dt_format + ".%f"
standard_date_format = "%Y-%m-%d"
standard_dt_format = standard_date_format + "T%H:%M:%S"


def nasa_date_to_iso(datestr):
    """Convert the day-number based NASA format to ISO.

    Parameters
    ----------
    datestr : str
        Date string in the form Y-j

    Returns
    -------
    Datestring in ISO standard yyyy-mm-ddTHH:MM:SS.MMMMMM
    """
    date = dt.datetime.strptime(datestr, nasa_date_format)
    return date.isoformat()


@click.command("nasa_date_to_iso")
@click.argument("datestr")
def nasa_date_to_iso_command(datestr):
    click.echo(nasa_date_to_iso(datestr))


def iso_to_nasa_date(datestr):
    date = dt.datetime.strptime(datestr, standard_date_format)
    return date.strftime(nasa_date_format)


def nasa_datetime_to_iso(dtimestr):
    if dtimestr.split(".")[1]:
        tformat = nasa_dt_format_with_ms
    else:
        tformat = nasa_dt_format
    time = dt.datetime.strptime(dtimestr, tformat)
    return time.isoformat()


def iso_to_nasa_datetime(dtimestr):
    date = dt.datetime.strptime(dtimestr, standard_dt_format)
    return date.strftime(nasa_dt_format)


def replace_all_nasa_times(df):
    for col in [col for col in df.columns if "TIME" in col]:
        if "T" in df[col].iloc[0]:
            df[col] = pd.to_datetime(df[col].map(nasa_datetime_to_iso))


def get_gdal_center_coords(imgpath):
    if not GDAL_INSTALLED:
        logger.error("GDAL not installed. Returning")
        return
    ds = gdal.Open(str(imgpath))
    xmean = ds.RasterXSize // 2
    ymean = ds.RasterYSize // 2
    return xmean, ymean


class ProgressBar(tqdm):
    """Provides `update_to(n)` which uses `tqdm.update(delta_n)`."""

    def update_to(self, b=1, bsize=1, tsize=None):
        """
        b  : int, optional
            Number of blocks transferred so far [default: 1].
        bsize  : int, optional
            Size of each block (in tqdm units) [default: 1].
        tsize  : int, optional
            Total size (in tqdm units). If [default: None] remains unchanged.
        """
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)  # will also set self.n = b * bsize


def download(url, localpath=".", use_tqdm=True, **kwargs):
    """Simple wrapper of urlretrieve

    Adding a default path to urlretrieve

    Parameters:
    ----------
    url : str
        HTTP(S) URL to download
    localpath : str,pathlib.Path
        Local path where to store the download.
    **kwargs : {dict}
        Keyword args to be handed to urlretrieve.
    Returns
    -------
    Tuple
        Tuple returned by urlretrieve
    """
    urlpath = Path(url)
    local = Path(localpath)
    savepath = local / urlpath.name if local.is_dir() else local
    logger.debug("Downloading %s into %s", url, localpath)
    if use_tqdm:
        with ProgressBar(
            unit="B", unit_scale=True, miniters=1, desc=url.split("/")[-1]
        ) as t:  # all optional kwargs
            return urlretrieve(url, savepath, reporthook=t.update_to)
    else:
        return urlretrieve(url, savepath, **kwargs)


def height_from_shadow(shadow_in_pixels, sun_elev):
    """Calculate height of an object from its shadow length.

    Note, that your image might have been binned.
    You need to correct `shadow_in_pixels` for that.

    Parameters
    ----------
    shadow_in_pixels : float
        Measured length of shadow in pixels
    sun_elev : angle(float)
        Angle of sun over horizon

    Returns
    -------
    height [meter]
    """
    return tan(radians(sun_elev)) * shadow_in_pixels
