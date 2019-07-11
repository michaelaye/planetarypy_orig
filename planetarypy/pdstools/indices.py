"""Support tools to work with PDS ISS indexfiles.

The main user interface is the IndexLabel class which is able to load the table file for you.
"""
import logging
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import pandas as pd
import pvl
import toml
import yaml
from tqdm import tqdm

from .. import utils
from .scraper import CTXIndex

try:
    from importlib_resources import read_text
except ModuleNotFoundError:
    from importlib.resources import read_text

try:
    import progressbar
except ImportError:
    PROGRESSBAR_EXISTS = False
else:
    PROGRESSBAR_EXISTS = True

logger = logging.getLogger(__name__)

indices_urls = toml.loads(read_text("planetarypy.pdstools.data", "indices_paths.toml"))


def list_available_index_files():
    print(yaml.dump(indices_urls, default_flow_style=False))
    print("Use indices.download('mission:instrument:index') to download in index file.")
    print("For example: indices.download('cassini:uvis:moon_summary'")


def replace_url_suffix(url, new_suffix=".tab"):
    """Cleanest way to replace the suffix in an URL.

    Sometimes the indices have upper case filenames, this is taken care of here.

    Parameters
    ==========
    url : str
        URl to a file that has a suffix like .lbl
    new_suffix : str, optional
        The new suffix. Default (all cases so far): .img
    """
    split = urlsplit(url)
    old_suffix = Path(split.path).suffix
    new_suffix = new_suffix.upper() if old_suffix.isupper() else new_suffix
    return urlunsplit(
        split._replace(path=str(Path(split.path).with_suffix(new_suffix)))
    )


def download(key=None, label_url=None, local_dir=".", convert_to_hdf=True):
    """Wrapping URLs for downloading PDS indices and their label files.

    Parameters
    ==========
    key : str, optional
        Colon-separated key into the available index files, e.g. cassini:uvis:moon_summary
    label_url : str, optional
        Alternative to using the index system, the user can provide the URL to a label
        for an index. The table file has to be in the same folder, as usual.
    local_dir: str, pathlib.Path, optional
        Path for local storage. Default: current directory and filename from URL
    """
    if label_url is None:
        if key is not None:
            mission, instr, index = key.split(":")
            label_url = indices_urls[mission][instr][index]
        else:
            raise SyntaxError("One of key or label_url needs to be given.")
    logger.info("Downloading %s." % label_url)
    local_label_path, _ = utils.download(label_url, local_dir)
    data_url = replace_url_suffix(label_url)
    logger.info("Downloading %s.", data_url)
    local_data_path, _ = utils.download(data_url, local_dir)
    if convert_to_hdf is True:
        label = IndexLabel(local_label_path)
        df = label.read_index_data()
        savepath = local_data_path.with_suffix(".hdf")
        df.to_hdf(savepath, "df")
    print(f"Downloaded and converted to pandas HDF: {savepath}")


def download_CTX_index():
    ctx = CTXIndex()
    download(label_url=str(ctx.latest_index_label_url))

class PVLColumn(object):
    def __init__(self, pvlobj):
        self.pvlobj = pvlobj

    @property
    def name(self):
        return self.pvlobj["NAME"]

    @property
    def name_as_list(self):
        "needs to return a list for consistency for cases when it's an array."
        if self.items is None:
            return [self.name]
        else:
            return [self.name + "_" + str(i + 1) for i in range(self.items)]

    @property
    def start(self):
        "Decrease by one as Python is 0-indexed."
        return self.pvlobj["START_BYTE"] - 1

    @property
    def stop(self):
        return self.start + self.pvlobj["BYTES"]

    @property
    def items(self):
        return self.pvlobj.get("ITEMS")

    @property
    def item_bytes(self):
        return self.pvlobj.get("ITEM_BYTES")

    @property
    def item_offset(self):
        return self.pvlobj.get("ITEM_OFFSET")

    @property
    def colspecs(self):
        if self.items is None:
            return (self.start, self.stop)
        else:
            i = 0
            bucket = []
            for _ in range(self.items):
                off = self.start + self.item_offset * i
                bucket.append((off, off + self.item_bytes))
                i += 1
            return bucket

    def decode(self, linedata):
        if self.items is None:
            start, stop = self.colspecs
            return linedata[start:stop]
        else:
            bucket = []
            for (start, stop) in self.colspecs:
                bucket.append(linedata[start:stop])
            return bucket

    def __repr__(self):
        return self.pvlobj.__repr__()


class IndexLabel(object):
    """Support working with label files of PDS Index tables.

    Parameters
    ----------
    labelpath : str, pathlib.Path
        Path to the labelfile for a PDS Indexfile. The actual table should reside in the same
        folder to be automatically parsed when calling the `read_index_data` method.
    """

    def __init__(self, labelpath):
        self.path = Path(labelpath)
        "search for table name pointer and store key and fpath."
        tuple = [i for i in self.pvl_lbl if i[0].startswith("^")][0]
        self.tablename = tuple[0][1:]
        self.index_name = tuple[1]

    @property
    def index_path(self):
        return self.path.parent / self.index_name

    @property
    def pvl_lbl(self):
        return pvl.load(str(self.path))

    @property
    def table(self):
        return self.pvl_lbl[self.tablename]

    @property
    def pvl_columns(self):
        return self.table.getlist("COLUMN")

    @property
    def columns_dic(self):
        return {col["NAME"]: col for col in self.pvl_columns}

    @property
    def colnames(self):
        """Read the columns in a ISS index label file.

        The label file for the ISS indices describes the content
        of the index files.
        """
        colnames = []
        for col in self.pvl_columns:
            colnames.extend(PVLColumn(col).name_as_list)
        return colnames

    @property
    def colspecs(self):
        colspecs = []
        columns = self.table.getlist("COLUMN")
        for column in columns:
            pvlcol = PVLColumn(column)
            if pvlcol.items is None:
                colspecs.append(pvlcol.colspecs)
            else:
                colspecs.extend(pvlcol.colspecs)
        return colspecs

    def read_index_data(self, convert_times=True):
        return index_to_df(self.index_path, self, convert_times=convert_times)


def index_to_df(indexpath, label, convert_times=True):
    """The main reader function for PDS Indexfiles.

    In conjunction with an IndexLabel object that figures out the column widths,
    this reader should work for all PDS TAB files.

    Parameters
    ----------
    indexpath : str or pathlib.Path
        The path to the index TAB file.
    label : pdstools.IndexLabel object
        Label object that has both the column names and the columns widths as attributes
        'colnames' and 'colspecs'
    convert_times : bool
        Switch to control if to convert columns with "TIME" in name (unless COUNT is as well in name) to datetime
    """
    indexpath = Path(indexpath)
    df = pd.read_fwf(
        indexpath, header=None, names=label.colnames, colspecs=label.colspecs
    )
    if convert_times:
        for column in [i for i in df.columns if "TIME" in i and "COUNT" not in i]:
            if column == "LOCAL_TIME":
                # don't convert local time
                continue
            print(f"Converting times for column {column}.")
            try:
                df[column] = pd.to_datetime(df[column])
            except ValueError:
                df[column] = pd.to_datetime(
                    df[column], format=utils.nasa_dt_format_with_ms
                )
        print("Done.")
    return df


def decode_line(linedata, labelpath):
    """Decode one line of tabbed data with the appropriate label file.

    Parameters
    ----------
    linedata : str
        One line of a .tab data file
    labelpath : str or pathlib.Path
        Path to the appropriate label that describes the data.
    """
    label = IndexLabel(labelpath)
    for column in label.pvl_columns:
        pvlcol = PVLColumn(column)
        print(pvlcol.name, pvlcol.decode(linedata))


def find_mixed_type_cols(df, fix=True):
    """For a given dataframe, find the columns that are of mixed type.

    Tool to help with the performance warning when trying to save a pandas DataFrame as a HDF.
    When a column changes datatype somewhere, pickling occurs, slowing down the reading process of the HDF file.


    Parameters
    ----------
    df : pandas.DataFrame
        Dataframe to be searched for mixed data-types
    fix : bool
        Switch to control if NaN values in these problem columns should be replaced by the string 'UNKNOWN'
    Returns
    -------
    List of column names that have data type changes within themselves.
    """
    result = []
    for col in df.columns:
        weird = (df[[col]].applymap(type) != df[[col]].iloc[0].apply(type)).any(axis=1)
        if len(df[weird]) > 0:
            print(col)
            result.append(col)
    if fix is True:
        for col in result:
            df[col].fillna("UNKNOWN", inplace=True)
    return result


def fix_hirise_edrcumindex(infname, outfname):
    """Fix HiRISE EDRCUMINDEX.

    The HiRISE EDRCUMINDEX has some broken lines where the SCAN_EXPOSURE_DURATION is of format F10.4 instead of
    the defined F9.4.
    This function simply replaces those incidences with one less decimal fraction, so 20000.0000 becomes 20000.000.

    Parameters
    ----------
    infname : str
        Path to broken EDRCUMINDEX.TAB
    outfname : str
        Path where to store the fixed TAB file
    """
    with open(infname) as f:
        with open(outfname, "w") as newf:
            for line in tqdm(f):
                exp = line.split(",")[21]
                if float(exp) > 9999.999:
                    # catching the return of write into dummy variable
                    _ = newf.write(line.replace(exp, exp[:9]))
                else:
                    _ = newf.write(line)
