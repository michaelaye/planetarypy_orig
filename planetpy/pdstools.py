"""Support tools to work with PDS ISS indexfiles."""
from pathlib import Path

import pandas as pd
try:
    import progressbar
except ImportError:
    PROGRESSBAR_EXISTS = False
else:
    PROGRESSBAR_EXISTS = True
import pvl

from . import utils

base_urls = {
    'hirise': 'http://hirise-pds.lpl.arizona.edu/PDS',
    # The '2' stands for all data at Saturn, '1' would be all transit data.
    'cassini_iss': 'http://pds-rings.seti.org/volumes/COISS_2xxx/COISS_'
}


class PVLColumn(object):
    def __init__(self, pvlobj):
        self.pvlobj = pvlobj

    @property
    def name(self):
        return self.pvlobj['NAME']

    @property
    def name_as_list(self):
        "needs to return a list for consistency for cases when it's an array."
        if self.items is None:
            return [self.name]
        else:
            return [self.name + '_' + str(i + 1) for i in range(self.items)]

    @property
    def start(self):
        "Decrease by one as Python is 0-indexed."
        return self.pvlobj['START_BYTE'] - 1

    @property
    def stop(self):
        return self.start + self.pvlobj['BYTES']

    @property
    def items(self):
        return self.pvlobj.get('ITEMS')

    @property
    def item_bytes(self):
        return self.pvlobj.get('ITEM_BYTES')

    @property
    def item_offset(self):
        return self.pvlobj.get('ITEM_OFFSET')

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
    """Support working with label files of PDS Index tables."""
    def __init__(self, labelpath):
        self.path = Path(labelpath)
        "search for table name pointer and store key and fpath."
        tuple = [i for i in self.pvl_lbl if i[0].startswith('^')][0]
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
        return self.table.getlist('COLUMN')

    @property
    def columns_dic(self):
        return {col['NAME']: col for col in self.pvl_columns}

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
        columns = self.table.getlist('COLUMN')
        for column in columns:
            pvlcol = PVLColumn(column)
            if pvlcol.items is None:
                colspecs.append(pvlcol.colspecs)
            else:
                colspecs.extend(pvlcol.colspecs)
        return colspecs

    def read_index_data(self):
        return index_to_df(self.index_path, self)


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


def index_to_df(indexpath, label, convert_times=True):
    indexpath = Path(indexpath)
    df = pd.read_fwf(indexpath, header=None,
                     names=label.colnames,
                     colspecs=label.colspecs)
    if convert_times:
        print("Converting times...")
        for column in [i for i in df.columns if 'TIME' in i]:
            df[column] = pd.to_datetime(df[column])
        print("Done.")
    return df


# TODO:
    # if not labelpath.exists():
    #     df = pd.read_csv(indexpath, header=None)


def convert_indexfiles_to_hdf(folder):
    """Convert all indexfiles to an HDF database.

    Search for .tab files in `folder`, read them into a dataframe,
    concat to large dataframe at the end and store as HDF file.

    Parameters
    ----------
    folder : str or pathlib.Path
        Folder in where to search for .tab files
    labelpath : str or pathlb.Path
    """
    indexdir = Path(folder)
    # TODO: make it work for .TAB as well
    indexfiles = list(indexdir.glob('*.tab'))
    bucket = []
    if PROGRESSBAR_EXISTS:
        bar = progressbar.ProgressBar(max_value=len(indexfiles))
    for i, indexfile in enumerate(indexfiles):
        # convert times later, more performant
        df = index_to_df(indexfile, convert_times=False)
        df['index_fname'] = str(indexfile)
        bucket.append(df)
        if bar:
            bar.update(i)
    totalindex = pd.concat(bucket, ignore_index=True)
    # Converting timestrings to datetimes
    print("Converting times...")
    for column in [i for i in totalindex.columns if 'TIME' in i]:
        totalindex[column] = pd.to_datetime(totalindex[column].
                                            map(utils.
                                                nasa_datetime_to_iso))
    # TODO: Clean up old iss references
    savepath = indexdir / 'iss_totalindex.hdf'
    totalindex.to_hdf(savepath, 'df')
    print("Created pandas HDF index database file here:\n{}"
          .format(savepath))
