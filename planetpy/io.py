from toml import toml
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

configpath = Path.home() / '.planetpy.toml'

if not configpath.exists():
    print("No configuration file {} found.\n".format(configpath))
    print("Please run `planetpy.io.set_database_path()` and provide the path where\n"
          "you want to archive your downloaded data.")
    print(
        f"""`planetpy` will store this path in {configpath}, where you can
        easily change it later.
        Note, that it will be stored with a host-name, that way you can have
        different archiving paths on different machines, but still share the same
        config file.""")
else:
    with open(configpath) as f:
        config = toml.load(f)


def set_database_path(dbfolder):
    """Use to write the database path into the config.

    Parameters
    ----------
    dbfolder : str or pathlib.Path
        Path to where planetpy will store data it downloads..
    """
    try:
        with open(configpath) as f:
            config = toml.load(f)
    except IOError:
        d = {}
        d['data_archive'] = {}
        d['data_archive'['path'] = dbfolder
    with open(configpath, 'w') as f:
        toml.dump(f)
    print("Saved database path into {}.".format(configpath))
