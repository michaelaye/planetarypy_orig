from tqdm import tqdm

from .. import indices
from ..utils import download

META_URL = 'http://pds-rings.seti.org/metadata'


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


class META:
    INDICES = {'index': 'Cumulative product index of volume series',
               'inventory': 'Cumulative list of observed bodies by product',
               'moon_summary': 'Cumulative list of observed geometry on moons',
               'ring_summary': 'Cumulative list of observed geometry on rings',
               'saturn_summary': 'Cumulative list of observed geometry on Saturn'
               }

    def __init__(self, name=''):
        if name == '':
            print("Call me with one of the following index names:")
            for k, v in self.INDICES.items():
                print(k, ": ", v)
            raise ValueError("Provide index name.")
        else:
            self._name = name

    @property
    def name(self):
        return self._name

    @property
    def folder_url(self):
        return META_URL + f'/CO{self.id}xxx/CO{self.id}999/'

    @property
    def meta_filename(self):
        return f'CO{self.id}999_{self.name}'

    @property
    def label_url(self):
        return self.folder_url + self.meta_filename + '.lbl'

    @property
    def table_url(self):
        return self.folder_url + self.meta_filename + '.tab'

    def download_table(self, local_folder='.'):
        baseurl = self.folder_url + self.meta_filename
        for ext in ['.lbl', '.tab']:
            filename = self.meta_filename + ext
            url = self.folder_url + filename
            local_path = f"{local_folder}/{filename}"
            print("Downloading", local_path)
            with ProgressBar(unit='B', unit_scale=True, miniters=1, desc=url) as t:
                download(url, local_path, reporthook=t.update_to, data=None)

    @property
    def label(self):
        return indices.IndexLabel(self.meta_filename + '.lbl')

    def read_table(self):
        return self.label.read_index_data()


class UVIS_META(META):
    id = 'UVIS_0'
    INDICES = {'index': 'Cumulative product index of volume series',
               'supplemental_index': 'Cumulative product index of volume series',
               'moon_summary': 'Cumulative list of observed geometry on moons',
               'ring_summary': 'Cumulative list of observed geometry on rings',
               'saturn_summary': 'Cumulative list of observed geometry on Saturn'
               }


class ISS_META(META):
    id = 'ISS_2'


class VIMS_META(META):
    id = 'VIMS_0'
