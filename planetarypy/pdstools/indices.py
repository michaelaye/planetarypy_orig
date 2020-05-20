"""Support tools to work with PDS ISS indexfiles.

The main user interface is the IndexLabel class which is able to load the table file for you.
"""
import copy
import logging
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import pandas as pd
import pvl
import toml
from dateutil import parser
from tqdm import tqdm

from .. import utils
from .._config import config
from .scraper import CTXIndex

try:
    # 3.6 compatibility
    from importlib_resources import path as resource_path
except ModuleNotFoundError:
    from importlib.resources import path as resource_path

logger = logging.getLogger(__name__)

indices_root = Path(config["data_archive"]["path"]) / "indices"


@dataclass
class Index:
    """Index manager class.

    Parameters
    ----------
    key : str
        Nested key in form of mission.instrument.index_name
    url : str
        URL to index
    timestamp : str
        Timestamp in ISO time format yy-mm-ddTHH:MM:SS.
        This is usually read by the IndexDB class from the config file and its
        value is the time of the last download.
    """

    local_root = indices_root
    key: str
    url: str
    timestamp: str

    @property
    def needs_download(self):
        """Determine if the index needs to be downloaded.

        Download shall happen when (1) no local timestamp was stored or (2) when the remote timestamp
        is newer.

        Parameters
        ----------
        index : indices.Index (namedtuple)
            Index holding the timestamp attribute read from the config file

        Returns
        -------
        bool
            Boolean indicating if download shall happen.
        """
        remote_timestamp = utils.get_remote_timestamp(self.url)
        self.new_timestamp = remote_timestamp
        if self.timestamp:
            if remote_timestamp > parser.parse(self.timestamp):
                return True
        else:
            # also return True when the timestamp is not valid
            return True
        # all other cases no D/L required
        return False

    @property
    def key_tokens(self):
        return self.key.split(".")

    @property
    def mission(self):
        return self.key_tokens[0]

    @property
    def instrument(self):
        return self.key_tokens[1]

    @property
    def index_name(self):
        "str: Examples: EDR, RDR"
        return self.key_tokens[2]

    @property
    def label_filename(self):
        return Path(self.url.split("/")[-1])

    @property
    def isupper(self):
        return self.label_filename.suffix.isupper()

    @property
    def table_filename(self):
        new_suffix = ".TAB" if self.isupper else ".tab"
        return self.label_filename.with_suffix(new_suffix)

    @property
    def label_path(self):
        return Path(urlsplit(self.url).path)

    @property
    def table_path(self):
        return self.label_path.with_name(self.table_filename.name)

    @property
    def table_url(self):
        tokens = urlsplit(self.url)
        return urlunsplit(
            tokens._replace(
                path=str(self.label_path.with_name(self.table_filename.name))
            )
        )

    @property
    def local_dir(self):
        p = self.local_root / f"{self.mission}/{self.instrument}/{self.index_name}"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def local_table_path(self):
        return self.local_dir / self.table_filename

    @property
    def local_label_path(self):
        return self.local_dir / self.label_filename

    @property
    def local_hdf_path(self):
        return self.local_table_path.with_suffix(".hdf")

    @property
    def df(self):
        return pd.read_hdf(self.local_hdf_path)

    def download(self, local_dir="", convert_to_hdf=True):
        """Wrapping URLs for downloading PDS indices and their label files.

        Parameters
        ----------
        key : str, optional
            Period-separated key into the available index files, e.g. cassini.uvis.moon_summary
        label_url : str, optional
            Alternative to using the index system, the user can provide the URL to a label
            for an index. The table file has to be in the same folder, as usual.
        local_dir: str, pathlib.Path, optional
            Path for local storage. Default: current directory and filename from URL
        convert_to_hdf : bool
            Switch to convert the index automatically to a faster loading HDF file
        """
        if not local_dir:
            local_dir = self.local_dir
        # check timestamp
        if not self.needs_download:
            print("Stored index is up-to-date.")
            return
        label_url = self.url
        logger.info("Downloading %s." % label_url)
        local_label_path, _ = utils.download(label_url, local_dir)
        logger.info("Downloading %s.", self.table_url)
        local_data_path, _ = utils.download(self.table_url, local_dir)
        IndexDB().update_timestamp(self)
        if convert_to_hdf is True:
            label = IndexLabel(local_label_path)
            df = label.read_index_data()
            savepath = local_data_path.with_suffix(".hdf")
            df.to_hdf(savepath, "df")
        print(f"Downloaded and converted to pandas HDF: {savepath}")


class IndexDB:
    fname = "pds_indices_db.toml"
    fpath = Path.home() / f".{fname}"

    def __init__(self):
        """Initialize index database.

        Will copy the package's version to user's home folder at init,
        so that user doesn't need to edit file in package to add new indices.

        Adding new index URLs to the package's config file pds_indices_db.toml
        is highly encouraged via pull request.
        """
        if not self.fpath.exists():
            with resource_path("planetarypy.pdstools.data", self.fname) as p:
                self.config = self.read_from_file(p)
        else:
            self.config = self.read_from_file()

    def read_from_file(self, path=None):
        """Read the config.

        Writing this short method to decouple IndexDB from choice of config file format.

        Parameters
        ----------
        path : str, pathlib.Path
            Path to the config file to open.
        """
        if path is None:
            path = self.fpath
        return toml.load(path)

    def write_to_file(self):
        "Write the config to user's home copy."
        with open(self.fpath, "w") as f:
            toml.dump(self.config, f)

    def get_by_path(self, nested_key):
        """Get sub-dictionary by nested key.

        Parameters
        ----------
        nested_key: str
            A nested key in the toml format, separated by '.', e.g. cassini.uvis.ring_summary
        """
        mapList = nested_key.split(".")
        d = copy.deepcopy(self.config)
        for k in mapList:
            d = d[k]
        return Index(nested_key, **d)

    def get(self, nested_key):
        "alias to get_by_path"
        return self.get_by_path(nested_key)

    def set_by_path(self, nested_key, value):
        """Set a nested dictionary key to new value.

        Parameters
        ----------
        nested_key : str
            A nested key in the toml format, separated by '.', e.g. cassini.uvis.summary
        value : str
            New value for dictionary key
        """
        dic = self.config
        keys = nested_key.split(".")
        for key in keys[:-1]:
            dic = dic.setdefault(key, {})
        dic[keys[-1]] = value

    def list_indices(self):
        "Print index database in pretty form, using toml.dumps"
        print(toml.dumps(self.config))
        print(
            "Use indices.download('mission.instrument.index') to download in index file."
        )
        print("For example: indices.download('cassini.uvis.moon_summary'")

    def update_timestamp(self, index):
        self.set_by_path(f"{index.key}.timestamp", index.new_timestamp.isoformat())
        self.write_to_file()

    def download(
        self, key=None, label_url=None, local_dir="", convert_to_hdf=True, force=False
    ):
        """Wrapping URLs for downloading PDS indices and their label files.

        Parameters
        ----------
        key : str, optional
            Period-separated key into the available index files, e.g. cassini.uvis.moon_summary
        label_url : str, optional
            Alternative to using the index system, the user can provide the URL to a label
            for an index. The table file has to be in the same folder, as usual.
        local_dir: str, pathlib.Path, optional
            Path for local storage. Default: current directory and filename from URL
        convert_to_hdf : bool
            Switch to convert the index automatically to a faster loading HDF file
        """
        if label_url is None:
            if key is not None:
                index = self.get_by_path(key)
            else:
                raise SyntaxError("One of key or label_url needs to be given.")
        # check timestamp
        if not index.needs_download and not force:
            print("Stored index is up-to-date.")
            return index.local_hdf_path
        if not local_dir:
            local_dir = index.local_dir
        label_url = index.url
        logger.info("Downloading %s." % label_url)
        local_label_path, _ = utils.download(label_url, local_dir)
        data_url = replace_url_suffix(label_url)
        logger.info("Downloading %s.", data_url)
        local_data_path, _ = utils.download(data_url, local_dir)
        self.update_timestamp(index)
        if convert_to_hdf is True:
            label = IndexLabel(local_label_path)
            df = label.read_index_data()
            savepath = local_data_path.with_suffix(".hdf")
            df.to_hdf(savepath, "df")
        print(f"Downloaded and converted to pandas HDF: {savepath}")

    def __repr__(self):
        return toml.dumps(self.config)


# global
indexdb = IndexDB()


def list_available_index_files():
    print(indexdb)


def replace_url_suffix(url, new_suffix=".tab"):
    """Cleanest way to replace the suffix in an URL.

    Sometimes the indices have upper case filenames, this is taken care of here.

    Parameters
    ----------
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
                    df[column], format=utils.nasa_dt_format_with_ms, errors="coerce"
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

    The HiRISE EDRCUMINDEX has some broken lines where the SCAN_EXPOSURE_DURATION is of format
    F10.4 instead of the defined F9.4.
    This function simply replaces those incidences with one less decimal fraction, so 20000.0000
    becomes 20000.000.

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
