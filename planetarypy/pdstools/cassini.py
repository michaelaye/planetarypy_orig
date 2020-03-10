from .._config import rootpath
from ..utils import ProgressBar, download
from . import indices

META_URL = "http://pds-rings.seti.org/metadata"


class META:
    INDICES = {
        "index": "Cumulative product index of volume series",
        "inventory": "Cumulative list of observed bodies by product",
        "moon_summary": "Cumulative list of observed geometry on moons",
        "ring_summary": "Cumulative list of observed geometry on rings",
        "saturn_summary": "Cumulative list of observed geometry on Saturn",
    }

    def __init__(self, name=""):
        if name == "":
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
        return META_URL + f"/CO{self.id}xxx/CO{self.id}999/"

    @property
    def meta_filename(self):
        return f"CO{self.id}999_{self.name}"

    @property
    def label_url(self):
        return self.folder_url + self.meta_filename + ".lbl"

    @property
    def table_url(self):
        return self.folder_url + self.meta_filename + ".tab"

    def download_table(self, local_folder="."):
        baseurl = self.folder_url + self.meta_filename
        for ext in [".lbl", ".tab"]:
            filename = self.meta_filename + ext
            url = self.folder_url + filename
            local_path = f"{local_folder}/{filename}"
            print("Downloading", local_path)
            with ProgressBar(unit="B", unit_scale=True, miniters=1, desc=url) as t:
                download(url, local_path, reporthook=t.update_to, data=None)

    @property
    def label(self):
        return indices.IndexLabel(self.meta_filename + ".lbl")

    def read_table(self, **kwargs):
        return self.label.read_index_data(**kwargs)


class UVIS_META(META):
    id = "UVIS_0"
    INDICES = {
        "index": "Cumulative product index of volume series",
        "supplemental_index": "Cumulative product index of volume series",
        "moon_summary": "Cumulative list of observed geometry on moons",
        "ring_summary": "Cumulative list of observed geometry on rings",
        "saturn_summary": "Cumulative list of observed geometry on Saturn",
    }


class ISS_META(META):
    id = "ISS_2"


class VIMS_META(META):
    id = "VIMS_0"


class IndexDB(object):
    def __init__(self, indexdir=None):
        if indexdir is None:
            try:
                indexdir = config["pyciss_index"]["path"]
            except KeyError:
                print("Did not find the key `pyciss_indexdir` in the config file.")
                return
        self.indexdir = Path(indexdir)

    @property
    def indexfiles(self):
        return self.indexdir.glob("*_????.tab")

    @property
    def cumulative_label(self):
        return IndexLabel(self.indexdir / "cumindex.lbl")

    def get_index_no(self, no):
        return iss_index_to_df(next(self.indexdir.glob("*_" + str(no) + ".tab")))
